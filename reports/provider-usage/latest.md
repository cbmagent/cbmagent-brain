# Provider Usage and Health Report

Generated UTC: `2026-05-04T09-45-27Z`

This report is redacted. It does not intentionally print tokens, API keys, bearer values, or credential files.

## Summary

- Hermes status command: `ok`
- OpenClaw gateway root: `ok` 200
- OpenClaw health: `degraded` - OpenClaw partially responded, but the gateway root or model inventory check failed.
- OpenClaw models visible: `0`
- Recent OpenClaw/Hermes cooldown hits: `5`
- Recommended fallback routing: Use Hermes primary/Nous for new autonomous work; reserve OpenClaw for manual retry or diagnostics.
- GitHub CLI auth: `ok`

## OpenClaw Model Inventory

- No models parsed. Parse/status detail: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`

## Current Config Signals

```text
◆ Model
  Model:        {'default': 'gpt-5.5', 'provider': 'openai-codex'}
  Model:        (auto)

```

## Auth/Provider Names

```text
copilot (2 credentials):
  #1  gh auth [REDACTED]
  #2  GITHUB_[REDACTED]

nous (1 credentials):
  #1  device_code          oauth   device_code ←

openai-codex (1 credentials):
  #1  device_code          oauth   device_code ←


```

## Recent GitHub Actions

```text
completed	success	Read-only domain audit	Read-only domain audit	main	schedule	25307970377	52s	2026-05-04T08:04:09Z
completed	success	feat: add Hermes provider verification workflow (#60)	Validate brain repo	main	push	25306999483	15s	2026-05-04T07:39:39Z
completed	success	feat: add Hermes provider verification workflow (#60)	Publish AI dashboard to GitHub Pages	main	push	25306999453	28s	2026-05-04T07:39:39Z
completed	success	feat: add Hermes provider verification workflow	Validate brain repo	feat/41-hermes-verification	pull_request	25306974902	18s	2026-05-04T07:38:58Z
completed	success	Publish AI dashboard to GitHub Pages	Publish AI dashboard to GitHub Pages	main	schedule	25306588606	23s	2026-05-04T07:28:42Z
completed	success	docs: add portfolio status dashboard markdown (#59)	Validate brain repo	main	push	25302774907	15s	2026-05-04T05:32:25Z
completed	success	docs: add portfolio status dashboard markdown (#59)	Publish AI dashboard to GitHub Pages	main	push	25302774891	21s	2026-05-04T05:32:25Z
completed	success	docs: add portfolio status dashboard markdown	Validate brain repo	feat/portfolio-dashboard-27	pull_request	25302757762	13s	2026-05-04T05:31:47Z
completed	success	feat(#44): add workspace-setup.sh clone/update script (#58)	Publish AI dashboard to GitHub Pages	main	push	25300660965	36s	2026-05-04T04:13:37Z
completed	success	feat(#44): add workspace-setup.sh clone/update script (#58)	Validate brain repo	main	push	25300660952	13s	2026-05-04T04:13:37Z

```

## Recent Rate Limit / Cooldown Signals

### hermes_agent_log

- `2026-05-03 20:24:02,598 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:24:02,622 INFO [20260503_190310_57390b] agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:32:15,343 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:32:15,369 INFO [20260503_174453_cc2319] agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:40:45,545 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:43:05,762 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:47:08,099 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:47:29,397 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-03 20:48:18,785 INFO agent.credential_pool: credential pool: no available entries (all exhausted or empty)`
- `2026-05-04 05:40:55,429 INFO agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`

### hermes_gateway_log

- No recent matching signals found.

### openclaw_commands_log

- No recent matching signals found.

### openclaw_openclaw_log

- No recent matching signals found.

### openclaw_gateway_log

- No recent matching signals found.

## Recommendations

- Treat OpenAI Codex OAuth quota as opaque; monitor observed rate-limit/cooldown errors.
- OpenClaw routing: Use Hermes primary/Nous for new autonomous work; reserve OpenClaw for manual retry or diagnostics.
- Use Nous/local tools as fallback/specialists when primary provider or OpenClaw signals failures.
- Keep deterministic audits in scripts/GitHub Actions so premium model quota is reserved for reasoning/coding.
- Add scheduled provider report workflow after read-only environment design is finalized.
