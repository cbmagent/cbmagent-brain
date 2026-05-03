#!/usr/bin/env python3
"""Generate an autonomous progress report for Clarke.

Uses GitHub CLI and local reports only. Does not inspect credential files.
"""
from __future__ import annotations
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO='cbmagent/cbmagent-brain'
OUT=ROOT/'reports'/'progress'

def gh(args):
    p=subprocess.run(['gh']+args, cwd=ROOT, text=True, capture_output=True)
    if p.returncode:
        return None, (p.stderr or p.stdout).strip()
    try:
        return json.loads(p.stdout), None
    except json.JSONDecodeError:
        return p.stdout.strip(), None

def issue_table(issues):
    if not issues: return ['None.']
    lines=[]
    for i in issues:
        labels=', '.join(l['name'] for l in i.get('labels',[]))
        lines.append(f"- #{i['number']} [{i['title']}]({i['url']}) — {labels}")
    return lines

def main():
    ts=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    open_issues,_=gh(['issue','list','--repo',REPO,'--state','open','--limit','200','--json','number,title,url,labels,createdAt,updatedAt'])
    recent_prs,_=gh(['pr','list','--repo',REPO,'--state','all','--limit','15','--json','number,title,url,state,mergedAt,createdAt,headRefName'])
    open_prs,_=gh(['pr','list','--repo',REPO,'--state','open','--limit','50','--json','number,title,url,state,headRefName'])
    open_issues=open_issues or []
    recent_prs=recent_prs or []
    open_prs=open_prs or []
    def has_label(issue,name): return any(l['name']==name for l in issue.get('labels',[]))
    human=[i for i in open_issues if has_label(i,'human-needed')]
    critical=[i for i in open_issues if has_label(i,'priority:critical') and not has_label(i,'human-needed') and not has_label(i,'blocked')]
    high=[i for i in open_issues if has_label(i,'priority:high') and not has_label(i,'human-needed') and not has_label(i,'blocked')]
    next_items=(critical+high)[:10]
    merged=[p for p in recent_prs if p.get('state')=='MERGED'][:10]
    lines=[
      '# Autonomous Progress Report','',f'Generated: `{ts}`','',
      '## Summary','',
      f'- Open issues: {len(open_issues)}',
      f'- Open PRs: {len(open_prs)}',
      f'- Human-needed blockers: {len(human)}',
      f'- Next safe agent tasks listed: {len(next_items)}','',
      '## Open PRs','',
      *([f"- #{p['number']} [{p['title']}]({p['url']}) — `{p['headRefName']}`" for p in open_prs] or ['None.']),
      '', '## Recently Merged PRs','',
      *([f"- #{p['number']} [{p['title']}]({p['url']})" for p in merged] or ['None.']),
      '', '## Next Safe Agent Tasks','',
      *issue_table(next_items),
      '', '## Human Needed','',
      *issue_table(human),
      '', '## Operating Note','',
      'The agent should keep taking `priority:critical`/`priority:high` issues that are not `human-needed` or `blocked`, create branches/PRs, validate, merge when safe, and only text Clarke for external credentials, approvals, production cutovers, or ambiguous decisions.'
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    md='\n'.join(lines).rstrip()+'\n'
    (OUT/f'{ts}.md').write_text(md, encoding='utf-8')
    (OUT/'latest.md').write_text(md, encoding='utf-8')
    data={'generated_at':ts,'open_issue_count':len(open_issues),'open_pr_count':len(open_prs),'human_needed_count':len(human),'next_safe_issues':[i['number'] for i in next_items]}
    (OUT/f'{ts}.json').write_text(json.dumps(data,indent=2)+'\n', encoding='utf-8')
    (OUT/'latest.json').write_text(json.dumps(data,indent=2)+'\n', encoding='utf-8')
    print(OUT/'latest.md')
if __name__=='__main__': main()
