# Develop Complete — Handoff

{{DEVELOP_NO_EDIT_POLICY}}

## Handoff
Capture not only facts but the **shared framing** from the session—what opportunities surfaced, which creative directions were considered, and what the user valued—so the next skill inherits the conversation, not just artifacts.

Write `.codex/forge-codex/memory/handoff-develop.md` with:
- Approved solutions with beads IDs
- Team composition
- Scope assessment
- Task type
- Key investigation findings

## Dashboard
Render skill completion dashboard per `templates/dashboard.md`.

## Doc-writer Capture
Dispatch Doc-writer to capture learnings in `.codex/forge-codex/memory/doc-writer.md`.

## Suggested Next

`plan` — **only after** any required design spec gate is complete (see `.develop-spec-gate.json` when `spec_required`).

Orchestrator context:

- **Scope tier:** {{SCOPE_TIER}}
- **Spec required:** {{SPEC_REQUIRED}}
- **Spec gate status:** {{SPEC_GATE_STATUS}}

## Git Checkpoint
git add .codex/forge-codex/ && git commit -m "workflow: develop complete -- solutions approved"
