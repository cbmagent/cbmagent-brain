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
  python3 scripts/kanban-github-sync.py [--dry-run] [--repo OWNER/REPO]
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
AGENT_BRAIN_LABEL = "agent-brain"
KANBAN_SENTINEL_RE = re.compile(r"<!-- kanban-task: ([a-zA-Z0-9_-]+) -->")
GITHUB_ISSUE_RE = re.compile(r"github-issue:\s*#(\d+)", re.IGNORECASE)


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


def get_github_issues(repo: str):
    raw = gh(
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--label", AGENT_READY_LABEL,
        "--limit", "100",
        "--json", "number,title,body,url,labels",
    )
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


def extract_kanban_id_from_issue(issue: dict) -> str | None:
    body = issue.get("body") or ""
    m = KANBAN_SENTINEL_RE.search(body)
    return m.group(1) if m else None


def extract_issue_number_from_task(task: dict) -> int | None:
    body = task.get("body") or ""
    m = GITHUB_ISSUE_RE.search(body)
    return int(m.group(1)) if m else None


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


def create_kanban_task(title: str, body: str, dry_run: bool) -> str | None:
    print(f"  + Kanban task: {title!r}")
    if dry_run:
        return None
    result = subprocess.run(
        ["hermes", "kanban", "create", title, "--body", body],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  [err] kanban create failed: {result.stderr.strip()}", file=sys.stderr)
        return None
    # hermes kanban create prints the task id on stdout
    m = re.search(r"([a-f0-9]{8,})", result.stdout)
    return m.group(1) if m else None

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


def sync(repo: str, dry_run: bool):
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
    # Issues labelled agent-ready with no kanban task → create task
    print("\n[GitHub → Kanban]")
    agent_ready_issues = get_github_issues(repo)
    existing_task_ids_in_issues = set()
    for issue in agent_ready_issues:
        tid = extract_kanban_id_from_issue(issue)
        if tid and tid in task_by_id:
            existing_task_ids_in_issues.add(tid)
            continue
        if tid:
            print(f"  ? Issue #{issue['number']} references kanban task {tid} which no longer exists — skipping")
            continue
        # No kanban task yet — create one
        body = (issue.get("body") or "").strip()
        task_body = f"{body}\n\ngithub-issue: #{issue['number']}\ngithub-url: {issue['url']}"
        task_id = create_kanban_task(issue["title"], task_body, dry_run)
        if task_id:
            add_sentinel_to_issue(repo, issue["number"], task_id, dry_run)

    # ── Status sync: Kanban status → GitHub labels ────────────────────────────
    print("\n[Status sync: Kanban → GitHub labels]")
    all_agent_issues = get_all_open_github_issues(repo)
    issue_by_number = {i["number"]: i for i in all_agent_issues}

    for task in tasks:
        issue_num = extract_issue_number_from_task(task)
        if issue_num is None:
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

    print("\n[Done]")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without making changes")
    parser.add_argument("--repo", default=REPO, help=f"GitHub repo (default: {REPO})")
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN — no changes will be made]\n")

    sync(args.repo, args.dry_run)


if __name__ == "__main__":
    main()
