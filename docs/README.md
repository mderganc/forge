# Forge documentation

User-facing guides for installing and running Forge workflows. Internal design notes live under `docs/plans/` and `docs/evaluations/` (not maintained as product docs).

## Getting started

| Doc | Audience |
|-----|----------|
| [../README.md](../README.md) | Install, commands, workflow overview |
| [../integrations/README.md](../integrations/README.md) | Cursor / Claude / Codex install layout |
| [../integrations/spec/commands.json](../integrations/spec/commands.json) | All 14 CLI workflows |

## Feature guides

| Doc | Topic |
|-----|--------|
| [graphify.md](graphify.md) | Knowledge graph: refresh, hooks, ship-time banner, CI flags |
| [structural-quality.md](structural-quality.md) | knip / madge / pyscn / skylos probes in code-review and evaluate |
| [sessions.md](sessions.md) | Parallel session directories under `.forge/sessions/` |
| [environment.md](environment.md) | `FORGE_*` environment variables |

## Contributors and agents

| Doc | Topic |
|-----|--------|
| [../AGENTS.md](../AGENTS.md) | Orchestration contracts, state lifecycle, diagnose sidecars |
| [../CLAUDE.md](../CLAUDE.md) | Graphify rules for this repo |
| [audit/documentation-audit-2026-06.md](audit/documentation-audit-2026-06.md) | Doc drift matrix (2026-06) |

## Internal (do not add to README workflows)

| Doc | Topic |
|-----|--------|
| [studio.md](studio.md) | Forge Studio localhost UI (design/plan gates) |
| [skylos-triage.md](skylos-triage.md) | Skylos probe notes |
| `plans/`, `evaluations/` | Historical plans and skill evaluations |

## Diagnose templates

| Doc | Topic |
|-----|--------|
| [../templates/diagnose-feedback-loop.md](../templates/diagnose-feedback-loop.md) | Repro / feedback loop before 5 Whys |
| [../templates/diagnose-execution-playbooks.md](../templates/diagnose-execution-playbooks.md) | Technique playbooks |
