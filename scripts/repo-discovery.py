#!/usr/bin/env python3
"""Discover accessible GitHub repos and map likely repositories to portfolio domains.

This script uses `gh` only; it never reads or prints token values. It outputs
reports/repo-inventory/<timestamp>.{json,md} and latest.{json,md}.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_FILE = ROOT / "portfolio" / "domains.yaml"
OUT_DIR = ROOT / "reports" / "repo-inventory"
OWNERS = ["cbmagent", "clarkemoyer", "FreeForCharity"]


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def load_domains() -> list[dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise SystemExit("PyYAML is required for repo discovery because domains.yaml is structured") from exc
    data = yaml.safe_load(DOMAIN_FILE.read_text(encoding="utf-8")) or {}
    return data.get("domains", [])


def gh_repo_list(owner: str) -> tuple[list[dict[str, Any]], str | None]:
    code, out, err = run([
        "gh", "repo", "list", owner, "--limit", "1000", "--json",
        "name,nameWithOwner,url,description,visibility,isPrivate,defaultBranchRef,homepageUrl,repositoryTopics,updatedAt,primaryLanguage"
    ], timeout=120)
    if code != 0:
        return [], (err or out).strip()
    try:
        return json.loads(out), None
    except json.JSONDecodeError as exc:
        return [], f"JSON parse failed for {owner}: {exc}"


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def domain_candidates(domain: str) -> set[str]:
    host = domain.lower()
    no_tld = ".".join(host.split(".")[:-1]) if "." in host else host
    return {normalize(host), normalize(no_tld), normalize(host.replace(".", "-")), normalize(host.replace(".", "_"))}


def score_repo(domain: dict[str, Any], repo: dict[str, Any]) -> tuple[int, list[str]]:
    d = domain.get("domain", "")
    candidates = domain_candidates(d)
    name = repo.get("name", "") or ""
    full = repo.get("nameWithOwner", "") or ""
    desc = repo.get("description", "") or ""
    home = repo.get("homepageUrl", "") or ""
    topics = " ".join(t.get("name", "") for t in (repo.get("repositoryTopics") or []))
    haystacks = {
        "name": normalize(name),
        "full": normalize(full),
        "description": normalize(desc),
        "homepage": normalize(home),
        "topics": normalize(topics),
    }
    score = 0
    reasons: list[str] = []
    declared = domain.get("repo")
    if declared and declared != "TBD" and declared.lower() == full.lower():
        score += 100
        reasons.append("declared repo exact match")
    for cand in candidates:
        if not cand:
            continue
        if cand == haystacks["name"]:
            score += 80; reasons.append("repo name matches domain")
        elif cand in haystacks["name"]:
            score += 50; reasons.append("repo name contains domain stem")
        if cand and cand in haystacks["homepage"]:
            score += 60; reasons.append("homepage contains domain")
        if cand and cand in haystacks["description"]:
            score += 25; reasons.append("description contains domain")
        if cand and cand in haystacks["topics"]:
            score += 20; reasons.append("topic contains domain")
    return score, sorted(set(reasons))


def main() -> int:
    domains = load_domains()
    owner_results: dict[str, Any] = {}
    repos: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    for owner in OWNERS:
        found, err = gh_repo_list(owner)
        owner_results[owner] = {"count": len(found), "error": err}
        repos.extend(found)
        if err:
            errors[owner] = err
    mappings = []
    missing = []
    for d in domains:
        scored = []
        for r in repos:
            score, reasons = score_repo(d, r)
            if score > 0:
                scored.append({"score": score, "reasons": reasons, "repo": r})
        scored.sort(key=lambda x: x["score"], reverse=True)
        declared = d.get("repo")
        top = scored[:5]
        status = "mapped" if top else "missing-or-unknown"
        if declared and declared != "TBD" and not any(x["repo"].get("nameWithOwner", "").lower() == str(declared).lower() for x in top):
            status = "declared-repo-not-accessible-or-not-found"
        if not top and d.get("role") != "redirect-only":
            missing.append(d.get("domain"))
        mappings.append({
            "domain": d.get("domain"),
            "role": d.get("role"),
            "priority": d.get("priority"),
            "declared_repo": declared,
            "status": status,
            "top_matches": [
                {
                    "repo": x["repo"].get("nameWithOwner"),
                    "url": x["repo"].get("url"),
                    "visibility": x["repo"].get("visibility"),
                    "description": x["repo"].get("description"),
                    "homepageUrl": x["repo"].get("homepageUrl"),
                    "score": x["score"],
                    "reasons": x["reasons"],
                }
                for x in top
            ],
        })
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    report = {
        "generated_at": ts,
        "owners": owner_results,
        "repo_count": len(repos),
        "domain_count": len(domains),
        "missing_canonical_domains": missing,
        "mappings": mappings,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"{ts}.json"
    md_path = OUT_DIR / f"{ts}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / "latest.json").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    lines = [
        "# Repository Discovery Report",
        "",
        f"Generated: `{ts}`",
        "",
        "## Owner Access",
        "",
    ]
    for owner, info in owner_results.items():
        err = info.get("error")
        lines.append(f"- `{owner}`: {info.get('count', 0)} repos" + (f"; error: `{err}`" if err else ""))
    lines += ["", "## Domain Mapping", ""]
    for m in mappings:
        lines.append(f"### {m['domain']}")
        lines.append(f"- role: `{m.get('role')}`")
        lines.append(f"- priority: `{m.get('priority')}`")
        lines.append(f"- declared repo: `{m.get('declared_repo')}`")
        lines.append(f"- status: `{m.get('status')}`")
        if m["top_matches"]:
            lines.append("- top matches:")
            for t in m["top_matches"]:
                lines.append(f"  - [{t['repo']}]({t['url']}) — score {t['score']}; {', '.join(t['reasons'])}")
        else:
            lines.append("- top matches: none")
        lines.append("")
    if missing:
        lines += ["## Missing / Unknown Canonical Domains", ""]
        for d in missing:
            lines.append(f"- `{d}`")
    md_path.write_text("\n".join(lines).rstrip()+"\n", encoding="utf-8")
    (OUT_DIR / "latest.md").write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(md_path)
    return 0 if not errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
