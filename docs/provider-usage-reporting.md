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
- OpenClaw gateway status
- recent rate-limit/cooldown messages
- GitHub Actions recent failures/stalls
- recommended provider routing for the day
- human tasks needed, if any
