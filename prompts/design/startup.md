# forge-codex Design — Startup

{{DEVELOP_NO_EDIT_POLICY}}

## What design is for

**Before design:** If intent is still fuzzy (problem shape, constraints, terminology, open decisions), run **`forge sketch`** first. Sketch writes `sketch-decisions.md`; design does **not** replace that step.

**Design is a collaborative skill.** Work **with** the human in a back-and-forth rhythm. The **recommended path** is the user's original ask (see `templates/scope-size-model.md`). Still surface **opportunities** and “exciting vs adequate” ideas — but label them **Scope expansion (optional — not recommended)** unless the user opts in. Invent multiple solution directions **within Recommended scope** before anyone commits to code or docs. For **medium/large** scope, design ends with a **named design spec** at `docs/forge/specs/YYYY-MM-DD-<slug>-design.md` (see spec gate on step 6). Scale ceremony to size: **trivial/small** stays lean (no formal spec, fewer candidates). Prefer short rounds of questions, options, and reactions over dumping long monologues.

At each continuation gate: “Does this match the **original ask**?” “Any Scope expansion you want to opt into?” If one unresolved logic/state or UI-shape question remains hard to settle, **offer** the future `forge:prototype` (not yet invokable — `docs/forge/prototype-skill-stub.md`).

## Dependency Detection

**Check beads:**
Run: bd doctor (or check beads skill availability)
If unavailable -> warn user, record in project.md: "beads: unavailable"
If available -> check .beads/ exists, run bd init if not -> record: "beads: available/initialized"

**Check agent teams:**
If agent teams unavailable -> inform user:
  "Agent teams required. Add to settings: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
  Stop.

## Autonomy Level
{{AUTONOMY_INSTRUCTIONS}}

## Session Resume
If {{MEMORY_DIR}}/project.md exists:
  -> Read all memory files, check stage markers
  -> Find earliest incomplete stage
  -> Report and resume

## Initialize
Create {{MEMORY_DIR}}/ directory and project.md with feature name, timestamps, dependencies, autonomy.
