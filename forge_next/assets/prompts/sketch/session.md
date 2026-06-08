# forge sketch — Session

{{SKETCH_NO_EDIT_POLICY}}

**Topic:** {{TOPIC}}

Follow **`templates/sketch-protocol.md`** for the full loop.

## Your job this step

1. Interview the user **one question at a time** with a **recommended answer** each turn.
2. Explore the codebase when that answers the question faster than asking.
3. Maintain **`{{SKETCH_DECISIONS_PATH}}`** — update after each resolved branch.
4. When domain-docs mode is on, apply `templates/CONTEXT-FORMAT.md` and `templates/ADR-FORMAT.md` rules.
5. Do **not** author `docs/forge/specs/*-design.md` — design does that after investigation and solution approval.

## Stop when

The user agrees the decision tree for **intent** is clear enough to start design (or plan if they want to skip design).

Then run **`forge sketch --step 3`** (preserve `--state` if shown in orchestrator output).
