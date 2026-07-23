# Phase 5: Mock Authoring

**Lead: Developer**

Fill scaffold with data packs, role-parameterized assertions, failure paths, and outcome validation (RED phase — test should fail until feature exists).

## Gate failures (if re-prompted)

{{AUTHORING_GATE_FAILURES}}

## Checklist

- [ ] Read **`templates/test-flow-criteria.md`** — acceptance bar for criteria 1–8.
- [ ] **Data packs:** populate budgeted packs only (`clean/` minimum; add `messy/` / `edge-cases/` / `duplicates/` when scope has matching failure_paths — smoke → clean + at most one edge). README per created variant.
- [ ] **Roles:** parametrize via conftest or BDD steps when roles > 1; distinct assertion sets per role; ≥ 2 outcome surfaces per test (single-role smoke may use one primary surface + one failure if scoped).
- [ ] **Failure paths:** ≥ 1 test when scope lists failure_paths; smoke with none may omit.
- [ ] **Entry point:** HTTP `TestClient`, CLI `subprocess`, etc. — never direct internal imports.
- [ ] **External mocks only:** stub services listed in scope; record in `authoring_results.external_mocks`.
- [ ] **Determinism:** patch or fix random, time, UUID; sort unordered collections before assert.
- [ ] Run pytest on the flow file — expect **FAIL** (RED). Do not implement the feature here.
- [ ] Populate `state.custom` with `authoring_results` (outcome surfaces, external mocks) for the orchestrator gate.
