# Read-Only and Write-Gated Environment Rollout Checklist

This checklist enables maximum agent autonomy for read-only discovery while keeping production mutations human-gated.

## Environment Names

### Cloudflare

- `cloudflare-readonly`
- `cloudflare-prod`

### Microsoft

- `m365-readonly`
- `m365-prod`

### Google

- `google-readonly`
- `google-prod`

### GitHub

- default `GITHUB_TOKEN` read permissions for safe repo/issue/status reads
- `github-prod` only when sensitive repo mutations need environment approval

## Permission Model

### Read-only environments

Read-only environments should not require human approval once credentials are properly scoped. They may run on schedule, workflow dispatch, issue events, or agent request.

Allowed examples:

- list Cloudflare zones and DNS records
- inspect Cloudflare redirects/rules
- check DNS compliance and GitHub Pages readiness
- list Microsoft domains and DKIM status
- inspect Google Search Console/Analytics/Workspace status where scoped
- list GitHub issues, PRs, workflow runs, and Pages status
- upload artifacts and comment read-only findings on issues

### Write-gated environments

Write-capable environments require GitHub environment protection with required reviewers.

Examples:

- edit Cloudflare DNS records
- create/update Cloudflare redirects
- GitHub Pages cutover records
- Microsoft domain add/verify/DKIM mutations
- Google Workspace/Admin/Search Console property mutations
- GitHub repo transfer, visibility, secrets, environments, branch protections, rulesets

## Human Setup Tasks

Clarke or an authorized admin needs to create/approve these outside the agent:

### Cloudflare read-only

- [ ] Create Cloudflare API token with least-privilege read-only scopes.
- [ ] Scope token to the required account/zones where possible.
- [ ] Add GitHub environment: `cloudflare-readonly`.
- [ ] Add environment secret: `CM_CLOUDFLARE_API_TOKEN_READONLY`.
- [ ] Do **not** require reviewers for read-only environment after scope is verified.

Recommended minimum Cloudflare permissions:

- Zone: Read
- DNS: Read

### Cloudflare production write

- [ ] Create/confirm separate Cloudflare write token.
- [ ] Add GitHub environment: `cloudflare-prod`.
- [ ] Add secret: `CM_CLOUDFLARE_API_TOKEN_DNS_WRITE`.
- [ ] Enable required reviewers.
- [ ] Keep dry-run as default for workflows.

Recommended Cloudflare write permissions:

- Zone: Read
- DNS: Edit
- Additional write scopes only when a workflow proves it needs them.

### Microsoft read-only

- [ ] Create/read existing Entra app for read-only domain/status checks.
- [ ] Prefer GitHub OIDC/federated credential over static secrets when practical.
- [ ] Add environment: `m365-readonly`.
- [ ] Add identifiers/secrets needed by the workflow.

Likely Graph application permission:

- Domain.Read.All or Directory.Read.All, with admin consent.

### Microsoft production write

- [ ] Create stricter write-capable app or expand only when needed.
- [ ] Add environment: `m365-prod`.
- [ ] Enable required reviewers.
- [ ] Document exact Graph/Exchange permissions per workflow.

### Google read-only

- [ ] Create Google credential or workload identity path for read-only APIs.
- [ ] Add environment: `google-readonly`.
- [ ] Add only read-scoped credentials/secrets.

Possible read scopes depend on selected APIs:

- Search Console read-only
- Google Analytics read-only
- Drive metadata/read-only where needed
- Workspace/Admin read-only where needed

### Google production write

- [ ] Create separate write-capable credential only if needed.
- [ ] Add environment: `google-prod`.
- [ ] Enable required reviewers.
- [ ] Document exact scopes per workflow.

## Workflow Design Rules

1. Split every workflow into read-only and write-capable variants where possible.
2. Read-only workflows should never import or reference write secrets.
3. Write workflows should default to `dry_run: true`.
4. Live writes require protected environment approval.
5. Live writes should also require explicit inputs and/or approval labels.
6. Workflows must post before/after summaries to the linked issue.
7. Post-change verification should use read-only workflows.

## Human Request Template

When the agent needs Clarke, send a concise request:

```text
Human task needed: create/approve <environment/credential>.

Purpose: <read-only audit or production write>.
Required scope: <exact least-privilege permissions>.
Where to add it: GitHub repo/org environment <name>, secret <name>.
Why now: <workflow/issue blocked>.
```
