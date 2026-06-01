# Skylos triage guide (Forge)

Skylos runs during **code-review / evaluate** Pass B (`FORGE_SKYLOS_AUDIT` optional). Treat output as **hints** — confirm with grep and tests before deleting code.

## Latest triage (2026-06-01)

| ID | Symbol | Verdict | Action |
|----|--------|---------|--------|
| Y1 | `write_report` (`scripts/shared/report.py`) | **Wired** | Used by `diagnostic_report.generate_structured_report` (`--format structured`); unit tests in `tests/test_report_module.py` |
| Y2 | `ReviewLoopState.is_clean` | **False positive** | Reserved stage-gate API |
| Y3 | `ReviewLoopState.reset_round` | **False positive** | Reserved stage-gate API |
| Y4 | `SkillState.get_review_loop` | **False positive** | Reserved; not wired to agents yet |
| Y5 | `SkillState.record_dispatch` | **False positive** | Reserved delegation tracking |
| Y6–Y8 | `cli.py` imports (`capture_human_output`, etc.) | **Alive** | Used via `forge_next/cli_dispatch.py`; re-exports on `cli` for tests |

## Policy

1. Do **not** bulk-delete from skylos JSON alone.
2. Grep for string references, `__all__`, and orchestrator re-exports.
3. Prefer **tests** or **wiring** over deletion for shared utilities (Y1).
4. Document reserved APIs in this file when skylos repeats on upgrade.

## Complexity (pyscn) companion list

See `.codex/forge/state/.structural-probes.json` pyscn findings P2–P8. Waves 1–7 refactored validators/installers/orchestrators; `cli.main` complexity resolved via `cli_dispatch.py`. P6–P7: `mece_tree_*` and `five_whys_*` helper modules.
