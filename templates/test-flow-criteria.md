# Mock Flow Quality Criteria

Canonical rubric for `forge test --mode flows`. Every flow must satisfy all eight criteria; gates in `scripts/test/test_flows.py` enforce subsets at scaffold (2–4), authoring (5–7), and report (1–8).

| # | Criterion | Summary |
|---|-----------|---------|
| 1 | **Realistic scenarios** | End-to-end user journeys (setup → process → review → export), not synthetic CRUD pings. |
| 2 | **Representative test data** | Fixtures under `fixtures/data-packs/{clean,messy,edge-cases,duplicates}/` with meaningful variation. |
| 3 | **User roles and permissions** | Project-discovered RBAC (Django Groups, Casbin, Cerbos, YAML). Collapse to `{anonymous}` when none found; audit waives criterion 3. |
| 4 | **Full process execution** | Entry-point ladder: UI > HTTP > CLI > module. Never import SUT internals and call functions directly. |
| 5 | **Outcome validation** | Assertions cover ≥ 2 of {response payload, DB row, log output, file, audit trail, notification}. |
| 6 | **Minimal mocking** | Mock only externals (email, paid APIs, non-deterministic LLM, slow jobs). Do not mock core logic, DB, permissions, or ingestion when a test DB exists. |
| 7 | **Failure and edge handling** | ≥ 1 failure-path assertion (bad input, missing permission, partial failure, retry behavior). |
| 8 | **Repeatable regression structure** | Deterministic inputs and outputs; no live randomness/time unless patched or fixed. |

**Related docs:** `templates/mock-flow-types.md` (four flow styles), `prompts/test/flow_*.md` (phase checklists).
