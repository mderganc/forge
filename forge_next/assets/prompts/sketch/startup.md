# forge sketch — Startup

{{SKETCH_NO_EDIT_POLICY}}

## What sketch is for

**Iterative intent dialogue** before design — pair-thinking with synthesis checkpoints, not a form. See **`templates/sketch-protocol.md`**.

- **Sketch** → `sketch-decisions.md` (intent only — destination, size, recommended scope, decisions, fog, scope expansion, out of scope)
- **Design** → investigation, solutions, **`docs/forge/specs/...-design.md`**

Routing: [AGENTS.md](../../AGENTS.md) § Process-first and § Sketch vs design. Size model: `templates/scope-size-model.md`.

## Setup

1. Confirm the **topic** in dialogue (one sentence). Record in `project.md` under `## Sketch topic`.
2. Ask for the **destination** — what “ready for design” looks like for this effort (spec, locked decision, or change). Record in `sketch-decisions.md` under `## Destination`.
3. Record provisional **Size** (small/medium/large); bias lower when unsure.
4. **Domain docs mode:** {{WITH_DOMAIN_DOCS}}
5. Ensure memory directory exists: `{{MEMORY_DIR}}`

## Existing domain documentation

{{DOMAIN_DOCS_STATUS}}

## Initialize

Create or update `project.md` with: session start time, topic, `with_domain_docs` flag, pointer to `{{SKETCH_DECISIONS_REL}}`.

Initialize `{{SKETCH_DECISIONS_REL}}` with the schema from `templates/sketch-protocol.md` (Destination, Size, Recommended scope, Decisions so far, Not yet specified, Scope expansion, Out of scope, Handoff notes).

Then begin step 2 — one question with a recommended answer inside the original ask.
