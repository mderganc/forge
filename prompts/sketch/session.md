# forge sketch — Session

{{SKETCH_NO_EDIT_POLICY}}

**Topic:** {{TOPIC}}

Follow **`templates/sketch-protocol.md`** — conversation loop, not checklist order.

## This step

1. **Reflect → confirm → ask** — synthesis every 2–3 exchanges.
2. **Loop-back** — revise `{{SKETCH_DECISIONS_PATH}}` when context changes; name which section changed (Decisions so far / Not yet specified / Out of scope).
3. **One question at a time** with a recommended answer; follow-ups on the same thread until settled.
4. Explore the codebase when faster than asking.
5. Domain-docs mode: `templates/CONTEXT-FORMAT.md`, `templates/ADR-FORMAT.md`.
6. Do **not** write `docs/forge/specs/*-design.md`.
7. **Plan, don't do** — record decisions; defer implementation and design specs to later skills.

## Synthesis checkpoint

Every 2–3 exchanges, summarize:
- **Destination** (what ready for design looks like)
- **Decisions so far** (locked)
- **Not yet specified** (fog)
- **Out of scope**

Ask: “What did I get wrong?”

## Continue or handoff

- **Keep talking:** finish this turn, then re-run **`forge sketch --step 2`** (same `--state` if shown).
- **Ready for design:** collaborative stop — summarize destination + locked vs fog vs out-of-scope; user confirms → **`forge sketch --step 3`**.

Do not run step 3 until the user confirms synthesis or says they are ready for design. **Destination** must be filled before handoff.
