# Template Alignment Tracker

This tracker connects cbmagent portfolio work, Free For Charity source templates, and the advanced TABS reference implementation.

## Source Repos

| Repo | Role | Giveback Direction |
| --- | --- | --- |
| FreeForCharity/FFC-IN-FFC_Single_Page_Template | Default full Next.js nonprofit site template | Backport reusable site/template improvements |
| FreeForCharity/FFC-IN-Footer_Only_Template | Footer/legal/cookie/analytics/team layer | Backport compliance/footer/policy improvements |
| FreeForCharity/FFC-Cloudflare-Automation | Operations and domain automation reference | Backport workflow/environment/issue-form improvements |
| clarkemoyer/technologyadoptionbarriers.org | Advanced automation/API/reference site | Extract generalized patterns into FFC templates where useful |

## Initial Candidate Improvements

### Read-only vs write-gated environments

- Candidate source: cbmagent-brain environment rollout docs
- Likely upstream: FreeForCharity/FFC-Cloudflare-Automation
- Value: Lets agents run DNS/M365/Google audits autonomously while keeping production writes protected.
- Proposed action: open upstream issue after first implementation in cbmagent-brain is stable.

### Provider usage/agent health reporting

- Candidate source: cbmagent-brain provider usage script
- Likely upstream: FreeForCharity/FFC-Cloudflare-Automation and/or TABS docs
- Value: Helps nonprofit automation avoid silent stalls and identify provider/cooldown issues.
- Proposed action: document as optional agent-ops pattern first.

### GitHub Pages/domain portfolio issue forms

- Candidate source: cbmagent-brain issue forms
- Likely upstream: FreeForCharity/FFC-Cloudflare-Automation
- Value: Standardizes domain intake, redirect-only aliases, and GitHub Pages readiness checks.
- Proposed action: compare with existing FFC issue forms and propose a compatible update.

### TABS advanced workflow extraction

- Candidate source: technologyadoptionbarriers.org workflows
- Likely upstream: FFC Single Page and Footer Only templates when generally useful
- Value: API smoke tests, post-deploy smoke checks, SEO reporting, Copilot review cycles, and daily pipelines may help nonprofit sites.
- Proposed action: triage each TABS workflow as reusable, TABS-specific, or documentation-only.

## Status Legend

- `candidate`: reusable idea identified
- `triaged`: target upstream repo selected
- `issue-opened`: upstream issue exists
- `pr-opened`: upstream PR exists
- `merged`: upstream contribution merged
- `not-reusable`: reviewed and intentionally not upstreamed
