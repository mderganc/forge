# Workflow skill runtime (shared)

Read this once per skill session. Skill-specific args and gates stay in each `skills/<name>/SKILL.md`.

## Delegation

Invoking a `forge:*` workflow skill authorizes the agent dispatch that skill requires. Do not ask the user to separately delegate or spawn sub-agents. Full contract: [AGENTS.md](../AGENTS.md) § Forge Skill Delegation Contract.

## Graphify

See [templates/graphify-contract.md](graphify-contract.md). Refresh at **ship** only (`forge ship --step 1`). Optional during skills: read `graphify-out/GRAPH_REPORT.md` or use `graphify query` / `path` / `explain`.

## Progress and continuation

The orchestrator prints a **Create Phase Todos** JSON block each step — mirror it immediately (e.g. `update_plan`). On step 1, complete **SESSION OPT-IN** first if shown.

Multi-step skills: do not stop between phases. See [templates/codex-runtime.md](codex-runtime.md) for continuation protocol and parallel dispatch.

## Execution order

**Run the orchestrator first** — `forge <skill> --step N` — and follow its output. Do not explore or analyze before running the script.

## Handoff

Final step emits a **WORKFLOW HANDOFF** menu. Defaults and alternatives: `scripts/shared/skill_chain.py` via `build_skill_handoff_menu()`.

## Routing

When unsure which skill to run next, see [AGENTS.md](../AGENTS.md) § Process-first skill choice.
