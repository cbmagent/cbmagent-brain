# Agent Stack

This brain is provider-neutral.

## Current Runtime

- Agent runtime: Hermes Agent
- Primary model/backend: OpenAI Codex OAuth / GPT-5.5
- Fallback/specialist providers: Nous, OpenClaw, GitHub Copilot, local tools

## Principle

The brain should be explicit about which agents are active while avoiding unnecessary coupling to any one runtime. If Hermes is replaced or supplemented later, the repo should continue to function as the same operational brain.

## Agent Roles

- Hermes: current orchestrator and tool runner
- OpenClaw: GitHub/Copilot specialist and potential backend alternative
- GitHub Copilot: code review and IDE-native assistant
- Nous: fallback/provider-safe hosted model source
- Local tools: deterministic shell, git, DNS, file, and build operations
