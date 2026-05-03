# Read-Only vs Write-Gated Environments

The agent should maximize autonomy for discovery and preparation while keeping production mutations gated.

## Environment Pattern

Use paired environments:

- `cloudflare-readonly`
- `cloudflare-prod`
- `m365-readonly`
- `m365-prod`
- `google-readonly`
- `google-prod`
- `github-prod` where sensitive GitHub mutations are needed

## Read-Only Environments

Read-only jobs may run without human approval when credentials are properly scoped.

Allowed examples:

- DNS inventory
- DNS compliance checks
- GitHub Pages readiness checks
- repository status reports
- Microsoft domain/DKIM status checks
- Google Workspace/Search Console/Analytics read reports
- issue comments with findings
- uploaded artifacts

## Write-Gated Environments

Write-capable jobs require GitHub environment protection and/or explicit approval labels.

Examples:

- DNS record create/update/delete
- Cloudflare redirect changes
- GitHub Pages cutover
- Microsoft tenant/domain mutations
- Google Workspace/Admin mutations
- GitHub repo transfer, visibility, secrets, rulesets

## Default Rule

Agents observe and prepare. GitHub Actions with protected environments execute production writes.
