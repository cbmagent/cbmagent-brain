# Hermes Provider Verification Report

Generated UTC: `2026-05-04T01-18-19Z`

This report is redacted and does not intentionally print tokens, API keys, bearer values, or credential files.

## Summary

- **Active provider**: `openai-codex`
- **Active model**: `gpt-5.5`
- **Overall health**: `healthy`

## Verifications

- **primary** `openai-codex` / `gpt-5.5` → ✅ ok latency=4.876s
- **fallback (rank 1)** `nous` / `anthropic/claude-sonnet-4.6` → ✅ ok latency=10.293s
- **fallback (rank 2)** `copilot` / `gpt-5.5` → ✅ ok latency=10.496s

## Fallback Chain

- 1. `anthropic/claude-sonnet-4.6` via `nous`
- 2. `gpt-5.5` via `copilot`

## Config Signals

```text
◆ Model
  Model:        {'default': 'gpt-5.5', 'provider': 'openai-codex'}
  Model:        (auto)

```

## Auth Name Signals

```text
copilot (1 credentials):
  #1  gh auth [REDACTED]

nous (1 credentials):
  #1  device_code          oauth   device_code ←

openai-codex (1 credentials):
  #1  device_code          oauth   device_code ←


```

