#!/usr/bin/env python3
"""Create one GitHub Issue per portfolio domain entry.

The script is idempotent: it scans existing open and closed issues for a
stable marker before creating anything. It uses the GitHub CLI and never reads
or prints credentials.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_FILE = ROOT / "portfolio" / "domains.yaml"
DASHBOARD_URL = "https://github.com/cbmagent/cbmagent-brain/blob/main/docs/portfolio-dashboard.md"
SOURCE_ISSUE = "#36"


@dataclass(frozen=True)
class PlannedIssue:
    domain: str
    role: str
    title: str
    body: str
    labels: tuple[str, ...]
    marker: str


def run(cmd: list[str], *, timeout: int = 60, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        input=input_text,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def load_domains() -> list[dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - environment guard
        raise SystemExit("PyYAML is required to read portfolio/domains.yaml") from exc
    data = yaml.safe_load(DOMAIN_FILE.read_text(encoding="utf-8")) or {}
    domains = data.get("domains", [])
    if not isinstance(domains, list):
        raise SystemExit("portfolio/domains.yaml must contain a top-level domains list")
    return domains


def issue_marker(domain: str) -> str:
    return f"<!-- domain-issue: {domain} -->"


def labels_for(domain: dict[str, Any]) -> tuple[str, ...]:
    role = str(domain.get("role", ""))
    labels = ["agent-brain", "domain-audit"]
    if role == "redirect-only":
        labels.append("cloudflare")
    else:
        labels.extend(["site-migration", "github-pages"])
    return tuple(dict.fromkeys(labels))


def canonical_body(domain: dict[str, Any], marker: str) -> str:
    name = domain["domain"]
    repo = domain.get("repo", "TBD")
    priority = domain.get("priority", "unknown")
    current_state = domain.get("current_state", "unknown")
    target_hosting = domain.get("target_hosting", "github-pages")
    notes = domain.get("notes")
    notes_block = f"\nNotes: {notes}\n" if notes else ""
    return f"""## Domain
`{name}`

## Source
- Portfolio registry: `portfolio/domains.yaml`
- Dashboard: {DASHBOARD_URL}
- Generated from: {SOURCE_ISSUE}

## Current metadata
- Role: `{domain.get('role')}`
- Target hosting: `{target_hosting}`
- Repo: `{repo}`
- Priority: `{priority}`
- Current state: `{current_state}`{notes_block}
## Migration / repo / Pages checklist
- [ ] Confirm canonical content owner and desired launch/cutover scope.
- [ ] Confirm or create the site repository; current registry value: `{repo}`.
- [ ] Add or verify GitHub Pages build/deploy workflow in the site repo.
- [ ] Add custom domain and `CNAME`/Pages configuration in the site repo.
- [ ] Run read-only DNS/HTTP/Pages readiness checks from this brain repo.
- [ ] Prepare Cloudflare DNS changes through a protected, write-gated workflow if needed.
- [ ] Verify HTTPS, canonical redirects, sitemap/robots, and basic accessibility after launch.
- [ ] Update `portfolio/domains.yaml` and the portfolio dashboard with the final state.

## Safety boundary
Agents may prepare branches, reports, and dry-run plans autonomously. Production DNS/provider writes must remain gated through approved GitHub Actions environments or human approval.

{marker}
"""


def redirect_body(domain: dict[str, Any], marker: str) -> str:
    name = domain["domain"]
    target = domain.get("canonical_target", "TBD")
    priority = domain.get("priority", "unknown")
    target_hosting = domain.get("target_hosting", "cloudflare-redirect")
    notes = domain.get("notes")
    notes_block = f"\nNotes: {notes}\n" if notes else ""
    return f"""## Redirect-only domain
`{name}` → `{target}`

## Source
- Portfolio registry: `portfolio/domains.yaml`
- Dashboard: {DASHBOARD_URL}
- Generated from: {SOURCE_ISSUE}

