# Phase 7: Report + Handoff

**Lead: Doc-writer**

Audit the flow, run sample-quality probes, update memory, and write handoff.

## Checklist

- [ ] Read **`templates/test-flow-criteria.md`** — mark each criterion **met** | **partial** | **missing** in `state.custom["criteria_audit"]`.
- [ ] **Probe A — data-pack byte-diff:** compare `clean/` vs `messy/`, `edge-cases/`, `duplicates/` (flag if < 5% — performative packs).
- [ ] **Probe B — role-matrix assertion diff:** distinct assertion sets per role (flag if identical across roles).
- [ ] **Pytest reliability:** function-scoped fixtures with teardown, `tmp_path`, stable IDs on parametrized roles, no unpatched random/time/UUID.
- [ ] Append flow section to **`{{MEMORY_DIR}}/test-report.md`** (scope, files, criteria table, probe results, findings).
- [ ] Update **`tests/scenarios/README.md`** (or features equivalent) if parser allows — column format: feature | type | roles | failure paths | date | status.
- [ ] Write **`handoff-test.md`** with feature, flow type, status, next steps.
