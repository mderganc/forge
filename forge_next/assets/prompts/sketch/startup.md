# forge sketch — Startup

{{SKETCH_NO_EDIT_POLICY}}

## What sketch is for

**Sketch organizes your thoughts before design.** Use it when intent is fuzzy: problem framing, constraints, terminology, and open decisions — **not** when you need investigation, solution options, or a design spec file.

- **Sketch** → intent and decision log (`sketch-decisions.md`)
- **Design** → evidence, solution brainstorming, **`docs/forge/specs/...-design.md`** (medium/large scope)

If the user has not run sketch and the idea is still messy, recommend **`forge sketch`** before **`forge design`**.

## Setup

1. Confirm the **topic** in dialogue (one sentence). Record it in `project.md` under `## Sketch topic`.
2. **Domain docs mode:** {{WITH_DOMAIN_DOCS}}
   - To enable glossary/ADR writes on step 1, the launcher was run with `--with-domain-docs`.
3. Ensure memory directory exists: `{{MEMORY_DIR}}`

## Existing domain documentation

{{DOMAIN_DOCS_STATUS}}

## Graphify

If `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` before broad codebase search (optional for sketch).

## Initialize

Create or update `project.md` with: sketch session start time, topic, `with_domain_docs` flag, and a pointer to `{{SKETCH_DECISIONS_REL}}`.
