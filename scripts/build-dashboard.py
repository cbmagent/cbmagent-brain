#!/usr/bin/env python3
"""Build static GitHub Pages dashboard for cbmagent-brain.

No credentials are read. Uses repo artifacts that are safe to publish to this private-repo Pages site.
"""
from __future__ import annotations
import html, json, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

def read(path: str, default: str = "") -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else default

def read_json(path: str, default):
    try:
        return json.loads(read(path, ""))
    except Exception:
        return default

def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))

def md_to_html(md: str) -> str:
    # Minimal safe markdown renderer for repo-generated reports.
    lines = []
    in_list = False
    in_code = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if not in_code:
                lines.append("<pre><code>"); in_code = True
            else:
                lines.append("</code></pre>"); in_code = False
            continue
        if in_code:
            lines.append(esc(line)); continue
        if not line:
            if in_list:
                lines.append("</ul>"); in_list = False
            continue
        if line.startswith("# "):
            if in_list: lines.append("</ul>"); in_list = False
            lines.append(f"<h1>{esc(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list: lines.append("</ul>"); in_list = False
            lines.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list: lines.append("</ul>"); in_list = False
            lines.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>"); in_list = True
            content = esc(line[2:])
            content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', content)
            content = re.sub(r"`([^`]+)`", r'<code>\1</code>', content)
            lines.append(f"<li>{content}</li>")
        else:
            if in_list: lines.append("</ul>"); in_list = False
            content = esc(line)
            content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', content)
            content = re.sub(r"`([^`]+)`", r'<code>\1</code>', content)
            lines.append(f"<p>{content}</p>")
    if in_list: lines.append("</ul>")
    if in_code: lines.append("</code></pre>")
    return "\n".join(lines)

provider = read_json("reports/provider-usage/latest.json", {})
progress = read_json("reports/progress/latest.json", {})
repo_inv = read_json("reports/repo-inventory/latest.json", {})
dns = read_json("portfolio/dns-audit-reports/latest.json", {})
progress_md = read("reports/progress/latest.md", "Progress report not generated yet.")
repo_md = read("reports/repo-inventory/latest.md", "Repository inventory not generated yet.")
dns_md = read("portfolio/dns-audit-reports/latest.md", "Domain audit not generated yet.")
provider_md = read("reports/provider-usage/latest.md", "Provider usage report not generated yet.")

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
open_issues = progress.get("open_issue_count", "unknown")
open_prs = progress.get("open_pr_count", "unknown")
human_needed = progress.get("human_needed_count", "unknown")
repo_count = repo_inv.get("repo_count", "unknown")
domain_count = repo_inv.get("domain_count", len(dns.get("domains", [])) or "unknown")
provider_name = provider.get("hermes", {}).get("provider") or provider.get("current_provider") or "openai-codex"
model_name = provider.get("hermes", {}).get("model") or provider.get("current_model") or "gpt-5.5"

html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>cbmagent AI Operations Dashboard</title>
  <style>
    :root {{ color-scheme: dark; --bg:#08111f; --panel:#101d33; --panel2:#132642; --text:#e6edf7; --muted:#9fb2ce; --accent:#6ee7f9; --green:#8ef6b2; --yellow:#ffd166; --red:#ff7b7b; --line:#26415f; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: radial-gradient(circle at top left, #12365c, var(--bg) 45%); color:var(--text); }}
    header {{ padding:48px 24px 28px; max-width:1200px; margin:auto; }}
    h1 {{ font-size: clamp(2rem, 5vw, 4.6rem); line-height:1; margin:0 0 16px; letter-spacing:-.06em; }}
    h2 {{ margin:0 0 14px; font-size:1.5rem; }}
    h3 {{ margin:18px 0 8px; color:var(--accent); }}
    p, li {{ color:var(--muted); line-height:1.55; }}
    a {{ color:var(--accent); }}
    code {{ background:#07101d; border:1px solid var(--line); border-radius:6px; padding:1px 5px; color:var(--green); }}
    .subtitle {{ font-size:1.2rem; max-width:880px; color:#c8d6eb; }}
    main {{ max-width:1200px; margin:auto; padding:0 24px 64px; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap:16px; margin:24px 0; }}
    .card {{ background:rgba(16,29,51,.86); border:1px solid var(--line); border-radius:18px; padding:20px; box-shadow: 0 12px 40px rgba(0,0,0,.25); }}
    .metric {{ font-size:2.4rem; font-weight:800; color:var(--green); letter-spacing:-.05em; }}
    .label {{ color:var(--muted); font-size:.92rem; }}
    .section {{ background:rgba(16,29,51,.74); border:1px solid var(--line); border-radius:22px; padding:24px; margin:20px 0; }}
    .tiers {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr)); gap:16px; }}
    .tier {{ background:var(--panel2); border:1px solid var(--line); border-radius:18px; padding:18px; }}
    .tier strong {{ color:#fff; }}
    .badge {{ display:inline-block; padding:4px 9px; border:1px solid var(--line); border-radius:999px; color:var(--accent); background:#07101d; font-size:.8rem; margin-bottom:8px; }}
    .reports {{ display:grid; grid-template-columns: 1fr; gap:16px; }}
    details {{ background:#07101d; border:1px solid var(--line); border-radius:14px; padding:14px 18px; }}
    summary {{ cursor:pointer; font-weight:700; color:var(--accent); }}
    footer {{ border-top:1px solid var(--line); padding:24px; color:var(--muted); text-align:center; }}
  </style>
</head>
<body>
  <header>
    <div class="badge">cbmagent-brain • provider-neutral AI control tower</div>
    <h1>AI Operations Dashboard</h1>
    <p class="subtitle">A live static dashboard for remembering how this repository works, what the autonomous agent is doing, and how each AI tier/provider should be used.</p>
    <p>Generated {esc(now)} from repository artifacts. No credentials or secret files are read.</p>
  </header>
  <main>
    <section class="grid" aria-label="status metrics">
      <div class="card"><div class="metric">{esc(open_issues)}</div><div class="label">Open GitHub issues</div></div>
      <div class="card"><div class="metric">{esc(open_prs)}</div><div class="label">Open pull requests</div></div>
      <div class="card"><div class="metric">{esc(human_needed)}</div><div class="label">Human-needed blockers</div></div>
      <div class="card"><div class="metric">{esc(domain_count)}</div><div class="label">Tracked domains</div></div>
      <div class="card"><div class="metric">{esc(repo_count)}</div><div class="label">Accessible repos inventoried</div></div>
      <div class="card"><div class="metric">{esc(model_name)}</div><div class="label">Primary model target</div></div>
    </section>

    <section class="section">
      <h2>How we intend to use the AI tiers</h2>
      <div class="tiers">
        <div class="tier"><span class="badge">Primary agent engine</span><h3>OpenAI Codex OAuth / GPT-5.5</h3><p><strong>Use for:</strong> main Hermes coding, planning, repo operations, PR creation, scripts, site migrations, and autonomous issue execution.</p><p><strong>Why:</strong> Clarke has approved this as the primary backend via supported OAuth path.</p></div>
        <div class="tier"><span class="badge">Fallback / background</span><h3>Nous</h3><p><strong>Use for:</strong> ToS-safe fallback inference, background work, and provider resilience when OpenAI/Codex is degraded or quota-constrained.</p><p><strong>Why:</strong> Keeps the system provider-neutral and avoids tying the brain to one backend.</p></div>
        <div class="tier"><span class="badge">GitHub-native specialist</span><h3>OpenClaw + GitHub Copilot</h3><p><strong>Use for:</strong> GitHub PR review, IDE assistance, Copilot-native review loops, and specialist fallback for GitHub workflows.</p><p><strong>Watch:</strong> cooldown/rate-limit lockouts should be reported and routed around.</p></div>
        <div class="tier"><span class="badge">Automation cockpit</span><h3>GitHub Actions</h3><p><strong>Use for:</strong> repeatable audits, deployments, validation, GitHub Pages publishing, and environment-gated infrastructure changes.</p><p><strong>Rule:</strong> read-only automation can run freely; production writes require protected environments and approvals.</p></div>
        <div class="tier"><span class="badge">Human/UI only unless safe API exists</span><h3>Consumer Claude/Gemini/M365 Copilot</h3><p><strong>Use for:</strong> human-interactive thinking and manual workflows.</p><p><strong>Do not use for:</strong> bot backends unless a supported programmatic API/OAuth path is confirmed.</p></div>
        <div class="tier"><span class="badge">Local/private utility</span><h3>Ollama / local tools</h3><p><strong>Use for:</strong> cheap/private preprocessing, simple transformations, and future local fallback where quality is sufficient.</p></div>
      </div>
    </section>

    <section class="section">
      <h2>Repository operating model</h2>
      <p><strong>cbmagent-brain</strong> is the control tower: standards, portfolio inventory, runbooks, dashboards, reports, provider health, and cross-repo links. It should not swallow project-specific management.</p>
      <p>Each site repo owns its own issues, PRs, Actions, GitHub Pages deployment, environments, branch protections, and cutover history. Standard work remains: issue → branch → PR → validation/review → merge → update status.</p>
    </section>

    <section class="section reports">
      <h2>Live repository reports</h2>
      <details open><summary>Progress report</summary>{md_to_html(progress_md)}</details>
      <details><summary>Provider usage / health report</summary>{md_to_html(provider_md)}</details>
      <details><summary>Repository inventory</summary>{md_to_html(repo_md)}</details>
      <details><summary>Domain DNS/HTTP audit</summary>{md_to_html(dns_md)}</details>
    </section>

    <section class="section">
      <h2>Key links</h2>
      <ul>
        <li><a href="https://github.com/cbmagent/cbmagent-brain">GitHub repository</a></li>
        <li><a href="https://github.com/cbmagent/cbmagent-brain/issues">Issue backlog</a></li>
        <li><a href="https://github.com/cbmagent/cbmagent-brain/pulls">Pull requests</a></li>
        <li><a href="https://github.com/cbmagent/cbmagent-brain/actions">GitHub Actions</a></li>
      </ul>
    </section>
  </main>
  <footer>Built from cbmagent-brain. Provider-neutral, secret-safe, GitHub-native.</footer>
</body>
</html>
"""
SITE.mkdir(parents=True, exist_ok=True)
(SITE / "index.html").write_text(html_doc, encoding="utf-8")
print(SITE / "index.html")
