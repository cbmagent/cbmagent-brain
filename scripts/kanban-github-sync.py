#!/usr/bin/env python3
"""
Bidirectional sync between GitHub Issues and Hermes Kanban.

Direction 1 — GitHub → Kanban:
  Issues labelled `status:agent-ready` that have no linked Kanban task
  are created as Kanban tasks in `ready` state.

Direction 2 — Kanban → GitHub:
  Kanban tasks that have no linked GitHub Issue (agent-initiated work)
  get a GitHub Issue created for visibility, labelled `agent-brain` +
  `status:agent-ready`.

Linkage is tracked via a sentinel line in each body:
  GitHub Issue body contains:  <!-- kanban-task: <task_id> -->
  Kanban task body contains:   github-issue: #<number>

Status mapping:
  Kanban ready/todo  ↔  GitHub label `status:agent-ready`
  Kanban running     →  GitHub label `status:in-progress` (added if missing)
  Kanban blocked     →  GitHub label `status:blocked-human` (added if missing)
  Kanban done        →  GitHub Issue closed with summary comment

Usage:
    python3 scripts/kanban-github-sync.py [--dry-run] [--repo OWNER/REPO] [--open-scope agent-ready|all]
                                                                        [--auto-assign-profile PROFILE]
                                                                        [--auto-assign-limit N]
                                                                        [--auto-dispatch-max N]
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = "cbmagent/cbmagent-brain"
HERMES_HOME = Path.home() / ".hermes"
KANBAN_DB = HERMES_HOME / "kanban.db"
AGENT_READY_LABEL = "status:agent-ready"
IN_PROGRESS_LABEL = "status:in-progress"
BLOCKED_LABEL = "status:blocked-human"
REVIEW_REQUESTED_LABELS = {"status:review-requested", "review-requested"}
AGENT_BRAIN_LABEL = "agent-brain"
COPILOT_ASSIGNEE = "copilot-github-direct"
HERMES_REVIEWER_ASSIGNEE = "hermes-reviewer"
KANBAN_SENTINEL_RE = re.compile(r"<!-- kanban-task: ([a-zA-Z0-9_-]+) -->")
GITHUB_ISSUE_RE = re.compile(r"github-issue:\s*#(\d+)", re.IGNORECASE)
TASK_REPO_RE = re.compile(r"^repo:\s*([^\s]+)\s*$", re.IGNORECASE | re.MULTILINE)
TASK_URL_RE = re.compile(r"^github-url:\s*https?://github\.com/([^/]+/[^/\s]+)", re.IGNORECASE | re.MULTILINE)


def gh(*args, check=True, capture=True) -> str:
    cmd = ["gh"] + list(args)
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"[warn] gh {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip() if capture else ""


def hermes(*args, check=True, capture=True) -> str:
    cmd = ["hermes"] + list(args)
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"[warn] hermes {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip() if capture else ""


def kanban_db():
    if not KANBAN_DB.exists():
        hermes("kanban", "init")
    return sqlite3.connect(KANBAN_DB)


def get_kanban_tasks(conn):
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, body, status, assignee FROM tasks WHERE status != 'archived'"
    ).fetchall()
    return [dict(r) for r in rows]


def get_open_github_issues(repo: str, open_scope: str):
    args = [
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--limit", "200",
        "--json", "number,title,body,url,labels,assignees",
    ]
    if open_scope == "agent-ready":
        args += ["--label", AGENT_READY_LABEL]
    raw = gh(*args)
    if not raw:
        return []
    return json.loads(raw)


def get_all_open_github_issues(repo: str):
    """All open issues with agent-brain label (includes in-progress, blocked)."""
    raw = gh(
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--label", AGENT_BRAIN_LABEL,
        "--limit", "200",
        "--json", "number,title,body,url,labels",
    )
    if not raw:
        return []
    return json.loads(raw)


def get_all_github_issues_state(repo: str, limit: int = 200):
    """Fetch issue state/labels/assignees in one call (cheap signal scan)."""
    raw = gh(
        "issue", "list",
        "--repo", repo,
        "--state", "all",
        "--limit", str(limit),
        "--json", "number,title,url,state,labels,assignees",
    )
    if not raw:
        return []
    return json.loads(raw)


def extract_kanban_id_from_issue(issue: dict) -> str | None:
    body = issue.get("body") or ""
    m = KANBAN_SENTINEL_RE.search(body)
    return m.group(1) if m else None


def extract_issue_number_from_task(task: dict) -> int | None:
    body = task.get("body") or ""
    m = GITHUB_ISSUE_RE.search(body)
    return int(m.group(1)) if m else None


def extract_repo_from_task(task: dict) -> str | None:
    body = task.get("body") or ""
    m = TASK_REPO_RE.search(body)
    if m:
        return m.group(1).strip()
    # Fallback for older tasks that stored literal "\\n" escapes in body text.
    m = re.search(r"repo:\s*([^\s\\]+)", body, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = TASK_URL_RE.search(body)
    if m:
        return m.group(1).strip()
    return None


def label_names(issue: dict) -> set:
    return {l["name"] for l in issue.get("labels", [])}


def add_label(repo: str, issue_number: int, label: str, dry_run: bool):
    print(f"  + label #{issue_number} ← {label}")
    if not dry_run:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", label)


def remove_label(repo: str, issue_number: int, label: str, dry_run: bool):
    print(f"  - label #{issue_number} ← remove {label}")
    if not dry_run:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--remove-label", label)


def close_issue(repo: str, issue_number: int, comment: str, dry_run: bool):
    print(f"  ✓ closing #{issue_number}")
    if not dry_run:
        gh("issue", "comment", str(issue_number), "--repo", repo, "--body", comment)
        gh("issue", "close", str(issue_number), "--repo", repo)


def create_github_issue(repo: str, title: str, body: str, labels: list[str], dry_run: bool) -> int | None:
    label_args = []
    for l in labels:
        label_args += ["--label", l]
    print(f"  + GitHub Issue: {title!r}")
    if dry_run:
        return None
    raw = gh("issue", "create", "--repo", repo, "--title", title, "--body", body, *label_args)
    # raw looks like https://github.com/owner/repo/issues/123
    m = re.search(r"/issues/(\d+)$", raw)
    return int(m.group(1)) if m else None


def create_kanban_task(
    title: str,
    body: str,
    dry_run: bool,
    idempotency_key: str | None = None,
    assignee: str | None = None,
) -> str | None:
    print(f"  + Kanban task: {title!r}")
    if dry_run:
        return None
    cmd = ["hermes", "kanban", "create", title, "--body", body]
    if idempotency_key:
        cmd += ["--idempotency-key", idempotency_key]
    if assignee:
        cmd += ["--assignee", assignee]
    result = subprocess.run(
        cmd,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  [err] kanban create failed: {result.stderr.strip()}", file=sys.stderr)
        return None
    # hermes kanban create prints the task id on stdout
    m = re.search(r"([a-f0-9]{8,})", result.stdout)
    return m.group(1) if m else None


def assign_kanban_task(task_id: str, profile: str, dry_run: bool):
    print(f"  ~ assign {task_id} -> {profile}")
    if not dry_run:
        hermes("kanban", "assign", task_id, profile)


def claim_kanban_task(task_id: str, dry_run: bool):
    print(f"  ~ claim {task_id} (set running)")
    if not dry_run:
        hermes("kanban", "claim", task_id)


def complete_kanban_task(task_id: str, summary: str, dry_run: bool):
    print(f"  ✓ complete task {task_id}")
    if not dry_run:
        hermes("kanban", "complete", task_id, "--summary", summary)


def has_review_requested_label(issue: dict) -> bool:
    labels = {l["name"].lower() for l in issue.get("labels", [])}
    return any(name in labels for name in REVIEW_REQUESTED_LABELS)


def has_copilot_assignee(issue: dict) -> bool:
    assignees = {a.get("login", "").lower() for a in issue.get("assignees", [])}
    return "copilot" in assignees


def create_review_handoff_task(repo: str, issue: dict, dry_run: bool):
    issue_num = issue["number"]
    title = f"Review requested: {repo} #{issue_num} - {issue['title']}"
    body = (
        f"repo: {repo}\n"
        f"github-issue: #{issue_num}\n"
        f"github-url: {issue['url']}\n"
        f"handoff: external-agent-requested-review\n"
        f"source-agent: copilot-github-direct\n\n"
        "Review request detected via issue label. Hermes reviewer should validate the external agent's proposed changes and decide approve/request changes."
    )
    key = f"review:{repo}#{issue_num}"
    print(f"  + review handoff task for issue #{issue_num}")
    if dry_run:
        return
    result = subprocess.run(
        [
            "hermes", "kanban", "create", title,
            "--body", body,
            "--idempotency-key", key,
            "--assignee", HERMES_REVIEWER_ASSIGNEE,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [warn] unable to create review handoff task for #{issue_num}: {result.stderr.strip()}", file=sys.stderr)


def is_human_needed_task(task: dict) -> bool:
    """Heuristic: skip auto-assignment for human-needed tasks."""
    text = f"{task.get('title', '')}\n{task.get('body', '')}".lower()
    return (
        "human-needed" in text
        or "status:blocked-human" in text
        or "blocked-human" in text
    )


def bounded_auto_assign_and_dispatch(
    repo: str,
    tasks: list[dict],
    dry_run: bool,
    auto_assign_profile: str,
    auto_assign_limit: int,
    auto_dispatch_max: int,
):
    print("\n[Bounded auto-assign/dispatch]")

    if auto_assign_limit <= 0 and auto_dispatch_max <= 0:
        print("  (disabled)")
        return

    eligible = []
    for task in tasks:
        if task.get("status") != "ready":
            continue
        if task.get("assignee"):
            continue
        task_repo = extract_repo_from_task(task)
        if task_repo and task_repo.lower() != repo.lower():
            continue
        if is_human_needed_task(task):
            continue
        eligible.append(task)

    # oldest-first so queue drains fairly
    eligible.sort(key=lambda t: t.get("created_at") or 0)

    assigned = 0
    for task in eligible[: max(0, auto_assign_limit)]:
        assign_kanban_task(task["id"], auto_assign_profile, dry_run)
        assigned += 1

    if auto_dispatch_max > 0:
        print(f"  ~ dispatch max={auto_dispatch_max}")
        if not dry_run:
            hermes("kanban", "dispatch", "--max", str(auto_dispatch_max), check=False)
    else:
        print("  ~ dispatch skipped (--auto-dispatch-max=0)")

    print(f"  assigned={assigned}, eligible={len(eligible)}")

def add_sentinel_to_issue(repo: str, issue_number: int, task_id: str, dry_run: bool):
    """Append kanban sentinel to issue body."""
    raw = gh("issue", "view", str(issue_number), "--repo", repo, "--json", "body")
    if not raw:
        return
    body = json.loads(raw).get("body") or ""
    if KANBAN_SENTINEL_RE.search(body):
        return  # already there
    new_body = body + f"\n\n<!-- kanban-task: {task_id} -->"
    print(f"  ~ appending kanban sentinel to #{issue_number}")
    if not dry_run:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--body", new_body)


def sync(
    repo: str,
    dry_run: bool,
    open_scope: str,
    auto_assign_profile: str,
    auto_assign_limit: int,
    auto_dispatch_max: int,
):
    conn = kanban_db()
    tasks = get_kanban_tasks(conn)
    conn.close()

    # Build lookup maps
    task_by_id = {t["id"]: t for t in tasks}
    task_ids_with_gh = set()

    # ── Direction 2: Kanban → GitHub ──────────────────────────────────────────
    # Any Kanban task that has no github-issue link gets a GitHub Issue created.
    print("\n[Kanban → GitHub]")
    for task in tasks:
        issue_num = extract_issue_number_from_task(task)
        if issue_num is not None:
            task_ids_with_gh.add(task["id"])
            continue
        # Agent-initiated task with no GitHub Issue yet
        body = (task.get("body") or "").strip()
        gh_body = f"{body}\n\ngithub-issue: (pending)\n\n*Auto-created from Hermes Kanban task `{task['id']}` — status: {task['status']}*"
        labels = [AGENT_BRAIN_LABEL]
        if task["status"] in ("ready", "todo", "triage"):
            labels.append(AGENT_READY_LABEL)
        issue_num = create_github_issue(repo, task["title"], gh_body, labels, dry_run)
        if issue_num:
            task_ids_with_gh.add(task["id"])
            # Update kanban task body with issue reference
            new_body = (task.get("body") or "").rstrip() + f"\n\ngithub-issue: #{issue_num}"
            if not dry_run:
                subprocess.run(
                    ["hermes", "kanban", "comment", task["id"], "--body",
                     f"Linked to GitHub Issue #{issue_num} — {repo}"],
                    capture_output=True
                )

    # ── Direction 1: GitHub → Kanban ──────────────────────────────────────────
    # Open issues with no kanban task → create task (scope controlled by --open-scope)
    print("\n[GitHub → Kanban]")
    open_issues = get_open_github_issues(repo, open_scope)
    existing_task_ids_in_issues = set()
    for issue in open_issues:
        tid = extract_kanban_id_from_issue(issue)
        if tid and tid in task_by_id:
            existing_task_ids_in_issues.add(tid)
            continue
        if tid:
            print(f"  ? Issue #{issue['number']} references kanban task {tid} which no longer exists — skipping")
            continue
        # No kanban task yet — create one
        body = (issue.get("body") or "").strip()
        labels = ",".join(l["name"] for l in issue.get("labels", [])) or "(none)"
        assignees = ",".join(a.get("login", "") for a in issue.get("assignees", [])) or "(none)"
        task_body = (
            f"repo: {repo}\n"
            f"github-issue: #{issue['number']}\n"
            f"github-url: {issue['url']}\n"
            f"github-labels: {labels}\n"
            f"github-assignees: {assignees}\n\n"
            f"{body}"
        )
        idempotency_key = f"gh:{repo}#{issue['number']}"
        assignee = COPILOT_ASSIGNEE if has_copilot_assignee(issue) else None
        task_id = create_kanban_task(
            issue["title"],
            task_body,
            dry_run,
            idempotency_key=idempotency_key,
            assignee=assignee,
        )
        if task_id:
            # Avoid high-volume GitHub writes when backfilling all-open scope.
            if open_scope == "agent-ready":
                add_sentinel_to_issue(repo, issue["number"], task_id, dry_run)

    # ── Status sync: Kanban status → GitHub labels ────────────────────────────
    print("\n[Status sync: Kanban → GitHub labels]")
    all_agent_issues = get_all_open_github_issues(repo)
    issue_by_number = {i["number"]: i for i in all_agent_issues}

    for task in tasks:
        issue_num = extract_issue_number_from_task(task)
        if issue_num is None:
            continue
        task_repo = extract_repo_from_task(task)
        if task_repo and task_repo.lower() != repo.lower():
            continue
        issue = issue_by_number.get(issue_num)
        if issue is None:
            continue  # Issue closed or missing — skip

        labels = label_names(issue)
        status = task["status"]

        if status in ("ready", "todo", "triage"):
            if AGENT_READY_LABEL not in labels:
                add_label(repo, issue_num, AGENT_READY_LABEL, dry_run)
            if IN_PROGRESS_LABEL in labels:
                remove_label(repo, issue_num, IN_PROGRESS_LABEL, dry_run)

        elif status == "running":
            if IN_PROGRESS_LABEL not in labels:
                add_label(repo, issue_num, IN_PROGRESS_LABEL, dry_run)
            if AGENT_READY_LABEL in labels:
                remove_label(repo, issue_num, AGENT_READY_LABEL, dry_run)

        elif status == "blocked":
            if BLOCKED_LABEL not in labels:
                add_label(repo, issue_num, BLOCKED_LABEL, dry_run)
            if IN_PROGRESS_LABEL in labels:
                remove_label(repo, issue_num, IN_PROGRESS_LABEL, dry_run)
            if AGENT_READY_LABEL in labels:
                remove_label(repo, issue_num, AGENT_READY_LABEL, dry_run)

        elif status == "done":
            # Get task summary from kanban
            runs_raw = subprocess.run(
                ["hermes", "kanban", "runs", task["id"]],
                capture_output=True, text=True
            ).stdout.strip()
            comment = (
                f"**Hermes Kanban task `{task['id']}` completed.**\n\n"
                f"{runs_raw[:500] if runs_raw else 'No run details available.'}\n\n"
                f"*Auto-synced by kanban-github-sync at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}*"
            )
            close_issue(repo, issue_num, comment, dry_run)

    # ── External agent signal sync (low-cost) ────────────────────────────────
    # Uses one GH list call (state + labels + assignees). No comment polling.
    print("\n[External agent signal sync]")
    all_issue_state = get_all_github_issues_state(repo)
    state_by_number = {i["number"]: i for i in all_issue_state}

    for task in tasks:
        issue_num = extract_issue_number_from_task(task)
        if issue_num is None:
            continue
        task_repo = extract_repo_from_task(task)
        if task_repo and task_repo.lower() != repo.lower():
            continue
        issue = state_by_number.get(issue_num)
        if issue is None:
            continue

        if issue.get("state") != "OPEN":
            if task["status"] != "done":
                complete_kanban_task(
                    task["id"],
                    f"Auto-completed: GitHub issue #{issue_num} is {issue.get('state', 'closed').lower()}.",
                    dry_run,
                )
            continue

        if has_copilot_assignee(issue):
            if task.get("assignee") != COPILOT_ASSIGNEE:
                assign_kanban_task(task["id"], COPILOT_ASSIGNEE, dry_run)
            if task["status"] in ("ready", "todo", "triage"):
                claim_kanban_task(task["id"], dry_run)

        if has_review_requested_label(issue):
            create_review_handoff_task(repo, issue, dry_run)

    # Controlled autonomous drain to avoid token/API spikes.
    bounded_auto_assign_and_dispatch(
        repo=repo,
        tasks=tasks,
        dry_run=dry_run,
        auto_assign_profile=auto_assign_profile,
        auto_assign_limit=auto_assign_limit,
        auto_dispatch_max=auto_dispatch_max,
    )

    print("\n[Done]")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without making changes")
    parser.add_argument("--repo", default=REPO, help=f"GitHub repo (default: {REPO})")
    parser.add_argument(
        "--open-scope",
        choices=["agent-ready", "all"],
        default="agent-ready",
        help="Which open issues to mirror into Kanban (default: agent-ready)",
    )
    parser.add_argument(
        "--auto-assign-profile",
        default="default",
        help="Profile to auto-assign eligible ready tasks to (default: default)",
    )
    parser.add_argument(
        "--auto-assign-limit",
        type=int,
        default=0,
        help="Max eligible ready tasks to auto-assign each run (default: 0)",
    )
    parser.add_argument(
        "--auto-dispatch-max",
        type=int,
        default=0,
        help="If >0, run one dispatch pass with this spawn cap (default: 0)",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN — no changes will be made]\n")

    sync(
        args.repo,
        args.dry_run,
        args.open_scope,
        args.auto_assign_profile,
        args.auto_assign_limit,
        args.auto_dispatch_max,
    )


if __name__ == "__main__":
    main()
