#!/usr/bin/env python3
"""Read-only DNS/HTTP audit for portfolio domains.

No credentials required. Does not mutate DNS, Cloudflare, GitHub, Microsoft, or Google.
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
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

DOMAINS_YAML = Path('portfolio/domains.yaml')
OUT_DIR = Path('portfolio/dns-audit-reports')


def load_domains() -> list[dict]:
    try:
        import yaml  # type: ignore
    except Exception:
        text = DOMAINS_YAML.read_text(encoding='utf-8')
        return [{'domain': m.group(1)} for m in re.finditer(r'^\s*- domain:\s*([^\s]+)', text, re.M)]
    data = yaml.safe_load(DOMAINS_YAML.read_text(encoding='utf-8')) or {}
    return data.get('domains', [])


def dig(domain: str, rtype: str) -> list[str]:
    try:
        p = subprocess.run(['dig', '+short', rtype, domain], text=True, capture_output=True, timeout=10)
        if p.returncode != 0:
            return []
        return [x.strip().rstrip('.') for x in p.stdout.splitlines() if x.strip()]
    except Exception:
        return []


def http_check(domain: str, scheme: str) -> dict:
    url = f'{scheme}://{domain}/'
    req = Request(url, headers={'User-Agent': 'cbmagent-brain-readonly-audit/0.1'})
    try:
        ctx = ssl.create_default_context()
        with urlopen(req, timeout=12, context=ctx) as resp:
            body = resp.read(200000).decode('utf-8', 'ignore')
            final_url = resp.geturl()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            signals = []
            hay = (body[:50000] + '\n' + '\n'.join(f'{k}: {v}' for k, v in headers.items())).lower()
            if 'wp-content' in hay or 'wp-includes' in hay or 'wordpress' in hay:
                signals.append('wordpress')
            if 'github.io' in hay or 'github pages' in hay:
                signals.append('github-pages')
            if 'cloudflare' in headers.get('server', '').lower() or headers.get('cf-ray'):
                signals.append('cloudflare')
            return {'ok': True, 'status': resp.status, 'final_url': final_url, 'server': headers.get('server', ''), 'signals': sorted(set(signals))}
    except HTTPError as e:
        return {'ok': False, 'status': e.code, 'error': str(e), 'final_url': url, 'signals': []}
    except Exception as e:
        return {'ok': False, 'status': None, 'error': type(e).__name__ + ': ' + str(e), 'final_url': url, 'signals': []}


def classify(domain: str, rec: dict, meta: dict) -> str:
    if meta.get('role') == 'redirect-only':
        return 'redirect-only-candidate'
    signals = set(rec.get('https', {}).get('signals') or []) | set(rec.get('http', {}).get('signals') or [])
    c = ' '.join(rec.get('cname', []) + rec.get('www_cname', [])).lower()
    ips = set(rec.get('a', []))
    gh_ips = {'185.199.108.153', '185.199.109.153', '185.199.110.153', '185.199.111.153'}
    if 'wordpress' in signals:
        return 'wordpress-detected'
    if 'github-pages' in signals or 'github.io' in c or ips.intersection(gh_ips):
        return 'github-pages-detected'
    if rec.get('https', {}).get('ok') or rec.get('http', {}).get('ok'):
        return 'live-other-or-unknown'
    if not rec.get('a') and not rec.get('aaaa') and not rec.get('cname'):
        return 'no-apex-records-detected'
    return 'dns-present-http-issue'


def audit_one(meta: dict) -> dict:
    d = meta['domain']
    rec = {
        'domain': d,
        'role': meta.get('role'),
        'canonical_target': meta.get('canonical_target'),
        'target_hosting': meta.get('target_hosting'),
        'repo': meta.get('repo'),
        'ns': dig(d, 'NS'),
        'a': dig(d, 'A'),
        'aaaa': dig(d, 'AAAA'),
        'cname': dig(d, 'CNAME'),
        'www_cname': dig('www.' + d, 'CNAME'),
        'www_a': dig('www.' + d, 'A'),
        'https': http_check(d, 'https'),
        'http': http_check(d, 'http'),
    }
    rec['classification'] = classify(d, rec, meta)
    return rec


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    domains = load_domains()
    ts = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(audit_one, domains))
    rows.sort(key=lambda r: r['domain'])
    json_path = OUT_DIR / f'{ts}.json'
    md_path = OUT_DIR / f'{ts}.md'
    latest_json = OUT_DIR / 'latest.json'
    latest_md = OUT_DIR / 'latest.md'
    payload = {'generated_at_utc': ts, 'read_only': True, 'domains': rows}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    latest_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    lines = [f'# Read-Only Domain Audit', '', f'Generated UTC: `{ts}`', '', 'This audit used public DNS and HTTP(S) checks only. It did not mutate any provider state.', '', '## Summary', '']
    for r in rows:
        lines.append(f"- **{r['domain']}**: `{r['classification']}`; HTTPS `{r['https'].get('status')}` → `{r['https'].get('final_url')}`")
    lines += ['', '## Details', '']
    for r in rows:
        lines += [f"### {r['domain']}", '', f"- Role: `{r.get('role')}`", f"- Target hosting: `{r.get('target_hosting')}`", f"- Repo: `{r.get('repo')}`", f"- Classification: `{r['classification']}`", f"- NS: `{', '.join(r['ns']) or 'none'}`", f"- A: `{', '.join(r['a']) or 'none'}`", f"- AAAA: `{', '.join(r['aaaa']) or 'none'}`", f"- CNAME apex: `{', '.join(r['cname']) or 'none'}`", f"- www CNAME: `{', '.join(r['www_cname']) or 'none'}`", f"- HTTPS: `{r['https'].get('status')}` `{r['https'].get('final_url')}` `{r['https'].get('error','')}`", f"- HTTP: `{r['http'].get('status')}` `{r['http'].get('final_url')}` `{r['http'].get('error','')}`", '']
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    latest_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(md_path)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
