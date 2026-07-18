# Workflow skill runtime (shared)

Read this once per skill session. Skill-specific args and gates stay in each `skills/<name>/SKILL.md`.

## Delegation

Invoking a `forge:*` workflow skill authorizes the agent dispatch that skill requires — **except `forge:sketch`** (1:1 dialogue only) **and `forge:ux-review`** (1:1 real-browser product UX audit) — neither requires a Forge agent team or Task/sub-agent spawn unless the user asks. For all other workflow skills, do not ask the user to separately delegate or spawn sub-agents.

Before spawning, read **`templates/forge-agent-roster.md`**. Use only roster roles (e.g. **Architect**, **Investigator**) — never invent composites like `backend-architect`. Full contract: [AGENTS.md](../AGENTS.md) § Forge Skill Delegation Contract.

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

## Simplicity (YAGNI)

- **YAGNI:** Build only what the current task or approved scope requires. No speculative APIs, config flags, abstraction layers, or "future-proof" hooks unless explicitly in scope.
- **Smallest correct change:** Prefer the shortest diff that satisfies acceptance criteria. A focused 5-line fix beats a 100-line refactor.
- **One-liners where readable:** Prefer inline expressions (ternaries, comprehensions, small lambdas, guard clauses) over one-off helpers, wrapper classes, or new files—when clarity is preserved.
- **No premature generalization:** One caller → implement at the call site; three similar call sites → then extract.
- **When in doubt:** Ship the simpler option; escalate breadth to design/plan, not implementation.

## Structural quality (build charter)

While designing, planning, and implementing, follow **`templates/structural-build-charter.md`**: complexity budget, no clones, no dead arms, no new cycles, no speculative exports. jscn/pyscn (and related probes) **verify** those rules later — they are not the first time agents should hear them.
