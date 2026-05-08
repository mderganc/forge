# Remediation Loop

Fix open findings and re-review until clean.

## Current Findings
{{PREVIOUS_FINDINGS}}

## Remediation Protocol

While open findings remain:

1. **Group findings** — Architect groups related findings into remediation batches
2. **Plan fixes** — For each batch: root cause, approved fix, affected files, risks
3. **Critic review** — Critic reviews remediation plan: "Fixing symptom or cause?"
4. **Dispatch fix** — PM dispatches fix to appropriate agent
5. **Re-review** — Original reviewer + Critic verify fix
6. **Update tracker** — Mark resolved or add new findings

## Exit Conditions
- All findings RESOLVED
- User accepts remaining risk
- External blocker (→ backlog)

## Agent Lifecycle

Each remediation cycle dispatches a fix agent and one or more re-reviewers.
Close each agent (`close_agent`) the moment it has reported back; do not carry
open agents into the next remediation batch. Codex caps concurrent agents and
leaked sessions across many remediation rounds will block further dispatch.
See `templates/codex-runtime.md` → *Parallel work*.

## Review Round
Current round: {{REVIEW_ROUND}}

No fixed iteration limit. Loop continues until clean.
