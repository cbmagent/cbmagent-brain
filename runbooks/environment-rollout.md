# Environment Rollout Runbook

## Goal

Give agents autonomous read-only inspection across Cloudflare, Microsoft, Google, and GitHub while requiring human approval for production writes.

## Order of Operations

1. Create read-only provider credentials first.
2. Add read-only GitHub environments and secrets.
3. Add read-only workflows and prove they cannot mutate state.
4. Create write-capable environments separately.
5. Add required reviewers to write-capable environments.
6. Add dry-run-only write workflows.
7. Add live mode only after dry-runs and approvals are proven.

## Verification

For each read-only workflow:

- Confirm it succeeds without production write secrets.
- Confirm it can run without environment approval.
- Confirm it uploads/comment reports only.
- Confirm it cannot call mutation endpoints.

For each write workflow:

- Confirm dry-run is default.
- Confirm environment approval is required for live mode.
- Confirm it comments before/after results.
- Confirm post-change read-only verification runs.

## Blockers

The agent cannot create external provider credentials by itself. Clarke/admin action is required for Cloudflare, Microsoft, and Google credential setup.
