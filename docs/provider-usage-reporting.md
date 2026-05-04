# Provider Usage and Limits Reporting

Goal: give the agent enough awareness of model/backend availability to route work safely and avoid silent stalls.

## Providers to Track

- OpenAI Codex OAuth / GPT-5.5
- Nous
- OpenClaw / GitHub Copilot
- GitHub Actions minutes/runs
- Local tools/Ollama if configured
- Google/Microsoft API quota signals where workflows expose them

## Reality Check

Some subscription/OAuth providers expose limited or opaque quota data. For those providers, track observed rate-limit/cooldown/failure signals from logs and workflow outputs rather than inventing exact limits.

## Report Output

A daily report should include:

- current Hermes provider/model
- OpenClaw gateway status and `/v1/models` inventory count
- recent rate-limit/cooldown messages from Hermes and OpenClaw logs
- explicit OpenClaw health classification: `healthy`, `degraded`, or `unavailable`
- fallback routing recommendation when OpenClaw is cooling down or unreachable
- GitHub Actions recent failures/stalls
- recommended provider routing for the day
- human tasks needed, if any

## OpenClaw Health Checks

Use `scripts/provider-usage-report.py` for read-only OpenClaw monitoring:

```bash
python scripts/provider-usage-report.py
```

The script checks the local OpenClaw gateway root and OpenAI-compatible model list at `http://127.0.0.1:18789/v1/models`, parses model IDs, scans recent Hermes/OpenClaw logs for cooldown/rate-limit terms, and writes redacted Markdown/JSON under `reports/provider-usage/`. It does not mutate OpenClaw, GitHub, DNS, or provider configuration.

## Hermes Verification

Use `scripts/hermes-verification.py` for redacted Hermes routing checks:

```bash
# Cheap inventory only; safe for scheduled runs. Add --strict if callers
# should fail when the Hermes CLI is unavailable or unhealthy.
python scripts/hermes-verification.py
python scripts/hermes-verification.py --strict

# Tiny live primary-provider smoke probe.
python scripts/hermes-verification.py --smoke

# Probe primary plus configured fallback providers when worth the quota.
python scripts/hermes-verification.py --smoke --include-fallbacks
```

The script writes JSON/Markdown reports under `reports/hermes-verification/`. It records provider/model names, pass/fail state, and latency; it intentionally avoids persisting prompt text, completion text, credential files, tokens, or API keys. The GitHub Actions workflow `.github/workflows/hermes-verification.yml` runs inventory on a schedule and exposes manual inputs for smoke probes.
