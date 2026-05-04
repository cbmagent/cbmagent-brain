# cbmagent Operator Workspace

Open `workspaces/cbmagent.code-workspace` in VS Code to use this repo as the local operator console.

## Intended Roots

| Local path | GitHub repo |
|---|---|
| `~/cbmagent-brain` | `cbmagent/cbmagent-brain` |
| `~/clarkemoyer.com` | `clarkemoyer/clarkemoyer.com` |
| `~/technologyadoptionbarriers.org` | `clarkemoyer/technologyadoptionbarriers.org` |
| `~/FFC-IN-FFC_Single_Page_Template` | `FreeForCharity/FFC-IN-FFC_Single_Page_Template` |
| `~/FFC-IN-Footer_Only_Template` | `FreeForCharity/FFC-IN-Footer_Only_Template` |
| `~/FFC-Cloudflare-Automation` | `FreeForCharity/FFC-Cloudflare-Automation` |
| `~/openclaw-deployment` | `cbmagent/openclaw-deployment` |

Some roots may not exist locally yet. Run the setup script (below) to clone them.

## Setup Script

`scripts/workspace-setup.sh` clones or fast-forwards all workspace repos to their expected local paths.
It will not overwrite any repo that has uncommitted local changes.

```bash
# Preview what would happen (no changes made):
./scripts/workspace-setup.sh --dry-run

# Clone / update all repos:
./scripts/workspace-setup.sh
```

Requirements: `git`, `gh` CLI (authenticated with `gh auth login`).

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
