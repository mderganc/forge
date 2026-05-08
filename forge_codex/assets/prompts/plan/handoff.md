Write the handoff file and render the dashboard.

## Handoff Content
The orchestrator writes `{{HANDOFF_FILE}}` automatically with:
- Plan location (`{{PLAN_FILE}}`)
- Task count and assignments
- Dependencies summary
- Beads state

If you have additional context to include (e.g., notes from the user during
approval), append it to the handoff file after the orchestrator writes it.

## Dashboard
Render the skill completion dashboard per `templates/dashboard.md`.

## Completion Gate
The orchestrator checks `{{PLAN_FILE}}` for any remaining
`<!-- FORGE_SKELETON: ... -->` markers. If any are present, the workflow does
**not** complete and you'll see a warning listing the unfilled sections —
fill them and re-run step 6.

## Suggested Next
- `evaluate --mode pre` (optional: review plan before implementing)
- `implement` (proceed directly to implementation)

## Git Checkpoint
```
git add .codex/forge-codex/ && git commit -m "workflow: plan complete"
```
