# forge sketch — Session

{{SKETCH_NO_EDIT_POLICY}}

**Topic:** {{TOPIC}}

Follow **`templates/sketch-protocol.md`** — conversation loop, not checklist order.

## This step

1. **Reflect → confirm → ask** — synthesis every 2–3 exchanges.
2. **Loop-back** — revise `{{SKETCH_DECISIONS_PATH}}` when context changes; say which decision changed.
3. **One question at a time** with a recommended answer; follow-ups on the same thread until settled.
4. Explore the codebase when faster than asking.
5. Domain-docs mode: `templates/CONTEXT-FORMAT.md`, `templates/ADR-FORMAT.md`.
6. Do **not** write `docs/forge/specs/*-design.md`.

## Continue or handoff

- **Keep talking:** finish this turn, then re-run **`forge sketch --step 2`** (same `--state` if shown).
- **Ready for design:** collaborative stop — summarize locked vs open; user confirms → **`forge sketch --step 3`**.

Do not run step 3 until the user confirms synthesis or says they are ready for design.
