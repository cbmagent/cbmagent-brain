# Provider Usage and Health Report

Generated UTC: `2026-05-03T21-36-23Z`

This report is redacted. It does not intentionally print tokens, API keys, bearer values, or credential files.

## Summary

- Hermes status command: `ok`
- OpenClaw gateway root: `ok` 200
- GitHub CLI auth: `ok`

## Current Config Signals

```text
◆ Model
  Model:        {'default': 'gpt-5.5', 'provider': 'openai-codex'}
  Model:        (auto)

```

## Auth/Provider Names

```text
copilot (1 credentials):
  #1  gh auth [REDACTED]

nous (1 credentials):
  #1  device_code          oauth   device_code ←

openai-codex (1 credentials):
  #1  openai-codex-oauth-1 oauth   device_code ←


```

## Recent GitHub Actions

```text
No runs found or command unavailable.
```

## Recent Rate Limit / Cooldown Signals

### hermes_agent_log

- `2026-05-03 16:18:44,636 INFO [20260503_155326_4b62db] agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`
- `2026-05-03 16:18:44,648 INFO [20260503_155326_4b62db] agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`
- `2026-05-03 16:18:44,661 INFO [20260503_155326_4b62db] agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`
- `2026-05-03 16:18:44,674 INFO [20260503_155326_4b62db] agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`
- `2026-05-03 16:42:44,777 ERROR tools.vision_tools: Error analyzing image: Invalid image source. Provide an HTTP/HTTPS URL or a valid local file path.`
- `    raise ValueError(`
- `ValueError: Invalid image source. Provide an HTTP/HTTPS URL or a valid local file path.`
- `2026-05-03 16:51:23,496 INFO [20260503_155326_4b62db] agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`
- `2026-05-03 16:57:07,398 INFO agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`
- `2026-05-03 17:25:50,280 INFO agent.auxiliary_client: Auxiliary auto-detect: using main provider openai-codex (gpt-5.5)`

### hermes_gateway_log

- `2026-05-03 02:13:22,974 WARNING gateway.platforms.telegram: [Telegram] Connect attempt 1/8 failed: httpx.ConnectError: All connection attempts failed — retrying in 1s`
- `2026-05-03 02:13:23,979 WARNING gateway.platforms.telegram: [Telegram] Connect attempt 2/8 failed: httpx.ConnectError: All connection attempts failed — retrying in 2s`
- `2026-05-03 10:17:06,471 WARNING gateway.platforms.telegram: [Telegram] Connect attempt 1/8 failed: httpx.ConnectError: All connection attempts failed — retrying in 1s`
- `2026-05-03 10:17:07,475 WARNING gateway.platforms.telegram: [Telegram] Connect attempt 2/8 failed: httpx.ConnectError: All connection attempts failed — retrying in 2s`
- `2026-05-03 14:29:23,757 WARNING gateway.platforms.telegram: [Telegram] Telegram network error, scheduling reconnect: httpx.ReadError: `
- `2026-05-03 14:29:23,757 WARNING gateway.platforms.telegram: [Telegram] Telegram network error (attempt 1/10), reconnecting in 5s. Error: httpx.ReadError: `
- `2026-05-03 14:29:30,125 INFO gateway.platforms.telegram: [Telegram] Telegram polling resumed after network error (attempt 1)`
- `2026-05-03 15:04:18,542 INFO gateway.run: inbound message: platform=telegram user=cbm agent chat=8742801497 msg='Im getting this error on my session with openclaw ⚠️ Something went wrong while '`

## Recommendations

- Treat OpenAI Codex OAuth quota as opaque; monitor observed rate-limit/cooldown errors.
- Use Nous/OpenClaw/local tools as fallback/specialists when primary provider signals failures.
- Keep deterministic audits in scripts/GitHub Actions so premium model quota is reserved for reasoning/coding.
- Add scheduled provider report workflow after read-only environment design is finalized.
