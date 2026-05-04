#!/usr/bin/env python3
"""Hermes provider/model verification workflow.

Usage:
    python3 scripts/hermes-verification.py [--check-fallbacks]

- Redacts all auth details.
- Runs a tiny smoke prompt with the primary/fallback providers.
- Reports pass/fail and latency.
- Does not expose prompt tokens/secrets.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
from pathlib import Path

OUT_DIR = Path("reports/provider-usage")
SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"gho_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"sk-[A-Za-z0-9]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.I),
    re.compile(r"[A-Za-z0-9_]*token[A-Za0-9_]*\s*[:=]\s*[^\s,}\\]]+", re.I),
    re.compile(r"[A-Za-z0-9_]*secret[A-Za-z0-9_]*\s*[:=]\s*[^\s,}\\]]+", re.I),
    re.compile(r"[A-Za-z0-9_]*key[A-Za-z0-9_]*\s*[:=]\s*[^\s,}\\]]+", re.I),
]

def redact(text: str) -> str:
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub(lambda m: (m.group(1) if m.groups() else "") + "[REDACTED]", out)
    return out

def run(cmd: list[str], cwd: Path | None = None, timeout: int = 25) -> dict:
    try:
        start = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        elapsed = time.time() - start
        return {
            "ok": p.returncode == 0,
            "exit_code": p.returncode,
            "stdout": redact(p.stdout),
            "stderr": redact(p.stderr),
            "elapsed_sec": round(elapsed, 3),
            "timeout_sec": timeout,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "elapsed_sec": round(timeout, 3)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e), "elapsed_sec": 0.0}

def parse_primary_provider(stdout: str) -> dict:
    # Look for lines like: Primary:   gpt-5.5  (via openai-codex)
    primary = {"model": None, "provider": None}
    for line in stdout.splitlines():
        line = redact(line)
        m = re.search(r"Primary:\s+(\S+)\s+\(via\s+(\S+)\)", line)
        if m:
            primary["model"] = m.group(1)
            primary["provider"] = m.group(2)
            break
    return primary

def parse_fallbacks(stdout: str) -> list[dict]:
    # Look for: 1. anthropic/claude-sonnet-4.6  (via nous)
    fallbacks = []
    for line in stdout.splitlines():
        line = redact(line)
        m = re.match(r"\s*(\d+)\.\s+(\S+)\s+\(via\s+(\S+)\)", line)
        if m:
            fallbacks.append({"rank": int(m.group(1)), "model": m.group(2), "provider": m.group(3)})
    return fallbacks

def parse_config_provider(stdout: str) -> dict:
    info = {"model": None, "provider": None}
    for line in stdout.splitlines():
        line = redact(line)
        # Handle JSON-ish entries or plain text
        m = re.search(r"['\"]provider['\"]\s*:\s*['\"]([^'\"]+)['\"]", line)
        if m:
            info["provider"] = m.group(1)
        m2 = re.search(r"['\"]default['\"]\s*:\s*['\"]([^'\"]+)['\"]", line)
        if m2:
            info["model"] = m2.group(1)
        # Also plain text: "Model:        {'default': 'gpt-5.5', 'provider': 'openai-codex'}"
        if not info["provider"]:
            m3 = re.search(r"provider['\"]?\s*:\s*['\"]?([^\s,}]+)", line, re.I)
            if m3:
                info["provider"] = m3.group(1).strip("'\"")
        if not info["model"]:
            m4 = re.search(r"default['\"]?\s*:\s*['\"]?([^\s,}]+)", line, re.I)
            if m4:
                info["model"] = m4.group(1).strip("'\"")
    return info

def smoke_test(provider: str | None, model: str | None, timeout: int = 25) -> dict:
    """Run a tiny smoke prompt via `hermes chat -q`."""
    cmd = ["hermes", "chat", "-q", "Reply with the word pong.", "-Q", "--max-turns", "2"]
    if provider:
        cmd += ["--provider", provider]
    if model:
        cmd += ["--model", model]
    # Pass toolsets none to avoid expensive tool invocations
    cmd += ["--toolsets", "none"]
    result = run(cmd, timeout=timeout)
    if not result["ok"]:
        return {"ok": False, "error": result.get("stderr", result.get("error", "unknown")), "latency_sec": result.get("elapsed_sec", 0)}
    body = result["stdout"]
    # Check if response looks like failure/cooldown
    failure_signals = ["rate limit", "ratelimited", "429", "exhausted", "unavailable", "timeout", "error", "failed", "cooldown", "quota"]
    has_failure = any(s in body.lower() for s in failure_signals)
    pong_found = "pong" in body.lower()
    return {
        "ok": not has_failure and pong_found,
        "pong_found": pong_found,
        "failure_signal": has_failure,
        "response_head": [redact(line) for line in body.strip().splitlines()[-3:][:2]],
        "latency_sec": result["elapsed_sec"],
        "provider": provider,
        "model": model,
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Hermes provider verification")
    ap.add_argument("--check-fallbacks", action="store_true", help="Also run smoke test on fallback providers")
    ap.add_argument("--primary-only", action="store_true", help="Only verify primary provider (skip fallbacks even if requested)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    # Gather metadata
    status = run(["hermes", "status"])
    fallback = run(["hermes", "fallback", "list"])
    config = run(["bash", "-lc", "hermes config show 2>/dev/null | grep -E \"Provider|Model|provider|model\" || true"])
    auth = run(["bash", "-lc", "hermes auth list 2>/dev/null | sed -E 's/(token|secret|key).*/[REDACTED]/Ig' || true"])

    # Parse primary from fallback list (it's the most reliable source)
    fb_stdout = fallback.get("stdout", "")
    primary = parse_primary_provider(fb_stdout)
    provider_name = primary.get("provider") or "primary"
    model_name = primary.get("model") or "unknown"

    # Fallback chain entries
    fallbacks = parse_fallbacks(fb_stdout)

    # Config signals
    cfg_signals = parse_config_provider(config.get("stdout", ""))
    if not primary["provider"]:
        primary["provider"] = cfg_signals.get("provider")
    if not primary["model"]:
        primary["model"] = cfg_signals.get("model")

    # Build verification report
    verifications = []

    # Primary smoke
    primary_smoke = smoke_test(primary.get("provider"), primary.get("model"))
    verifications.append({
        "role": "primary",
        "provider": primary.get("provider") or "unknown",
        "model": primary.get("model") or "unknown",
        **primary_smoke,
    })

    if args.check_fallbacks and not args.primary_only:
        for fb in fallbacks:
            fb_smoke = smoke_test(fb["provider"], fb["model"])
            verifications.append({
                "role": "fallback",
                "rank": fb["rank"],
                "provider": fb["provider"],
                "model": fb["model"],
                **fb_smoke,
            })

    overall_ok = all(v.get("ok") for v in verifications)

    data = {
        "generated_at_utc": ts,
        "redacted": True,
        "overall_health": "healthy" if overall_ok else "degraded",
        "active_provider": primary.get("provider") or "unknown",
        "active_model": primary.get("model") or "unknown",
        "verifications": verifications,
        "fallback_chain": fallbacks,
        "commands": {
            "hermes_status": status,
            "hermes_fallback_list": fallback,
            "hermes_config_signals": config,
            "hermes_auth_list": auth,
        },
    }

    # Write JSON report
    json_path = OUT_DIR / f"{ts}.hermes-verification.json"
    latest_json = OUT_DIR / "latest-hermes-verification.json"
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    json_path.write_text(json_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")

    # Write Markdown report
    lines = [
        "# Hermes Provider Verification Report",
        "",
        f"Generated UTC: `{ts}`",
        "",
        "This report is redacted and does not intentionally print tokens, API keys, bearer values, or credential files.",
        "",
        "## Summary",
        "",
        f"- **Active provider**: `{data['active_provider']}`",
        f"- **Active model**: `{data['active_model']}`",
        f"- **Overall health**: `{data['overall_health']}`",
        "",
        "## Verifications",
        "",
    ]
    for v in verifications:
        role = v.get("role", "primary")
        rank = v.get("rank")
        label = f"{role} (rank {rank})" if rank is not None else role
        ok = "✅ ok" if v.get("ok") else "❌ fail"
        lines.append(f"- **{label}** `{v.get('provider')}` / `{v.get('model')}` → {ok} latency={v.get('latency_sec')}s")
        if not v.get("ok"):
            lines.append(f"  - failure_signal={v.get('failure_signal')}, pong_found={v.get('pong_found')}")
            if v.get("error"):
                lines.append(f"  - error: {v.get('error')}")
    lines += ["", "## Fallback Chain", ""]
    if fallbacks:
        for fb in fallbacks:
            lines.append(f"- {fb['rank']}. `{fb['model']}` via `{fb['provider']}`")
    else:
        lines.append("- None configured.")
    lines += ["", "## Config Signals", "", "```text", config.get("stdout", "") or "N/A", "```", "", "## Auth Name Signals", "", "```text", auth.get("stdout", "") or "N/A", "```", ""]

    md_path = OUT_DIR / f"{ts}.hermes-verification.md"
    latest_md = OUT_DIR / "latest-hermes-verification.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    print(json_path)
    return 0 if overall_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
