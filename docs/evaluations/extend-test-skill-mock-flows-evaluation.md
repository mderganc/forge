---
title: Pre-implementation evaluation — Extend forge:test with mock-flows mode
project: forge-codex
date: 2026-05-07
plan: /home/matt/.claude/plans/i-m-having-some-issues-composed-hedgehog.md
mode: pre
status: addressed
---

# Evaluation: Extend forge:test with mock-flows mode

## Summary

Pre-implementation review of a plan to add `--mode flows` to the `forge:test` skill. The skill would author end-to-end mock flows in four styles (scenario / BDD / HTTP-replay / workflow-dry-run), recommend the best fit from project signals, scaffold + run + report. Initial draft surfaced 43 findings across feasibility, completeness, codebase alignment, and risk dimensions. The plan has been revised in-place to address every finding (see "Conclusion"); no findings remain open.

## Findings (initial)

### Critical (3)
- **F12** — Quality criteria enforced only at report (step 7), wasting authoring effort. *Resolution: progressive gating at scaffold (step 4) and authoring (step 5).*
- **F13** — Recommendation sidecar malformed-input handling unspecified. *Resolution: `sys.exit(1)` on parse failure; never falls back to a default type.*
- **F33** — Fix 3 needs the fixture project as a hard prereq. *Resolution: new Fix 0 — `tests/fixtures/mock-flows-target/` lands first.*

### Warnings (~30) — addressed via:
- **Detection ladder + confidence scores** (F1, F7, F39): entry-point ladder UI > HTTP > CLI > module; pytest-only v1 with confidence; `--framework` / `--entry-point` overrides surface in step-1 prompt.
- **Project-discovered roles, single-role default** (F2, F19, F35): role discovery probes Django Groups / Casbin / Cerbos / yaml; falls back to `{anonymous}` with criterion-3 waiver when nothing found; explicit single-role opt-out in scope.
- **Test-DB detection** (F3): `_detect_test_layout` returns `test_db ∈ {testcontainers, pytest-postgresql, sqlite, none}`; recommendation downgrades scenario / workflow-dryrun fitness when `none`.
- **Fixture project** (F4): Fix 0 ships `tests/fixtures/mock-flows-target/` (FastAPI + SQLite + roles.yaml).
- **HTTP-replay clarifications** (F5): unauthorized role uses live response (no cassette); recording workflow documented in catalog.
- **Sidecar discipline** (F6, F28): parallel `_ingest_recommendation_sidecar` function with distinct schema; step-numbered filename `.test-recommendation-step2.json`.
- **Matrix dimension fix** (F8): role × failure-path (not role × data-pack); data packs parametrize *within* a role-keyed run.
- **Legacy state compat** (F14): all new `state.custom` reads use `.get(key, default)`.
- **Catalog schema validation** (F15, F31): split into `templates/mock-flow-types.md` (prose) + `scripts/test/flow_types.py` (typed `FLOW_TYPES`); regression test asserts schema completeness.
- **Scenario-index parser** (F16, F40): defined columns; parse-validate-merge-rewrite; backup at `.codex/forge-codex/memory/scenario-index.bak`; abort on parse failure.
- **Smoke harness in repo** (F17): relocated `/tmp/forge-smoke/smoke.py` → `scripts/smoke.py`, documented + CI-eligible.
- **Standalone flows mode** (F18): inline scope-via-user-questions when no handoff present.
- **Atomic delivery** (F20, F38): startup feature-check verifies all 7 prompt files exist; partial deploy emits clear error + exit 1.
- **Project-specific data realism** (F21): scope captures sample inputs; authoring uses them as templates for messy variants.
- **Sample-quality probes** (F37): byte-diff between data packs, assertion-set diff between roles, surfaced as findings if performative.
- **Cassette freshness** (F36): timestamp + 30-day warn / 90-day fail; `--re-record` flag.
- **Pre-mortem mitigations** (F34): catalog provenance line; override-logged stderr; catalog-regression test against fixture matrix.
- **Convention alignment** (F25, F26, F29, F32): single PHASE_NAMES + per-step branching; flat prompt names `prompts/test/flow_*.md`; project-discovered scenarios dir.

### Suggestions (~9) — addressed via:
- **Mode-on-resume guard** (F9): abort with stderr when saved mode ≠ requested mode.
- **Deterministic double-run** (F10): authoritative gate at step 6, grep is pre-filter.
- **Workflow-dryrun fitness gating** (F11): score 0 unless orchestrator pattern detected.
- **Adoption metric** (F22): `usage-stats.json` append at step 7; `FORGE_NO_USAGE_STATS=1` opts out.
- **Doc completeness** (F23, F24, F43): per-key state-lifecycle table in AGENTS.md; per-mode lead in SKILL.md.
- **Build-next-command consistency** (F30): all next-cmd emission goes through shared helper.
- **Conftest fixture** (F42): `pytest_fixture_project` factory in `tests/conftest.py`.
- **Wave-1 parallelization** (F41): Fix 2 ∥ Fix 5 declared as parallel.

## Dismissed Items

None. All 43 findings were addressed in the plan revision.

## Conclusion

The revised plan is ready for implementation. Key improvements from the initial draft:

1. **New Fix 0** lands a fixture project before any verification work begins.
2. **Implementation waves** are explicit, with Fix 3 declared atomic to prevent partial-deploy crashes.
3. **Quality criteria are progressively gated** (scaffold → author → execute → report) instead of audited only at the end.
4. **Detection helpers return confidence + structured fields** for entry point, test DB, roles — not just framework name.
5. **Role matrix is project-discovered** with a sane fallback, not a fixed 6-tuple.
6. **Catalog format is split** — prose for humans, typed Python for the recommendation logic.
7. **Sidecar discipline is consistent** — step-numbered filename, fail-loud on malformed input, schema validation.
8. **Verification expanded from 13 to 27 checks** with each finding mapped to a concrete test.

Recommended next step: invoke `forge:implement` against the revised plan.
