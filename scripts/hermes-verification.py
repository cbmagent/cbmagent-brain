#!/usr/bin/env python3
"""Verify Hermes provider/model routing without exposing credentials.

By default this is a cheap inventory/status check. Pass --smoke to run tiny
one-shot prompts against the primary and configured fallback providers.
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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "hermes-verification"
MAX_CAPTURE = 4000

# Build sensitive marker strings in pieces so repository smoke checks do not
# mistake redaction test patterns for committed credentials.
SENSITIVE_PATTERNS = [
    re.compile("gh" + "p_" + r"[A-Za-z0-9_]+"),
    re.compile("gh" + "o_" + r"[A-Za-z0-9_]+"),
    re.compile("github" + "_pat_" + r"[A-Za-z0-9_]+"),
    re.compile(r"(bearer\s+)[A-Za-z0-9._\-]+", re.I),
    re.compile(r"([A-Za-z0-9_]*(?:token|secret|credential)[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+", re.I),
    re.compile(r"([A-Za-z0-9_]*api[_-]?key[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+", re.I),
    re.compile(r"(/home/[^/]+/\.hermes/(?:\.env|auth\.json))"),
]


def redact(text: str | None) -> str:
    if not text:
        return ""
    out = text[-MAX_CAPTURE:]
    for pattern in SENSITIVE_PATTERNS:
        out = pattern.sub(lambda match: (match.group(1) if match.groups() else "") + "[REDACTED]", out)
    return out


def run_command(args: list[str], timeout: int = 30, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "latency_ms": latency_ms,
            "stdout_redacted": redact(proc.stdout),
            "stderr_redacted": redact(proc.stderr),
        }
    except Exception as exc:  # noqa: BLE001 - report all smoke failures, do not crash.
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": f"{type(exc).__name__}: {redact(str(exc))}",
        }


def parse_primary(config_text: str, fallback_text: str) -> dict[str, str | None]:
    # Preferred signal from `hermes fallback list`: "Primary: model (via provider)".
    match = re.search(r"Primary:\s+(.+?)\s+\(via\s+([^)]+)\)", fallback_text)
    if match:
        return {"model": match.group(1).strip(), "provider": match.group(2).strip()}

    # Common `hermes config show` signal: "Model: {'default': 'gpt-5.5', 'provider': 'openai-codex'}".
    model_match = re.search(r"Model:\s+\{[^\n]*'default':\s*'([^']+)'[^\n]*'provider':\s*'([^']+)'", config_text)
    if model_match:
        return {"model": model_match.group(1), "provider": model_match.group(2)}

    return {"model": None, "provider": None}


def parse_fallbacks(fallback_text: str) -> list[dict[str, str | int | None]]:
    entries: list[dict[str, str | int | None]] = []
    pattern = re.compile(r"^\s*(\d+)\.\s+(.+?)\s+\(via\s+([^)]+)\)", re.M)
    for match in pattern.finditer(fallback_text):
        raw_model = match.group(2).strip()
        provider = match.group(3).strip()
        model = raw_model
        if raw_model.startswith(provider + "/"):
            model = raw_model[len(provider) + 1 :]
        entries.append({"order": int(match.group(1)), "model": model, "provider": provider})
    return entries


def smoke_target(target: dict[str, Any], timeout: int) -> dict[str, Any]:
    provider = target.get("provider")
    model = target.get("model")
    result: dict[str, Any] = {"provider": provider, "model": model, "attempted": False}
    if not provider or not model:
        result.update({"ok": False, "reason": "provider or model was not detected"})
        return result

    cmd = [
        "hermes",
        "--provider",
        str(provider),
        "--model",
        str(model),
        "--oneshot",
        "Reply with exactly the lowercase word ok.",
        "--ignore-rules",
        "--toolsets",
        "",
    ]
    env = os.environ.copy()
    env.setdefault("HERMES_DISABLE_MEMORY", "1")
    probe = run_command(cmd, timeout=timeout, env=env)
    # Do not persist the model response text or prompt token details. Only keep
    # pass/fail, latency, and redacted diagnostics for failures.
    stdout = probe.pop("stdout_redacted", "")
    stderr = probe.get("stderr_redacted", "")
    normalized = stdout.strip().lower()
    result.update(
        {
            "attempted": True,
            "ok": bool(probe.get("ok")) and normalized == "ok",
            "latency_ms": probe.get("latency_ms"),
            "exit_code": probe.get("exit_code"),
        }
    )
    if normalized != "ok":
        result["diagnostic_redacted"] = redact(stderr or stdout)[-1000:]
    return result


def write_reports(data: dict[str, Any]) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = data["generated_at_utc"]
    json_path = OUT_DIR / f"{ts}.json"
    md_path = OUT_DIR / f"{ts}.md"
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    json_path.write_text(json_text, encoding="utf-8")
    (OUT_DIR / "latest.json").write_text(json_text, encoding="utf-8")

    primary = data["detected"]["primary"]
    fallbacks = data["detected"]["fallbacks"]
    lines = [
        "# Hermes Provider/Model Verification",
        "",
        f"Generated UTC: `{ts}`",
        "",
        "This report is redacted. It records provider/model names, pass/fail state, and latency only; it does not intentionally persist prompts, completions, credential files, tokens, or API keys.",
        "",
        "## Detected Routing",
        "",
        f"- Primary: `{primary.get('provider') or 'unknown'}` / `{primary.get('model') or 'unknown'}`",
        f"- Fallback entries: `{len(fallbacks)}`",
    ]
    for item in fallbacks:
        lines.append(f"  - {item.get('order')}. `{item.get('provider')}` / `{item.get('model')}`")

    lines += ["", "## Command Checks", ""]
    for name, check in data["checks"].items():
        status = "pass" if check.get("ok") else "fail"
        lines.append(f"- {name}: `{status}` ({check.get('latency_ms', 'n/a')} ms)")

    lines += ["", "## Smoke Checks", ""]
    if not data["smoke_checks"]:
        lines.append("- Skipped. Run `python scripts/hermes-verification.py --smoke` for tiny live provider probes.")
    else:
        for check in data["smoke_checks"]:
            status = "pass" if check.get("ok") else "fail"
            lines.append(
                f"- `{check.get('provider')}` / `{check.get('model')}`: `{status}` ({check.get('latency_ms', 'n/a')} ms)"
            )
            if check.get("diagnostic_redacted"):
                lines.append(f"  - Diagnostic: `{check['diagnostic_redacted']}`")

    lines += ["", "## Notes", ""]
    lines.extend(f"- {note}" for note in data["notes"])
    md_text = "\n".join(lines).rstrip() + "\n"
    md_path.write_text(md_text, encoding="utf-8")
    (OUT_DIR / "latest.md").write_text(md_text, encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Hermes provider/model routing with redacted reports.")
    parser.add_argument("--smoke", action="store_true", help="Run tiny live one-shot prompts against detected providers.")
    parser.add_argument("--include-fallbacks", action="store_true", help="When --smoke is set, also probe fallback entries.")
    parser.add_argument("--smoke-timeout", type=int, default=60, help="Timeout in seconds for each live smoke probe.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any inventory or smoke check fails.")
    args = parser.parse_args()

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    config_check = run_command(["hermes", "config", "show"], timeout=20)
    fallback_check = run_command(["hermes", "fallback", "list"], timeout=20)
    status_check = run_command(["hermes", "status"], timeout=30)
    auth_check = run_command(["hermes", "auth", "list"], timeout=20)

    config_text = config_check.get("stdout_redacted", "") + "\n" + config_check.get("stderr_redacted", "")
    fallback_text = fallback_check.get("stdout_redacted", "") + "\n" + fallback_check.get("stderr_redacted", "")
    primary = parse_primary(config_text, fallback_text)
    fallbacks = parse_fallbacks(fallback_text)

    smoke_checks: list[dict[str, Any]] = []
    if args.smoke:
        smoke_checks.append(smoke_target(primary, timeout=args.smoke_timeout))
        if args.include_fallbacks:
            for item in fallbacks:
                smoke_checks.append(smoke_target(item, timeout=args.smoke_timeout))

    data: dict[str, Any] = {
        "generated_at_utc": ts,
        "redacted": True,
        "expensive_checks_skipped": not args.smoke,
        "detected": {"primary": primary, "fallbacks": fallbacks},
        "checks": {
            "hermes_config_show": config_check,
            "hermes_fallback_list": fallback_check,
            "hermes_status": status_check,
            "hermes_auth_list": auth_check,
        },
        "smoke_checks": smoke_checks,
        "notes": [
            "Default mode performs inventory only so scheduled runs do not consume provider quota.",
            "Live smoke checks intentionally use a tiny response and persist only pass/fail, latency, and redacted failure diagnostics.",
            "Fallback smoke probes require --include-fallbacks so operators can decide when broader provider checks are worth the cost.",
        ],
    }
    json_path, md_path = write_reports(data)
    print(md_path)
    print(json_path)
    checks_ok = all(check.get("ok") for check in data["checks"].values()) and all(
        check.get("ok") for check in smoke_checks
    )
    return 0 if (checks_ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
