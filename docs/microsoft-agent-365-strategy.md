# Microsoft Agent 365 Strategy

## Purpose

Microsoft Agent 365 should be treated as the Microsoft 365 governance and security control plane for Microsoft-visible agents. `cbmagent-brain` remains the provider-neutral portfolio/source-of-truth, and GitHub remains the work-execution and audit plane for issues, branches, PRs, checks, Actions, reviews, and release history.

This is a complement, not a replacement:

- Agent 365 answers: Which agents are visible to Microsoft 365, who owns them, what Microsoft data/tools can they touch, and what security/compliance signals apply?
- `cbmagent-brain` answers: Which agents exist across providers, projects, repos, domains, dashboards, runbooks, and operating policies?
- GitHub answers: What work was requested, prepared, reviewed, approved, executed, and merged?

## Agent 365 capabilities to align with

Microsoft positions Agent 365 around three pillars: observe, govern, and secure.

Relevant capabilities from Microsoft documentation and announcements include:

- Agent registry in the Microsoft 365 admin center for inventory, owner tracking, unmanaged-agent visibility, export, pinning, upload, and governance review.
- Agent details with metadata for description, publisher, status, channel, platform, sensitivity, version, permissions, users, data/tools, security, certification, activity, connected agents, and AI teammate instances where applicable.
- Agent identity blueprints in Microsoft Entra Agent ID for governed agent identity templates, authentication configuration, permissions, activity logs, Conditional Access targeting, and disabling authentication for all identities from a blueprint.
- Microsoft Graph delegated and application permission models, where delegated permissions are bounded by the signed-in user's access and application permissions can grant tenant-wide access and require administrator consent.
- Agent 365 CLI setup paths for blueprints, MCP/tool permissions, bot permissions, Copilot Studio permissions, and custom permissions, with admin consent required for OAuth2 permission grants.
- Defender, Intune, Entra, and Purview integrations for shadow-agent discovery, endpoint blocking/protection, identity governance, runtime threat monitoring, and data protection/compliance signals.

## Which agents should be represented in Agent 365

Represent agents in Agent 365 when they are visible to, authenticated by, deployed into, or materially integrated with Microsoft 365/Entra/Graph/Teams/Outlook/SharePoint/Defender/Purview/Intune.

### Register or map now / first wave

1. Hermes Agent runtime for `cbmagent-brain`
   - Why: primary orchestrator and tool runner; may use GitHub, browser, web, terminal, and future Microsoft-readonly tooling.
   - Agent 365 stance: internal line-of-business/supporting operations agent. Use delegated or tightly scoped app-only identity only when Microsoft API access is needed.

2. Hermes Kanban dispatcher/workers
   - Why: autonomous task execution surface with durable task handoffs.
   - Agent 365 stance: represent the dispatcher/control service and, if practical, high-risk specialist worker classes rather than every ephemeral run.

3. Microsoft 365 readonly audit/reporting agents
   - Why: intended use of `m365-readonly` environment and safest early adoption path.
   - Agent 365 stance: first-class Microsoft-visible agents with readonly Graph/Entra/Purview reporting scopes.

4. GitHub Copilot / Copilot Chat / Copilot coding surfaces used by cbmagent operations
   - Why: Microsoft ecosystem agent already visible to Microsoft governance surfaces and GitHub audit trails.
   - Agent 365 stance: map as Microsoft/external platform agents; track policy posture and usage instead of duplicating GitHub records.

5. OpenClaw when used against GitHub/Copilot/Microsoft-visible work
   - Why: announced Agent 365 shadow-agent controls specifically call out local/CLI coding agents such as OpenClaw, GitHub Copilot CLI, and Claude Code as discovery/protection targets.
   - Agent 365 stance: represent as endpoint/local or external agent where discovered, plus record cbmagent ownership and allowed repos.

### Register or map later / conditional

6. Browser automation agents
   - Register only when they access Microsoft 365 admin portals, Teams, Outlook, SharePoint, or tenant resources.

7. Local deterministic tools
   - Do not register shell/git/DNS tools as standalone agents. Track them as tools/capabilities used by a registered agent unless they gain independent credentials or autonomy.

8. Project-specific website/content agents
   - Register only if they read/write Microsoft 365 content, interact in Teams/Outlook, or receive an Entra identity. Otherwise keep them in GitHub/project dashboards.

9. AI teammates
   - Use only for a clearly human-facing Microsoft 365 presence such as Teams/email/calendar interaction. Do not promote internal batch workers to AI teammates by default.

## Metadata cbmagent-brain should track

Add or align a provider-neutral agent registry model that can map into Agent 365 without making the brain Microsoft-specific.

Recommended fields:

### Stable identity and ownership

