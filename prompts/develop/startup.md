# forge-codex Develop — Startup

{{DEVELOP_NO_EDIT_POLICY}}

## What develop is for

**Develop is a collaborative skill.** Work **with** the human in a back-and-forth rhythm: surface **opportunities** (not only problems), **brainstorm requirements** before locking scope, and **invent** multiple solution directions before anyone commits to code or docs. The scripted steps exist to **structure** that dialogue—not to replace it. Prefer short rounds of questions, options, and reactions over dumping long monologues.

At each continuation gate, welcome refinements: “Does this match what you’re trying to achieve?” “What are we missing?” “What would make this exciting vs merely adequate?”

**Phase todos:** When the orchestrator prints **Create Phase Todos** JSON, if a **SESSION OPT-IN** block appears above it on step 1, resolve opt-in with the user **before** mirroring todos (`update_plan` / plan steps). Then mirror the JSON before other work, same as other forge skills.

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
