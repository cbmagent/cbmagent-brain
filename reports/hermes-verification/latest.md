# Hermes Provider/Model Verification

Generated UTC: `2026-05-04T07-37-53Z`

This report is redacted. It records provider/model names, pass/fail state, and latency only; it does not intentionally persist prompts, completions, credential files, tokens, or API keys.

## Detected Routing

- Primary: `openai-codex` / `gpt-5.5`
- Fallback entries: `2`
  - 1. `nous` / `anthropic/claude-sonnet-4.6`
  - 2. `copilot` / `gpt-5.5`

## Command Checks

- hermes_config_show: `pass` (473 ms)
- hermes_fallback_list: `pass` (321 ms)
- hermes_status: `pass` (1525 ms)
- hermes_auth_list: `pass` (883 ms)

## Smoke Checks

- `openai-codex` / `gpt-5.5`: `pass` (6883 ms)

## Notes

- Default mode performs inventory only so scheduled runs do not consume provider quota.
- Live smoke checks intentionally use a tiny response and persist only pass/fail, latency, and redacted failure diagnostics.
- Fallback smoke probes require --include-fallbacks so operators can decide when broader provider checks are worth the cost.
