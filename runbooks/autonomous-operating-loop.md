# Autonomous Operating Loop

This repo should be operated as an active agent brain, not a static notebook.

## Loop

1. Refresh local `main`.
2. Read open issues and labels.
3. Select the highest-priority non-blocked issue that does not require human credentials.
4. Create a branch named from the issue.
5. Make the smallest useful increment.
6. Validate locally.
7. Push branch and open PR linking `Closes #N` or `Refs #N`.
8. Check/repair CI.
9. Merge when safe and update/close issue.
10. Generate or update progress report.
11. Continue to next task until blocked or external approval is required.

## Work Selection

Preferred order:

1. `priority:critical` + not `human-needed` + not `blocked`
2. `readonly` automation
3. validation/CI that protects future work
4. repo discovery and dashboards
5. provider health/routing visibility
6. site factory and migration implementation
7. write-gated workflows in dry-run mode
8. human-needed setup issues only when unavoidable

## Stop Conditions

Only stop and text Clarke when:

- external credentials/environment approval are needed,
- a production write/cutover decision is needed,
- GitHub auth/permissions fail,
- there is a real ambiguity that changes the technical path,
- repeated CI failures need human judgment.

## Human Task Message Format

```text
Human task needed: <action>
Why now: <issue/workflow blocked>
Where: <repo/org/provider location>
Required scope: <least privilege>
Secret/environment name: <name>
Verification: <how agent will verify after you finish>
```
