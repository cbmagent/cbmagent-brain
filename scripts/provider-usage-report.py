#!/usr/bin/env python3
"""Generate a redacted provider usage/health report.

This script uses local CLI/status/log signals only. It must not print secrets.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

OUT_DIR = Path('reports/provider-usage')
SECRET_PATTERNS = [
    re.compile(r'gho_[A-Za-z0-9_]+'),
    re.compile(r'ghp_[A-Za-z0-9_]+'),
    re.compile(r'github_pat_[A-Za-z0-9_]+'),
    re.compile(r'(Bearer\s+)[A-Za-z0-9._\-]+', re.I),
    re.compile(r'([A-Za-z0-9_]*token[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+', re.I),
    re.compile(r'([A-Za-z0-9_]*secret[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+', re.I),
    re.compile(r'([A-Za-z0-9_]*key[A-Za-z0-9_]*\s*[:=]\s*)[^\s,}\]]+', re.I),
]

def redact(s: str) -> str:
    out = s
    for pat in SECRET_PATTERNS:
        out = pat.sub(lambda m: (m.group(1) if m.groups() else '') + '[REDACTED]', out)
    return out

def run(cmd: list[str], timeout=15) -> dict:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {'ok': p.returncode == 0, 'exit_code': p.returncode, 'stdout': redact(p.stdout[-4000:]), 'stderr': redact(p.stderr[-4000:])}
    except Exception as e:
        return {'ok': False, 'error': type(e).__name__ + ': ' + str(e)}

def http(url: str, timeout=5) -> dict:
    try:
        req = Request(url, headers={'User-Agent': 'cbmagent-provider-report/0.1'})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(1000).decode('utf-8', 'ignore')
            return {'ok': True, 'status': resp.status, 'body_head': redact(body[:500])}
    except Exception as e:
        return {'ok': False, 'error': type(e).__name__ + ': ' + str(e)}

def grep_log(path: Path, terms: list[str], max_lines=20) -> list[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(errors='ignore').splitlines()[-5000:]
    except Exception:
        return []
    hits=[]
    low_terms=[t.lower() for t in terms]
    for line in lines:
        lo=line.lower()
        if any(t in lo for t in low_terms):
            hits.append(redact(line)[-500:])
    return hits[-max_lines:]

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    data = {
        'generated_at_utc': ts,
        'redacted': True,
        'commands': {},
        'services': {},
        'signals': {},
        'notes': []
    }
    data['commands']['hermes_status'] = run(['hermes', 'status'], timeout=20)
    data['commands']['hermes_config_provider_model'] = run(['bash','-lc','hermes config show 2>/dev/null | grep -E "Provider|Model|provider|model" || true'], timeout=20)
    data['commands']['hermes_auth_list_names_only'] = run(['bash','-lc','hermes auth list 2>/dev/null | sed -E "s/(token|secret|key).*/[REDACTED]/Ig" || true'], timeout=20)
    data['commands']['gh_auth_status'] = run(['gh','auth','status'], timeout=20)
    data['commands']['recent_brain_actions_runs'] = run(['gh','run','list','--repo','cbmagent/cbmagent-brain','--limit','10'], timeout=20)
    data['services']['openclaw_gateway_root'] = http('http://127.0.0.1:18789/', timeout=5)
    data['services']['openclaw_models'] = http('http://127.0.0.1:18789/v1/models', timeout=5)
    log_terms = ['rate limit','ratelimit','quota','cooldown','429','exhausted','unavailable','provider','error']
    data['signals']['hermes_agent_log'] = grep_log(Path.home()/'.hermes/logs/agent.log', log_terms)
    data['signals']['hermes_gateway_log'] = grep_log(Path.home()/'.hermes/logs/gateway.log', log_terms)
    data['notes'].append('OpenAI Codex OAuth/ChatGPT subscription quota is opaque from CLI; report observed failures/cooldowns rather than claiming exact remaining quota.')
    data['notes'].append('Provider routing recommendations should prefer read-only/local/GitHub Actions tasks when premium model quota appears constrained.')
    json_path = OUT_DIR / f'{ts}.json'
    md_path = OUT_DIR / f'{ts}.md'
    latest_json = OUT_DIR / 'latest.json'
    latest_md = OUT_DIR / 'latest.md'
    json_text = json.dumps(data, indent=2, sort_keys=True) + '\n'
    json_path.write_text(json_text, encoding='utf-8')
    latest_json.write_text(json_text, encoding='utf-8')
    lines = [
        '# Provider Usage and Health Report', '',
        f'Generated UTC: `{ts}`', '',
        'This report is redacted. It does not intentionally print tokens, API keys, bearer values, or credential files.', '',
        '## Summary', ''
    ]
    hs = data['commands']['hermes_status']
    lines.append(f"- Hermes status command: `{'ok' if hs.get('ok') else 'not ok'}`")
    oc = data['services']['openclaw_gateway_root']
    lines.append(f"- OpenClaw gateway root: `{'ok' if oc.get('ok') else 'not ok'}` {oc.get('status','')}")
    gh = data['commands']['gh_auth_status']
    lines.append(f"- GitHub CLI auth: `{'ok' if gh.get('ok') else 'not ok'}`")
    lines += ['', '## Current Config Signals', '', '```text', data['commands']['hermes_config_provider_model'].get('stdout','') or data['commands']['hermes_config_provider_model'].get('stderr',''), '```', '', '## Auth/Provider Names', '', '```text', data['commands']['hermes_auth_list_names_only'].get('stdout','') or data['commands']['hermes_auth_list_names_only'].get('stderr',''), '```', '', '## Recent GitHub Actions', '', '```text', data['commands']['recent_brain_actions_runs'].get('stdout','') or 'No runs found or command unavailable.', '```', '', '## Recent Rate Limit / Cooldown Signals', '']
    for log_name, hits in data['signals'].items():
        lines += [f'### {log_name}', '']
        if not hits:
            lines.append('- No recent matching signals found.')
        else:
            for h in hits[-10:]:
                lines.append(f'- `{h}`')
        lines.append('')
    lines += ['## Recommendations', '', '- Treat OpenAI Codex OAuth quota as opaque; monitor observed rate-limit/cooldown errors.', '- Use Nous/OpenClaw/local tools as fallback/specialists when primary provider signals failures.', '- Keep deterministic audits in scripts/GitHub Actions so premium model quota is reserved for reasoning/coding.', '- Add scheduled provider report workflow after read-only environment design is finalized.', '']
    md = '\n'.join(lines)
    md_path.write_text(md, encoding='utf-8')
    latest_md.write_text(md, encoding='utf-8')
    print(md_path)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