## Current metadata
- Role: `{domain.get('role')}`
- Target hosting: `{target_hosting}`
- Canonical target: `{target}`
- Priority: `{priority}`{notes_block}
## Cloudflare redirect checklist
- [ ] Confirm `{target}` is the intended canonical destination.
- [ ] Run read-only DNS/HTTP checks for `{name}` and `{target}`.
- [ ] Prepare a Cloudflare redirect rule/page rule plan in dry-run form.
- [ ] Execute production redirect changes only through a protected, write-gated workflow or human-approved action.
- [ ] Verify HTTP and HTTPS redirect status, destination URL, and absence of redirect loops.
- [ ] Update `portfolio/domains.yaml` and the portfolio dashboard with the verified redirect state.

## Safety boundary
Agents may prepare branches, reports, and dry-run plans autonomously. Production DNS/provider writes must remain gated through approved GitHub Actions environments or human approval.

{marker}
"""


def plan_issue(domain: dict[str, Any]) -> PlannedIssue:
    name = str(domain.get("domain", "")).strip()
    if not name:
        raise ValueError(f"domain entry is missing domain: {domain!r}")
    role = str(domain.get("role", "")).strip() or "unknown"
    marker = issue_marker(name)
    if role == "redirect-only":
        target = domain.get("canonical_target", "TBD")
        title = f"Redirect setup: {name} to {target}"
        body = redirect_body(domain, marker)
    else:
        title = f"Site migration: {name}"
        body = canonical_body(domain, marker)
    return PlannedIssue(name, role, title, body, labels_for(domain), marker)


def existing_issues() -> list[dict[str, Any]]:
    proc = run([
        "gh",
        "issue",
        "list",
        "--state",
        "all",
        "--limit",
        "1000",
        "--json",
        "number,title,body,url,state",
    ], timeout=120)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout).strip())
    return json.loads(proc.stdout or "[]")


def existing_label_names() -> set[str]:
    proc = run(["gh", "label", "list", "--limit", "1000", "--json", "name"], timeout=60)
    if proc.returncode != 0:
        # Avoid failing issue generation just because label listing is unavailable.
        return set()
    return {item.get("name", "") for item in json.loads(proc.stdout or "[]")}


def find_existing(planned: PlannedIssue, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    for issue in issues:
        body = issue.get("body") or ""
        if planned.marker in body:
            return issue
    for issue in issues:
        if issue.get("title") == planned.title:
            return issue
    return None


def create_issue(planned: PlannedIssue, valid_labels: set[str]) -> str:
    body_file = ROOT / ".tmp-domain-issue-body.md"
    body_file.write_text(planned.body, encoding="utf-8")
    try:
        cmd = ["gh", "issue", "create", "--title", planned.title, "--body-file", str(body_file)]
        labels = [label for label in planned.labels if not valid_labels or label in valid_labels]
        for label in labels:
            cmd.extend(["--label", label])
        proc = run(cmd, timeout=120)
        if proc.returncode != 0:
            raise SystemExit((proc.stderr or proc.stdout).strip())
        return proc.stdout.strip()
    finally:
        try:
            body_file.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Create missing GitHub issues. Without this, only print the plan.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary JSON.")
    args = parser.parse_args(argv)

    planned = [plan_issue(domain) for domain in load_domains()]
    issues = existing_issues()
    valid_labels = existing_label_names()

    summary: dict[str, Any] = {"created": [], "existing": [], "planned_count": len(planned), "apply": args.apply}
    for item in planned:
        found = find_existing(item, issues)
        if found:
            summary["existing"].append({"domain": item.domain, "title": item.title, "number": found.get("number"), "url": found.get("url"), "state": found.get("state")})
            continue
        if args.apply:
            url = create_issue(item, valid_labels)
            summary["created"].append({"domain": item.domain, "title": item.title, "url": url})
            # Keep the in-memory index current so duplicate domains in the YAML cannot create duplicates.
            issues.append({"title": item.title, "body": item.body, "url": url, "state": "OPEN"})
        else:
            summary["created"].append({"domain": item.domain, "title": item.title, "url": None})

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        action = "Created" if args.apply else "Would create"
        print(f"Planned domain issues: {summary['planned_count']}")
        print(f"Existing matches: {len(summary['existing'])}")
        print(f"{action}: {len(summary['created'])}")
        for item in summary["created"]:
            suffix = f" -> {item['url']}" if item.get("url") else ""
            print(f"- {item['domain']}: {item['title']}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
