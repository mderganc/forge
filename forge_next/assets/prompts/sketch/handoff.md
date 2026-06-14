# forge sketch — Handoff

{{SKETCH_NO_EDIT_POLICY}}

## Gate

Handoff runs only after **collaborative synthesis** in step 2: user confirmed locked vs open (or explicitly said ready for design).

## Required artifacts

- **`{{SKETCH_DECISIONS_REL}}`** — resolved and deferred branches
- **`handoff-sketch.md`** (orchestrator writes via `write_handoff`)

## Handoff content

1. Topic and success criteria
2. Resolved decisions (from sketch-decisions.md)
3. Deferred items design must not assume closed
4. Terminology (and CONTEXT.md updates if domain-docs mode ran)
5. Next: **`forge design --step 1`**

Sketch does **not** replace design or write the design spec.

Default handoff: **`design`**. Use **`plan`** only if direction is fully locked and user skips design.
