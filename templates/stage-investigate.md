# Stage 1 — Investigation

## Purpose
Deep investigation using the five-why protocol to identify root causes (bugfix/refactor) or core technical challenges and requirements gaps (features).

## Lead Agent
**Architect** — conducts the five-why analysis

## Superpowers Integration
- Bugfix tasks: invoke `superpowers:systematic-debugging` if available
- Feature tasks: invoke `superpowers:brainstorming` if available

## PM Actions

### 1. Assign Investigation

Send to Architect:

> **Task: Investigate [task-type] — [feature/bug description]**
>
> Read `.codex/forge-codex/memory/project.md` for requirements, task type, and scope.
> Read AGENTS.md and any project rules for conventions.
>
> Conduct five-why root cause analysis following `templates/five-why-protocol.md`:
> - For each issue/challenge, drill through up to 5 why-layers
> - Pattern analysis and hypothesis testing at each layer
> - Record evidence at every layer
> - Stop at an actionable root cause
>
> Write findings to `.codex/forge-codex/memory/investigation.md`.
> Use Codex runtime conventions from `templates/codex-runtime.md`.
> Create beads issues for each finding and root cause (if beads available).
> Cross-reference beads IDs in memory per `templates/memory-protocol.md`.

### 2. Run Review Loop

Per `templates/review-loop.md`:

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Architect | Did I stop too early? Did I validate every hypothesis? |
| Cross-review | QA Reviewer | Are findings reproducible? Is evidence concrete? Coverage gaps? |
| Critic challenge | Critic | What assumptions are untested? What if the opposite is true? What's overlooked? |
| PM validation | PM | Complete against task type checklist? All beads IDs present? |

Loop until all four pass cleanly in the same round.

### 3. Beads Tracking

For each finding:
bd create "[finding]" -t bug/task --parent [epic-id] -l "finding,stage-1"

For each root cause:
bd create "[root cause]" -t task --parent [epic-id] -l "root-cause,stage-1"
bd dep add [root-cause-id] [finding-id] --type discovered-from

### 4. Stage Gate

| Autonomy | Behavior |
|----------|----------|
| Level 1 | Present investigation summary to user, ask for approval |
| Level 2 | Auto-proceed, log summary to project.md |
| Level 3 | Auto-proceed, log summary to project.md |

### 5. Git Checkpoint

git add .codex/forge-codex/ && git commit -m "workflow: Stage 1 complete — investigation"

Record in project.md: `## Stage 1: COMPLETE [timestamp]`
