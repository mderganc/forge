# forge-codex Develop — Startup

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
