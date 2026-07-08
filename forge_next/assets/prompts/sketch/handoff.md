# forge sketch — Handoff

{{SKETCH_NO_EDIT_POLICY}}

## Gate

Handoff runs only after **collaborative synthesis** in step 2: user confirmed locked vs open (or explicitly said ready for design). **`## Destination`** in `sketch-decisions.md` must be filled.

## Required artifacts

- **`{{SKETCH_DECISIONS_REL}}`** — destination, decisions so far, not yet specified, out of scope
- **`handoff-sketch.md`** (orchestrator writes via `write_handoff`)

## Handoff content

1. Topic and **destination** (what ready for design looks like)
2. Decisions so far (from sketch-decisions.md)
3. **Not yet specified** — fog design must not assume resolved
4. **Out of scope** — boundaries design must respect
5. Terminology (and CONTEXT.md updates if domain-docs mode ran)
6. Next: **`forge design --step 1`**

Sketch does **not** replace design or write the design spec.

Default handoff: **`design`**. Use **`plan`** only if direction is fully locked and user skips design.