- `agent_id`: provider-neutral cbmagent identifier.
- `display_name`.
- `description` / purpose.
- `owner`: human owner or accountable team.
- `technical_owner`: maintainer/repo/profile responsible for implementation.
- `publisher`: cbmagent, Microsoft, GitHub, OpenClaw, Nous, external partner, etc.
- `publisher_type`: internal, Microsoft, external_partner, shared_by_creator.
- `source_repo` / `source_url`.
- `runbook_url`.
- `support_contact`.

### Platform and runtime

- `runtime`: Hermes, OpenClaw, GitHub Copilot, Copilot Studio, Claude Code, local tool, other.
- `provider`: OpenAI, Nous, Microsoft, local, etc.
- `model_or_backend` where appropriate.
- `deployment_environment`: local, GitHub Actions, Windows endpoint, server, cloud, SaaS.
- `workspace_kind`: scratch, dir, worktree, GitHub Actions runner, etc.
- `channels`: CLI, GitHub, Teams, Outlook, SharePoint, browser, API, dashboard.
- `status`: proposed, active, paused, retired, blocked, unmanaged.
- `lifecycle_stage`: experiment, pilot, production, deprecated.

### Microsoft / Agent 365 mapping

- `m365_visible`: true/false.
- `agent365_record_id` when known.
- `entra_app_id` / `agent_identity_blueprint_id` / `agent_id_in_entra` when provisioned.
- `identity_model`: none, delegated_user, app_only, agent_identity_blueprint, ai_teammate.
- `tenant_id` as non-secret metadata where appropriate.
- `m365_channels`: Teams, Outlook, Copilot, Microsoft 365 apps, SharePoint.
- `agent365_publisher_type`, `agent365_platform`, `agent365_channel`, `agent365_availability`, `agent365_deployment_status`.
- `blueprint_name` and `blueprint_owner`.

### Permissions, data, and tools

- `graph_permissions_delegated`: list of requested/granted delegated scopes.
- `graph_permissions_application`: list of requested/granted app-only permissions.
- `entra_roles`: RBAC roles, if any.
- `admin_consent_required`: true/false.
- `purview_labels_or_policies`: applicable data protection/compliance controls.
- `defender_monitoring`: none, planned, enabled.
- `conditional_access_policy_ids` or names.
- `data_sources`: GitHub, Microsoft Graph, SharePoint sites, Teams, Outlook, DNS, Cloudflare, Google, etc.
- `tool_access`: GitHub CLI, Graph API, M365 admin center, browser automation, terminal, DNS provider, etc.
- `write_capabilities`: explicit list of possible mutations.
- `readonly_capabilities`: explicit list of safe reporting/discovery actions.

### Risk, governance, and audit

- `risk_tier`: low, medium, high, critical.
- `data_sensitivity`: public, internal, confidential, regulated, privileged_admin.
- `production_write_allowed`: false by default.
- `approval_required`: none, GitHub environment, M365 admin, both.
- `approval_environment`: e.g., `m365-prod`, `github-prod`.
- `last_reviewed_at`.
- `next_access_review_at`.
- `reviewer`.
- `audit_links`: GitHub issues/PRs/actions, Agent 365 export, dashboard URL.
- `last_activity_seen_at`.
- `decommission_plan`.

## Read-only Microsoft capabilities that are safe for agents

Safe means: scoped to least privilege, preferably delegated or app-only readonly, no production mutation, outputs written back as GitHub issue comments/artifacts/reports, and secrets held in GitHub Actions environments or approved local credential stores.

Good candidates for `m365-readonly`:

- Agent 365 registry export/review: list agents, owners, publisher type, platform, channel, unmanaged/ownerless status, activity summaries, and risk flags.
- Microsoft Graph inventory reads: users, groups, service principals/app registrations, OAuth grants, directory roles, Teams/SharePoint site metadata, domain status, and audit-relevant settings using readonly scopes.
- Entra governance reads: Conditional Access policy metadata, app consent grants, service principal owners, sign-in/activity logs where licensed and permitted, access review status.
- Defender/Intune reads: discovered local/CLI agents, endpoint posture, allowed/blocked agent execution policy status, security alerts relevant to agents.
- Purview/compliance reads: sensitivity label inventory, DLP policy metadata, compliance/risk indicators exposed to the agent details/security tabs.
- M365 admin reads: domain/DKIM/SPF/DMARC posture, tenant settings, published/installed agent availability, pinned agents, ownerless agents.

Readonly guardrails:

