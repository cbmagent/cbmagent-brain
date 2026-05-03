#!/usr/bin/env python3
import json, subprocess, sys
repo='cbmagent/cbmagent-brain'
raw=subprocess.check_output(['gh','issue','list','--repo',repo,'--state','open','--limit','200','--json','number,title,labels,url'], text=True)
issues=json.loads(raw)
priority_rank={'priority:critical':0,'priority:high':1,'priority:medium':2,'priority:low':3}
def score(issue):
    labels={l['name'] for l in issue.get('labels',[])}
    if 'human-needed' in labels or 'blocked' in labels:
        penalty=100
    else:
        penalty=0
    pr=min([priority_rank.get(l,9) for l in labels] or [9])
    readonly=0 if 'readonly' in labels else 1
    epic=1 if 'epic' in labels else 0
    return (penalty, pr, readonly, epic, issue['number'])
issues.sort(key=score)
if not issues:
    print('No open issues.')
    sys.exit(0)
for i in issues[:10]:
    labels=', '.join(l['name'] for l in i.get('labels',[]))
    print(f"#{i['number']}: {i['title']} [{labels}] {i['url']}")
