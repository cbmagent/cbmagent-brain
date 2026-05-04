#!/usr/bin/env python3
"""GitHub Pages readiness checker for the cbmagent portfolio.

Read-only. No credentials required for public checks.
Uses GitHub public API for repo existence and Pages config.
Checks DNS CNAME, A records, HTTPS status, and classifies per-domain readiness.

Outputs:
  - reports/pages-readiness/pages-readiness-<date>.json  (machine-readable)
  - reports/pages-readiness/pages-readiness-latest.md    (dashboard-friendly)

Readiness classifications:
  READY          – DNS → GitHub Pages IPs/CNAME, HTTPS 200, Pages enabled
  DNS_ONLY       – DNS pointing to GitHub but no HTTPS or Pages response yet
  REPO_MISSING   – No repo mapped and domain status is unknown
  WORDPRESS      – Domain is serving WordPress (migration needed)
  REDIRECTOR     – Domain is a redirect-only role (expected, not a gap)
  LIVE_OTHER     – Domain is live but not on GitHub Pages
  UNREACHABLE    – No DNS or HTTP response
  NEEDS_AUDIT    – Insufficient info to classify (repo TBD or audit-needed)
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import re
import socket
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DOMAINS_YAML = ROOT / "portfolio" / "domains.yaml"
OUT_DIR = ROOT / "reports" / "pages-readiness"

# GitHub Pages canonical A/AAAA records
GITHUB_PAGES_A = {
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
}
GITHUB_PAGES_AAAA = {
    "2606:50c0:8000::153",
    "2606:50c0:8001::153",
    "2606:50c0:8002::153",
    "2606:50c0:8003::153",
}

GITHUB_IO_SUFFIX = ".github.io"
GH_API_BASE = "https://api.github.com"


# ---------------------------------------------------------------------------
# YAML loader (graceful fallback to regex if PyYAML not installed)
# ---------------------------------------------------------------------------

def load_domains() -> list[dict]:
    text = DOMAINS_YAML.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        return data.get("domains", [])
    except Exception:
        # Fallback: extract only domain names
        return [
            {"domain": m.group(1)}
            for m in re.finditer(r"^\s*- domain:\s*(\S+)", text, re.M)
        ]


# ---------------------------------------------------------------------------
# DNS helpers
# ---------------------------------------------------------------------------

def dig(domain: str, rtype: str) -> list[str]:
    try:
        p = subprocess.run(
            ["dig", "+short", rtype, domain],
            text=True,
            capture_output=True,
            timeout=10,
        )
        return [x.strip().rstrip(".") for x in p.stdout.splitlines() if x.strip()]
    except Exception:
        return []


def resolve_cname_chain(domain: str) -> list[str]:
    """Return list of CNAMEs in order (not including final A)."""
    seen: list[str] = []
    current = domain
    for _ in range(8):  # guard against loops
        cnames = dig(current, "CNAME")
        if not cnames:
            break
        target = cnames[0].rstrip(".")
        if target in seen:
            break
        seen.append(target)
        current = target
    return seen


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http_probe(domain: str, scheme: str = "https") -> dict:
    url = f"{scheme}://{domain}/"
    req = Request(url, headers={"User-Agent": "cbmagent-brain-pages-readiness/0.1"})
    ctx = ssl.create_default_context()
    try:
        with urlopen(req, timeout=12, context=ctx) as resp:
            body = resp.read(200_000).decode("utf-8", "ignore")
            final_url = resp.geturl()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            signals: set[str] = set()
            hay = body[:50_000].lower() + "\n" + "\n".join(
                f"{k}: {v}" for k, v in headers.items()
            )
            if "wp-content" in hay or "wp-includes" in hay or "wordpress" in hay:
                signals.add("wordpress")
            if "github.io" in hay or "github pages" in hay:
                signals.add("github-pages")
            if "cloudflare" in headers.get("server", "").lower() or headers.get(
                "cf-ray"
            ):
                signals.add("cloudflare")
            return {
                "ok": True,
                "status": resp.status,
                "final_url": final_url,
                "server": headers.get("server", ""),
                "signals": sorted(signals),
            }
    except HTTPError as e:
        return {"ok": False, "status": e.code, "error": str(e), "final_url": url, "signals": []}
    except Exception as e:
        return {
            "ok": False,
            "status": None,
            "error": type(e).__name__ + ": " + str(e),
            "final_url": url,
            "signals": [],
        }


# ---------------------------------------------------------------------------
# GitHub API helper (public, unauthenticated — rate-limited to 60 req/hr)
# ---------------------------------------------------------------------------

def gh_api_get(path: str) -> dict | None:
    url = GH_API_BASE + path
    req = Request(url, headers={"User-Agent": "cbmagent-brain-pages-readiness/0.1", "Accept": "application/vnd.github+json"})
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 404:
            return None
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}


def check_repo_and_pages(repo_slug: str) -> dict:
    """Return {'repo_exists': bool, 'pages_enabled': bool, 'pages_url': str|None}."""
    if not repo_slug or repo_slug.upper() == "TBD":
        return {"repo_exists": None, "pages_enabled": None, "pages_url": None}
    repo_info = gh_api_get(f"/repos/{repo_slug}")
    if repo_info is None:
        return {"repo_exists": False, "pages_enabled": None, "pages_url": None}
    if "_error" in repo_info:
        return {"repo_exists": None, "pages_enabled": None, "pages_url": None, "error": repo_info["_error"]}
    # Check Pages
    pages_info = gh_api_get(f"/repos/{repo_slug}/pages")
    if pages_info is None:
        return {"repo_exists": True, "pages_enabled": False, "pages_url": None}
    if "_error" in pages_info:
        return {"repo_exists": True, "pages_enabled": None, "pages_url": None}
    return {
        "repo_exists": True,
        "pages_enabled": True,
        "pages_url": pages_info.get("html_url"),
        "pages_cname": pages_info.get("cname"),
        "pages_status": pages_info.get("status"),
    }


# ---------------------------------------------------------------------------
# Per-domain check
# ---------------------------------------------------------------------------

def check_domain(meta: dict) -> dict:
    domain = meta["domain"]
    role = meta.get("role", "canonical-site")
    repo = meta.get("repo", "TBD")
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    result: dict = {
        "domain": domain,
        "role": role,
        "repo": repo,
        "priority": meta.get("priority", ""),
        "current_state": meta.get("current_state", ""),
        "checked_at": now,
    }

    # Skip detailed checks for pure redirectors
    if role == "redirect-only":
        result["classification"] = "REDIRECTOR"
        result["summary"] = "Redirect-only domain; no Pages required."
        return result

    # DNS
    a_records = dig(domain, "A")
    aaaa_records = dig(domain, "AAAA")
    cname_chain = resolve_cname_chain(domain)
    www_a = dig(f"www.{domain}", "A")
    www_cname = resolve_cname_chain(f"www.{domain}")

    result["dns"] = {
        "a": a_records,
        "aaaa": aaaa_records,
        "cname_chain": cname_chain,
        "www_a": www_a,
        "www_cname": www_cname,
    }

    # HTTP/HTTPS
    https_result = http_probe(domain, "https")
    http_result = http_probe(domain, "http")
    result["http_probe"] = {"https": https_result, "http": http_result}

    # GitHub repo + Pages API
    gh_info = check_repo_and_pages(repo)
    result["github"] = gh_info

    # Classify
    all_cnames = " ".join(cname_chain + www_cname).lower()
    all_a = set(a_records + www_a)
    all_signals = set(
        https_result.get("signals", []) + http_result.get("signals", [])
    )

    points_to_gh = (
        bool(all_a.intersection(GITHUB_PAGES_A))
        or GITHUB_IO_SUFFIX in all_cnames
        or "github-pages" in all_signals
    )

    if "wordpress" in all_signals:
        cls = "WORDPRESS"
        summary = "Live WordPress site — migration needed before Pages cutover."
    elif points_to_gh and https_result.get("ok"):
        cls = "READY"
        summary = "DNS → GitHub Pages, HTTPS 200."
    elif points_to_gh and not https_result.get("ok"):
        cls = "DNS_ONLY"
        summary = "DNS points to GitHub Pages but HTTPS not yet responding."
    elif not a_records and not aaaa_records and not cname_chain:
        cls = "UNREACHABLE"
        summary = "No DNS records found."
    elif repo == "TBD" or meta.get("current_state") == "audit-needed":
        cls = "NEEDS_AUDIT"
        summary = "Repo TBD or audit-needed; classify after domain audit."
    elif https_result.get("ok") or http_result.get("ok"):
        cls = "LIVE_OTHER"
        summary = "Live but not on GitHub Pages."
    else:
        cls = "NEEDS_AUDIT"
        summary = "Could not determine status; manual review needed."

    result["classification"] = cls
    result["summary"] = summary
    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

CLASSIFICATION_ORDER = [
    "READY", "DNS_ONLY", "WORDPRESS", "LIVE_OTHER",
    "UNREACHABLE", "NEEDS_AUDIT", "REDIRECTOR",
]

CLASSIFICATION_EMOJI = {
    "READY": "✅",
    "DNS_ONLY": "🔶",
    "WORDPRESS": "🔴",
    "LIVE_OTHER": "🟡",
    "UNREACHABLE": "⚫",
    "NEEDS_AUDIT": "❓",
    "REDIRECTOR": "↩️",
}


def build_markdown(results: list[dict], run_date: str) -> str:
    by_cls: dict[str, list[dict]] = {c: [] for c in CLASSIFICATION_ORDER}
    for r in results:
        cls = r.get("classification", "NEEDS_AUDIT")
        by_cls.setdefault(cls, []).append(r)

    lines = [
        f"# GitHub Pages Readiness Report",
        f"",
        f"Generated: {run_date}  ",
        f"Domains checked: {len(results)}",
        f"",
        "## Summary",
        "",
        "| Classification | Count |",
        "|---|---|",
    ]
    for cls in CLASSIFICATION_ORDER:
        count = len(by_cls.get(cls, []))
        if count:
            emoji = CLASSIFICATION_EMOJI.get(cls, "")
            lines.append(f"| {emoji} {cls} | {count} |")

    lines += ["", "---", ""]

    for cls in CLASSIFICATION_ORDER:
        items = by_cls.get(cls, [])
        if not items:
            continue
        emoji = CLASSIFICATION_EMOJI.get(cls, "")
        lines += [f"## {emoji} {cls} ({len(items)})", ""]
        for r in sorted(items, key=lambda x: x.get("priority", "p9")):
            domain = r["domain"]
            repo = r.get("repo") or "—"
            summary = r.get("summary", "")
            pri = r.get("priority", "")
            lines.append(f"### {domain}")
            lines.append(f"- **Priority:** {pri}  ")
            lines.append(f"- **Repo:** `{repo}`  ")
            lines.append(f"- **Summary:** {summary}")
            dns = r.get("dns", {})
            if dns.get("a"):
                lines.append(f"- **A records:** {', '.join(dns['a'])}")
            if dns.get("cname_chain"):
                lines.append(f"- **CNAME chain:** {' → '.join(dns['cname_chain'])}")
            gh = r.get("github", {})
            if gh.get("repo_exists") is False:
                lines.append("- **GitHub repo:** ❌ not found")
            elif gh.get("pages_enabled"):
                pages_url = gh.get("pages_url") or ""
                lines.append(f"- **GitHub Pages:** ✅ enabled ({pages_url})")
            elif gh.get("pages_enabled") is False:
                lines.append("- **GitHub Pages:** ⚠️ repo exists but Pages not enabled")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    domains = load_domains()
    if not domains:
        print("ERROR: No domains loaded from domains.yaml", file=sys.stderr)
        sys.exit(1)

    print(f"Checking {len(domains)} domains...", file=sys.stderr)

    results: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(check_domain, meta): meta for meta in domains}
        for fut in cf.as_completed(futs):
            try:
                r = fut.result()
                results.append(r)
                cls = r.get("classification", "?")
                print(f"  {cls:15s} {r['domain']}", file=sys.stderr)
            except Exception as exc:
                meta = futs[fut]
                print(f"  ERROR {meta['domain']}: {exc}", file=sys.stderr)
                results.append({"domain": meta["domain"], "classification": "NEEDS_AUDIT", "summary": f"Check error: {exc}"})

    results.sort(key=lambda r: (
        CLASSIFICATION_ORDER.index(r.get("classification", "NEEDS_AUDIT"))
        if r.get("classification") in CLASSIFICATION_ORDER else 99,
        r.get("priority", "p9"),
        r.get("domain", ""),
    ))

    run_date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    run_ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # JSON
    json_path = OUT_DIR / f"pages-readiness-{run_ts}.json"
    json_path.write_text(json.dumps({"run_date": run_date, "domains": results}, indent=2), encoding="utf-8")

    # Markdown (latest)
    md = build_markdown(results, run_date)
    md_path = OUT_DIR / "pages-readiness-latest.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"\nReport written: {md_path}", file=sys.stderr)
    print(f"JSON written:   {json_path}", file=sys.stderr)
    print(md)


if __name__ == "__main__":
    main()