- Prefer `*.Read.All`, `Directory.Read.All`, `AuditLog.Read.All`, report-reader style roles, or dedicated readonly admin roles where possible.
- Avoid app-only permissions unless a service account/batch job truly needs them; application permissions can read tenant-wide data and require admin consent.
- Do not grant write scopes to a readonly agent even if the code path promises not to use them.
- Store generated reports in `reports/` or issue comments; avoid storing raw PII-heavy exports in the repo.

## Write actions that require approval

### Require GitHub environment approval

Use protected GitHub Actions environments when the action is executed through repo automation or changes repository/workflow state:

- Running workflows with write-capable secrets for Microsoft/Graph/Entra operations.
- Creating or updating repo secrets/environments/rulesets where supported by automation.
- Opening or merging PRs that alter production automation paths.
- Publishing dashboard/site changes that expose governance data.
- Dispatching production audit/remediation workflows from issues.
- Any operation that writes durable governance records back to the repo outside normal PR review.

Recommended environments:

- `m365-readonly`: readonly report generation; no human approval if scopes are truly readonly.
- `m365-prod`: Graph/Entra/Purview/Defender/M365 mutations; required reviewers.
- `github-prod`: sensitive GitHub mutations; required reviewers.

### Require Microsoft 365 / Entra admin approval

Use M365/Entra admin approval when the action changes tenant configuration, grants consent, changes agent availability, or affects users/data:

- Granting OAuth/admin consent for Graph application permissions or privileged delegated scopes.
- Creating/updating/disabling an Entra Agent ID blueprint.
- Creating/deprovisioning agent identities or AI teammate identities.
- Assigning Conditional Access policies, app consent policies, roles, groups, or access reviews.
- Installing, uninstalling, blocking, pinning, or publishing agents for users/org-wide availability.
- Uploading agent manifests/ZIPs to Agent 365 or updating store-listed agents.
- Changing Defender/Intune controls that block or allow local/CLI agents.
- Changing Purview labels/DLP/compliance policies.
- Any write to mailbox, Teams, SharePoint, OneDrive, calendar, or directory content.

### Require both GitHub and M365 approvals

Require both when GitHub automation will perform an M365 tenant mutation. GitHub validates the requested work, records the issue/PR/action audit trail, and releases environment secrets; M365/Entra approval validates tenant-level consent and policy impact.

Examples:

- Workflow creates an Agent ID blueprint and requests/administers Graph permission grants.
- Workflow publishes or blocks an agent in Microsoft 365 admin center.
- Workflow changes Conditional Access or Defender/Intune policies.
- Workflow creates an AI teammate identity.

## Complementary operating model

1. `cbmagent-brain` keeps a provider-neutral agent registry and strategy docs.
2. GitHub Issues request investigations and changes.
3. GitHub branches/PRs update docs, registry records, scripts, dashboards, and runbooks.
4. GitHub Actions perform readonly discovery automatically and production writes only through protected environments.
5. Agent 365 provides Microsoft-side visibility, ownership, risk, activity, identity governance, and admin controls for Microsoft-visible agents.
6. Agent 365 exports and signals feed back into `cbmagent-brain` reports/dashboards, but GitHub remains the audit trail for work execution.
7. Microsoft tenant changes are never performed directly by ad hoc agents; they are prepared as reviewed GitHub work and approved/administered through M365/Entra controls.

## Recommended next steps

1. Add `agents.yaml` or similar provider-neutral registry to `cbmagent-brain` using the metadata fields above.
2. Create an `m365-readonly` GitHub Actions environment and document required readonly scopes/roles before adding credentials.
3. Build a readonly Agent 365/M365 inventory report that exports registry/owner/risk/activity metadata and writes a sanitized summary to `reports/agent365/`.
4. Map the current first-wave agents: Hermes runtime, Kanban dispatcher/workers, M365 readonly audit agent, GitHub Copilot surfaces, and OpenClaw if used on Microsoft-visible/GitHub work.
5. Define `m365-prod` and `github-prod` protected environment reviewer requirements before enabling any write-capable Microsoft automation.
6. Keep Agent 365 adoption incremental: register/observe first, then governance policies, then carefully approved tool/write access, and only then AI teammate scenarios.

## Sources reviewed

- Microsoft Security Blog, "Microsoft Agent 365, now generally available, expands capabilities and integrations" (2026-05-01).
- Microsoft Community Hub, "What's New in Agent 365: May 2026" (2026-05-01).
- Microsoft Learn, "Get started with Agent 365 development".
- Microsoft Learn, "Agent Registry in Microsoft 365 admin center".
- Microsoft Learn, "Understand agent details in Microsoft 365 admin center".
- Microsoft Learn, "Overview of Microsoft Graph permissions".
- Microsoft Learn, "Agent identity blueprints in Microsoft Entra Agent ID".
- Microsoft Learn, "Agent 365 CLI setup command reference".
