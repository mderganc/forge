# forge sketch — Handoff

{{SKETCH_NO_EDIT_POLICY}}

## Required artifacts

- **`{{SKETCH_DECISIONS_REL}}`** in memory — resolved and deferred branches.
- **`handoff-sketch.md`** (orchestrator also writes via `write_handoff`).

## Handoff content

Summarize for design:

1. **Topic** and success criteria from sketch.
2. **Resolved decisions** (copy from sketch-decisions.md).
3. **Deferred** items design must not assume closed.
4. **Terminology** — canonical terms (and `CONTEXT.md` updates if domain-docs mode ran).
5. **Explicit next step:** Run **`forge design --step 1`**. Design will:
   - Read `sketch-decisions.md` if present
   - Investigate and brainstorm **solutions**
   - Produce **`docs/forge/specs/YYYY-MM-DD-<slug>-design.md`** when scope is medium/large (spec gate before step 7)

Sketch does **not** replace design and does **not** write the design spec.

## Suggested next

Default: **`design`**. Use **`plan`** only if the user explicitly wants to skip design and the direction is fully locked.
