# Stage 1 — Investigation

Dispatch agents for deep investigation.

## Agent Dispatch

### Investigator (evidence gathering)
Explore the codebase and gather evidence:
- Read relevant code paths end-to-end
- Run existing tests, collect results
- Check git history for recent changes
- Collect error messages, stack traces, reproduction steps
- For bugfixes: follow `templates/systematic-debugging.md`

Write evidence to `.codex/forge-codex/memory/investigator.md`

### Architect (analysis lead)
Analyze the evidence using `templates/five-why-protocol.md`:
- For each issue/challenge, drill through up to 5 why-layers
- Pattern analysis and hypothesis testing at each layer
- Record evidence at every layer
- Stop at an actionable root cause
- For features: use `templates/brainstorming.md` for requirements exploration

Write findings to `.codex/forge-codex/memory/investigation.md`
