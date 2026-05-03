# GitHub Operating Model

## Boundary

`cbmagent-brain` is a control tower, not a replacement for GitHub-native project management.

## Project Repos Own

- Issues
- Branches
- Pull requests
- Actions
- Pages
- Wiki/docs
- Project-specific milestones
- Deployment settings
- Repo-specific secrets/environments

## Brain Repo Owns

- Portfolio inventory
- Cross-repo reporting
- Standards/templates
- Runbooks
- Provider/agent routing notes
- VS Code operator workspace
- Attribution and upstream giveback tracking

## Required Work Loop

```text
Issue → branch → PR → checks/actions → Copilot/review → merge → update portfolio status
```

## Initial Repo Bootstrap Exception

The first commit may be direct to `main` because the repository is being created from empty state. After bootstrap, use the standard workflow.
