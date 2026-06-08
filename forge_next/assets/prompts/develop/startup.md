# forge-codex Design — Startup

{{DEVELOP_NO_EDIT_POLICY}}

## What design is for

**Before design:** If intent is still fuzzy (problem shape, constraints, terminology, open decisions), run **`forge sketch`** first. Sketch writes `sketch-decisions.md`; design does **not** replace that step.

**Design is a collaborative skill.** Work **with** the human in a back-and-forth rhythm: surface **opportunities** (not only problems), **brainstorm requirements** before locking scope, and **invent** multiple solution directions before anyone commits to code or docs. For **medium/large** scope, design ends with a **named design spec** at `docs/forge/specs/YYYY-MM-DD-<slug>-design.md` (see spec gate on step 6). The scripted steps exist to **structure** that dialogue—not to replace it. Prefer short rounds of questions, options, and reactions over dumping long monologues.

At each continuation gate, welcome refinements: “Does this match what you’re trying to achieve?” “What are we missing?” “What would make this exciting vs merely adequate?”

**Phase todos:** When the orchestrator prints **Create Phase Todos** JSON, if a **SESSION OPT-IN** block appears above it on step 1, resolve opt-in with the user **before** mirroring todos (`update_plan` / plan steps). Then mirror the JSON before other work, same as other forge skills.

**Graphify:** If a **GRAPHIFY** block appears in step output, follow `templates/graphify-contract.md` **before** search tools or bulk file reads.

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
If .codex/forge-codex/memory/project.md exists:
  -> Read all memory files, check stage markers
  -> Find earliest incomplete stage
  -> Report and resume

## Initialize
Create .codex/forge-codex/memory/ directory and project.md with feature name, timestamps, dependencies, autonomy.
