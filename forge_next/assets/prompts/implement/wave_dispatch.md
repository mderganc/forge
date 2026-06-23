# Phase 3: Wave Dispatch

Dispatch agents for Wave {{CURRENT_WAVE}} of {{TOTAL_WAVES}}.

## Tasks in This Wave

{{WAVE_TASKS}}

## Instructions

For each task in the wave, dispatch the assigned agent with:

1. Task details from the plan file (path from handoff or `{{MEMORY_DIR}}/plans/`)
2. Branch name for their sub-branch
3. TDD instructions per `templates/tdd-protocol.md`:
   - Write failing test first
   - Verify it fails with expected error
   - Implement minimal code to pass
   - Verify all tests pass (new + existing)
   - **YAGNI:** Smallest diff; prefer one-liners where readable; no drive-by refactors
4. Cross-reference beads if available

Follow `templates/parallel-dispatch.md` for dispatch protocol.

## Sub-Branch Creation

For each task in this wave:
```
git checkout {{FEATURE_BRANCH_PATTERN}}
git checkout -b {{TASK_BRANCH_PATTERN}}
```

Branch guardrails:
- Keep all implementation/task branches under the selected conventional prefix (`{{BRANCH_PREFIX}}/...`).
- Do not invent or infer `forge/*` branch names.
- If a task sub-branch already exists, `git checkout` it instead of recreating.

## Agents to Dispatch

{{AGENT_LIST}}

## Blocker Protocol

If any agent reports a blocker during implementation:
1. Classify: missing dependency, unclear requirement, technical obstacle, external
2. Route to appropriate agent for resolution
3. Update plan if wave structure changes
4. Other agents in the wave continue unblocked

## Agent Lifecycle

Every agent dispatched in this wave must be closed via `close_agent` as soon as
it has reported its result (or the moment it is determined no longer useful —
e.g., redundant, blocked, or replaced). Do not advance to Wave {{CURRENT_WAVE}} + 1
with any agent from this wave still open. Codex enforces a concurrent-agent cap;
leaked sessions accumulate across waves and eventually block further dispatch.

See `templates/codex-runtime.md` → *Parallel work* for the spawn → wait →
capture → close pattern.
