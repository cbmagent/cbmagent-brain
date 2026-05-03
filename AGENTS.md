# Agent Instructions for cbmagent-brain

This repository is the provider-neutral brain for cbmagent operations. Hermes Agent is the current runtime, but the repo should remain usable by future agents such as OpenClaw or other backends.

## Operating Principles

1. Be transparent about which agents/providers are in use.
2. Keep this repo provider-neutral where possible.
3. Do not duplicate project-specific GitHub Issues here.
4. Link to project issues/PRs/actions instead of replacing them.
5. Preserve the strict GitHub workflow: issue → branch → PR → review/checks → merge.
6. Prefer read-only autonomous discovery and reporting.
7. Keep production writes gated through GitHub Actions environments and required reviewers.
8. Never commit secrets, tokens, auth files, API keys, or bearer tokens.
9. Credit source repos when deriving templates, workflows, docs, or patterns.
10. Send reusable improvements back upstream to Free For Charity repos when appropriate.

## Current Runtime Context

- Current active agent: Hermes Agent
- Current primary backend/model: OpenAI Codex OAuth / GPT-5.5
- Specialist/fallback agents/providers may include: Nous, OpenClaw, GitHub Copilot, local tools

## Repo Role

This repo owns portfolio-level standards, registry, reporting, and runbooks. Project repos own project-specific tasks, code, issues, PRs, Actions, Pages, and Wikis.

## Safety Boundary

Agents may autonomously run/read:

- DNS audits
- GitHub repo/issue/PR status checks
- GitHub Pages readiness checks
- link checks
- Lighthouse/a11y checks
- Microsoft/Google read-only status checks where configured
- report generation

Agents should not directly perform production writes. Production mutations should be prepared as issues/PRs/workflow dispatches and executed through protected GitHub Actions environments.
