# cbmagent-brain

Provider-neutral operating brain for cbmagent agents, portfolio governance, reusable workflows, and AI-assisted project operations.

This repository is intentionally **not named after a single agent backend**. Hermes Agent is the current runtime operating this brain, but the brain is designed to survive backend changes and coordinate work across Hermes, OpenClaw, GitHub Copilot, local VS Code workflows, and future agents.

## Current Agent Stack

- **Current primary runtime:** Hermes Agent
- **Current primary model/backend:** OpenAI Codex OAuth / GPT-5.5
- **Fallback/specialist providers:** Nous, OpenClaw, GitHub Copilot, local tools where appropriate
- **Project-management boundary:** GitHub Issues, branches, PRs, Actions, Projects, Wikis, and Pages remain the source of truth for project-specific work

The repo is open about the agents it coordinates. It should not hide that Hermes is currently running it, but it should also avoid becoming Hermes-specific when a more general agent-brain standard is better.

## Purpose

`cbmagent-brain` owns portfolio-level coordination:

- Agent operating doctrine
- Provider/model routing notes
- Domain/site portfolio inventory
- GitHub operating standards
- Read-only vs write-gated environment design
- Nonprofit giveback and attribution policy
- Reusable issue/PR/workflow templates
- Cross-repo reporting and dashboards
- VS Code operator workspace design
- Links to project-specific GitHub issues and PRs

It does **not** replace repo-local GitHub project management.

## Core Rule

For code/content/infrastructure changes in a project repo:

```text
Issue → branch → PR → checks/actions → Copilot/review → merge → update portfolio status
```

This brain can summarize, link, and orchestrate. The actual work items live in the relevant project repos.

## Foundational Reference Repos

This brain intentionally credits and learns from foundational Free For Charity and Clarke projects:

- [FreeForCharity/FFC-Cloudflare-Automation](https://github.com/FreeForCharity/FFC-Cloudflare-Automation)
- [FreeForCharity/FFC-IN-FFC_Single_Page_Template](https://github.com/FreeForCharity/FFC-IN-FFC_Single_Page_Template)
- [FreeForCharity/FFC-IN-Footer_Only_Template](https://github.com/FreeForCharity/FFC-IN-Footer_Only_Template)
- [clarkemoyer/technologyadoptionbarriers.org](https://github.com/clarkemoyer/technologyadoptionbarriers.org)

A goal of this work is to give reusable improvements back to nonprofit infrastructure.

## Initial Structure

```text
docs/         Operating model and design notes
portfolio/    Domains, repos, migrations, status reports
references/   Source repo lineage and attribution notes
runbooks/     Repeatable procedures
standards/    Templates, labels, PR/issue standards
workspaces/   VS Code/operator workspace assets
```

## Bootstrap Note

This initial repository bootstrap may be committed directly to `main` because the repo did not exist yet. Future changes should follow the issue → branch → PR workflow.
