# forge sketch — Handoff

{{SKETCH_NO_EDIT_POLICY}}

## Gate

Handoff runs only after **collaborative synthesis** in step 2: user confirmed locked vs open (or explicitly said ready for design). **`## Destination`** in `sketch-decisions.md` must be filled.

## Required artifacts

- **`{{SKETCH_DECISIONS_REL}}`** — destination, size, recommended scope, decisions so far, not yet specified, scope expansion, out of scope
- **`handoff-sketch.md`** (orchestrator writes via `write_handoff`)

## Handoff content

1. Topic and **destination** (what ready for design looks like)
2. **Size** (small/medium/large) and rationale
3. **Recommended scope** (original ask)
4. Decisions so far (from sketch-decisions.md)
5. **Not yet specified** — fog design must not assume resolved
6. **Scope expansion** — optional, not recommended unless user opted in
7. **Out of scope** — boundaries design must respect
8. Prototype offer notes (if a logic/UI question remains — future skill; see `docs/forge/prototype-skill-stub.md`)
9. Terminology (and CONTEXT.md updates if domain-docs mode ran)
10. Next: **`forge design --step 1`**

Sketch does **not** replace design or write the design spec.

Default handoff: **`design`**. Use **`plan`** only if direction is fully locked and user skips design.
