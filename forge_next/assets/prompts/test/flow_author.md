# Phase 5: Mock Authoring

**Lead: Developer**

Fill scaffold with data packs, role-parameterized assertions, failure paths, and outcome validation (RED phase — test should fail until feature exists).

## Gate failures (if re-prompted)

{{AUTHORING_GATE_FAILURES}}

## Checklist

- [ ] Read **`templates/test-flow-criteria.md`** — acceptance bar for criteria 1–8.
- [ ] **Data packs:** populate `clean/`, `messy/`, `edge-cases/`, `duplicates/` with README per variant (from step 3 sample inputs).
- [ ] **Roles:** parametrize via conftest or BDD steps; distinct assertion sets per role; ≥ 2 outcome surfaces per test.
- [ ] **Failure paths:** ≥ 1 test exercising a scoped failure scenario (bad input, forbidden role, etc.).
- [ ] **Entry point:** HTTP `TestClient`, CLI `subprocess`, etc. — never direct internal imports.
- [ ] **External mocks only:** stub services listed in scope; record in `authoring_results.external_mocks`.
- [ ] **Determinism:** patch or fix random, time, UUID; sort unordered collections before assert.
- [ ] Run pytest on the flow file — expect **FAIL** (RED). Do not implement the feature here.
- [ ] Populate `state.custom` with `authoring_results` (outcome surfaces, external mocks) for the orchestrator gate.
