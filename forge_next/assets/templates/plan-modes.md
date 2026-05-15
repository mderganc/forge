# Plan Modes Reference

Used by `forge plan`, planner/architect agents, and `templates/writing-plans.md`.

## Modes

| Mode | Best for | Ceremony |
|------|----------|----------|
| `default` | Multi-module features, moderate/high risk, handoff-heavy work | Full governance sections |
| `lite` | Short, isolated, low-risk ad hoc tasks | Concise sections, same task rigor |

## Shared invariants (non-negotiable)

- No placeholder language: `TBD`, `TODO`, "implement later", "add validation", "handle edge cases" without specifics.
- Every task: exact file paths, verification command, expected outcome.
- TDD for runtime code changes (or explicit exemption for docs/config-only tasks).
- Compatible with skeleton markers, completion gates, and implement handoff.

## Precedence

1. CLI `--mode <default|lite>`
2. Interactive user choice (when CLI omitted on new session)
3. Persisted preference in `.codex/forge-codex/memory/plan-preference.json`
4. System fallback: `default`

Legacy sessions without `plan_mode` in state hydrate as `default` with a one-time note.

## Preference file

Path: `.codex/forge-codex/memory/plan-preference.json`

```json
{
  "default_mode": "lite"
}
```

Saving preference affects **future new sessions** only, not in-progress state.
