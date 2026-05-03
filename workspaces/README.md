# cbmagent Operator Workspace

Open `workspaces/cbmagent.code-workspace` in VS Code to use this repo as the local operator console.

## Intended Roots

- `cbmagent-brain`
- `clarkemoyer.com`
- `technologyadoptionbarriers.org`
- `FFC-IN-FFC_Single_Page_Template`
- `FFC-IN-Footer_Only_Template`
- `FFC-Cloudflare-Automation`

Some roots may not exist locally yet. Clone them as needed.

## Recommended Extensions

See `.vscode/extensions.json`.

## Useful Tasks

Run VS Code command **Tasks: Run Task** and select:

- `Hermes: status`
- `Hermes: auth list`
- `Brain: validate YAML`
- `Brain: run read-only domain audit`
- `Brain: provider usage report`
- `GitHub: open issues`
- `GitHub: open PRs`

## Operating Model

Use VS Code as an operator cockpit, not as a replacement for GitHub. Repo-specific work still follows issue → branch → PR → checks/review → merge.
