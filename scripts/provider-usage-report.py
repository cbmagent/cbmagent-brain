#!/usr/bin/env python3
"""Generate a redacted provider usage/health report.

This script uses local CLI/status/log signals only. It must not print secrets.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

OUT_DIR = Path("reports/provider-usage")
OPENCLAW_BASE_URL = "http://127.0.0.1:18789"
SECRET_PATTERNS = [
    re.compile(r"gho_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.I),
    re.compile(r"([A-Za-z0-9_]*token[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+", re.I),
    re.compile(r"([A-Za-z0-9_]*secret[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+", re.I),
    re.compile(r"([A-Za-z0-9_]*key[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+", re.I),
]
COOLDOWN_TERMS = [
    "rate limit",
    "ratelimit",
    "rate_limit",
    "quota",
    "cooldown",
    "429",
    "too many requests",
    "exhausted",
    "unavailable",
]
OPENCLAW_LOG_PATHS = [
    Path.home() / ".openclaw/logs/commands.log",
    Path.home() / ".openclaw/logs/openclaw.log",
    Path.home() / ".openclaw/logs/gateway.log",
]


def redact(s: str) -> str:
    out = s
    for pat in SECRET_PATTERNS:
        out = pat.sub(lambda m: (m.group(1) if m.groups() else "") + "[REDACTED]", out)
    return out


def run(cmd: list[str], timeout: int = 15) -> dict:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "ok": p.returncode == 0,
            "exit_code": p.returncode,
            "stdout": redact(p.stdout[-4000:]),
            "stderr": redact(p.stderr[-4000:]),
        }
    except Exception as e:  # pragma: no cover - environment dependent
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)}


def http(url: str, timeout: int = 5, max_bytes: int = 20000) -> dict:
    try:
        req = Request(url, headers={"User-Agent": "cbmagent-provider-report/0.2"})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(max_bytes).decode("utf-8", "ignore")
            return {"ok": True, "status": resp.status, "body_head": redact(body)}
    except Exception as e:  # pragma: no cover - environment dependent
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)}


def grep_log(path: Path, terms: list[str], max_lines: int = 20) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        lines = path.read_text(errors="ignore").splitlines()[-5000:]
    except Exception:
        return []
    hits: list[str] = []
    low_terms = [t.lower() for t in terms]
    for line in lines:
        lo = line.lower()
        if any(t in lo for t in low_terms):
            hits.append(redact(line)[-500:])
    return hits[-max_lines:]


def parse_openclaw_models(models_response: dict) -> dict:
    """Return redacted OpenAI-compatible model inventory from /v1/models."""
    parsed = {
        "ok": False,
        "model_count": 0,
        "model_ids": [],
        "parse_error": None,
    }
    if not models_response.get("ok"):
        parsed["parse_error"] = models_response.get("error") or "models endpoint not ok"
        return parsed
    body = models_response.get("body_head") or ""
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        parsed["parse_error"] = f"JSONDecodeError: {e}"
        return parsed
    raw_models = payload.get("data", []) if isinstance(payload, dict) else []
    model_ids: list[str] = []
    for item in raw_models:
        if isinstance(item, dict) and item.get("id"):
            model_ids.append(str(item["id"]))
    parsed.update(
        {
            "ok": True,
            "model_count": len(model_ids),
            "model_ids": sorted(redact(m) for m in model_ids)[:50],
            "truncated": len(model_ids) > 50,
        }
    )
    return parsed


def collect_cooldown_signals() -> dict:
    sources = {
        "hermes_agent_log": Path.home() / ".hermes/logs/agent.log",
        "hermes_gateway_log": Path.home() / ".hermes/logs/gateway.log",
    }
    for path in OPENCLAW_LOG_PATHS:
        sources[f"openclaw_{path.name.replace('.', '_')}"] = path

    hits_by_source = {name: grep_log(path, COOLDOWN_TERMS) for name, path in sources.items()}
    total_hits = sum(len(hits) for hits in hits_by_source.values())
    cooldown_hits = sum(
        1
        for hits in hits_by_source.values()
        for hit in hits
        if any(term in hit.lower() for term in ["cooldown", "rate limit", "ratelimit", "rate_limit", "429", "too many requests", "quota"])
    )
    return {
        "sources": hits_by_source,
        "total_recent_signal_hits": total_hits,
        "recent_cooldown_hits": cooldown_hits,
    }


def classify_openclaw(root: dict, models: dict, model_inventory: dict, cooldowns: dict) -> dict:
    if root.get("ok") and models.get("ok") and model_inventory.get("model_count", 0) > 0:
        if cooldowns["recent_cooldown_hits"]:
            state = "degraded"
            reason = "Gateway and model inventory are reachable, but recent cooldown/rate-limit signals were found."
            fallback = "Prefer Hermes primary/Nous for urgent work; use OpenClaw for GitHub-specialist tasks after cooldown clears."
        else:
            state = "healthy"
            reason = "Gateway and model inventory are reachable with no recent cooldown/rate-limit log signals."
            fallback = "OpenClaw is available as GitHub/Copilot specialist fallback."
    elif root.get("ok") or models.get("ok"):
        state = "degraded"
        reason = "OpenClaw partially responded, but the gateway root or model inventory check failed."
        fallback = "Use Hermes primary/Nous for new autonomous work; reserve OpenClaw for manual retry or diagnostics."
    else:
        state = "unavailable"
        reason = "OpenClaw gateway did not respond on the local read-only health endpoints."
        fallback = "Route work to Hermes primary/Nous/local deterministic scripts until OpenClaw gateway is restarted."
    return {"state": state, "reason": reason, "fallback_routing": fallback}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    data = {
        "generated_at_utc": ts,
        "redacted": True,
        "commands": {},
        "services": {},
        "signals": {},
        "openclaw": {},
        "notes": [],
    }
    data["commands"]["hermes_status"] = run(["hermes", "status"], timeout=20)
    data["commands"]["hermes_config_provider_model"] = run(
        ["bash", "-lc", "hermes config show 2>/dev/null | grep -E 'Provider|Model|provider|model' || true"], timeout=20
    )
    data["commands"]["hermes_auth_list_names_only"] = run(
        ["bash", "-lc", "hermes auth list 2>/dev/null | sed -E 's/(token|secret|key).*/[REDACTED]/Ig' || true"], timeout=20
    )
    data["commands"]["gh_auth_status"] = run(["gh", "auth", "status"], timeout=20)
    data["commands"]["recent_brain_actions_runs"] = run(
        ["gh", "run", "list", "--repo", "cbmagent/cbmagent-brain", "--limit", "10"], timeout=20
    )
    data["services"]["openclaw_gateway_root"] = http(f"{OPENCLAW_BASE_URL}/", timeout=5)
    data["services"]["openclaw_models"] = http(f"{OPENCLAW_BASE_URL}/v1/models", timeout=5)

    data["openclaw"]["model_inventory"] = parse_openclaw_models(data["services"]["openclaw_models"])
    cooldowns = collect_cooldown_signals()
    data["signals"] = cooldowns["sources"]
    data["openclaw"]["cooldown_summary"] = {
        "total_recent_signal_hits": cooldowns["total_recent_signal_hits"],
        "recent_cooldown_hits": cooldowns["recent_cooldown_hits"],
        "log_paths_checked": [str(p) for p in OPENCLAW_LOG_PATHS],
    }
    data["openclaw"]["health"] = classify_openclaw(
        data["services"]["openclaw_gateway_root"],
        data["services"]["openclaw_models"],
        data["openclaw"]["model_inventory"],
        cooldowns,
    )
    data["notes"].append(
        "OpenAI Codex OAuth/ChatGPT subscription quota is opaque from CLI; report observed failures/cooldowns rather than claiming exact remaining quota."
    )
    data["notes"].append(
        "OpenClaw checks are read-only local HTTP/log inspections; this script does not mutate OpenClaw, GitHub, DNS, or provider settings."
    )
    data["notes"].append(
        "Provider routing recommendations should prefer read-only/local/GitHub Actions tasks when premium model quota appears constrained."
    )

    json_path = OUT_DIR / f"{ts}.json"
    md_path = OUT_DIR / f"{ts}.md"
    latest_json = OUT_DIR / "latest.json"
    latest_md = OUT_DIR / "latest.md"
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    json_path.write_text(json_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")

    health = data["openclaw"]["health"]
    inventory = data["openclaw"]["model_inventory"]
    cooldown_summary = data["openclaw"]["cooldown_summary"]
    lines = [
        "# Provider Usage and Health Report",
        "",
        f"Generated UTC: `{ts}`",
        "",
        "This report is redacted. It does not intentionally print tokens, API keys, bearer values, or credential files.",
        "",
        "## Summary",
        "",
    ]
    hs = data["commands"]["hermes_status"]
    lines.append(f"- Hermes status command: `{'ok' if hs.get('ok') else 'not ok'}`")
    oc = data["services"]["openclaw_gateway_root"]
    lines.append(f"- OpenClaw gateway root: `{'ok' if oc.get('ok') else 'not ok'}` {oc.get('status', '')}")
    lines.append(f"- OpenClaw health: `{health['state']}` - {health['reason']}")
    lines.append(f"- OpenClaw models visible: `{inventory.get('model_count', 0)}`")
    lines.append(f"- Recent OpenClaw/Hermes cooldown hits: `{cooldown_summary['recent_cooldown_hits']}`")
    lines.append(f"- Recommended fallback routing: {health['fallback_routing']}")
    gh = data["commands"]["gh_auth_status"]
    lines.append(f"- GitHub CLI auth: `{'ok' if gh.get('ok') else 'not ok'}`")
    lines += [
        "",
        "## OpenClaw Model Inventory",
        "",
    ]
    if inventory.get("model_ids"):
        for model in inventory["model_ids"][:25]:
            lines.append(f"- `{model}`")
        if inventory.get("truncated"):
            lines.append("- ... inventory truncated in Markdown; see JSON report for full redacted sample.")
    else:
        lines.append(f"- No models parsed. Parse/status detail: `{inventory.get('parse_error') or 'none'}`")
    lines += [
        "",
        "## Current Config Signals",
        "",
        "```text",
        data["commands"]["hermes_config_provider_model"].get("stdout", "")
        or data["commands"]["hermes_config_provider_model"].get("stderr", ""),
        "```",
        "",
        "## Auth/Provider Names",
        "",
        "```text",
        data["commands"]["hermes_auth_list_names_only"].get("stdout", "")
        or data["commands"]["hermes_auth_list_names_only"].get("stderr", ""),
        "```",
        "",
        "## Recent GitHub Actions",
        "",
        "```text",
        data["commands"]["recent_brain_actions_runs"].get("stdout", "") or "No runs found or command unavailable.",
        "```",
        "",
        "## Recent Rate Limit / Cooldown Signals",
        "",
    ]
    for log_name, hits in data["signals"].items():
        lines += [f"### {log_name}", ""]
        if not hits:
            lines.append("- No recent matching signals found.")
        else:
            for h in hits[-10:]:
                lines.append(f"- `{h}`")
        lines.append("")
    lines += [
        "## Recommendations",
        "",
        "- Treat OpenAI Codex OAuth quota as opaque; monitor observed rate-limit/cooldown errors.",
        f"- OpenClaw routing: {health['fallback_routing']}",
        "- Use Nous/local tools as fallback/specialists when primary provider or OpenClaw signals failures.",
        "- Keep deterministic audits in scripts/GitHub Actions so premium model quota is reserved for reasoning/coding.",
        "- Add scheduled provider report workflow after read-only environment design is finalized.",
        "",
    ]
    md = "\n".join(lines)
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
