# Mock Flow Types

**Provenance:** v1 tuned against forge-codex repo + tests/fixtures/mock-flows-target/

This catalog describes the four supported mock-flow styles used by `forge:test --mode flows`. Each type serves different project contexts and team preferences. The recommendation phase scores all four against your project's signals and proposes the best fit with alternatives.

## Quality Criteria (8 total)

Every flow this skill produces must satisfy these criteria. Enforcement is **progressive**: criteria 2/3/4 gate the scaffold step; 5/6/7 gate the authoring step; 1/8 are audited at report.

1. **Realistic scenarios** — flows describe end-to-end user journeys (project setup, data upload, processing, review, export, sharing, permission changes), not synthetic CRUD pings.
2. **Representative test data** — fixtures include malformed files, edge cases, incomplete records, duplicate inputs, encoding/formatting issues, *and* well-formed control inputs. Lives under `<scope>/fixtures/data-packs/{clean,messy,edge-cases,duplicates}/` with a per-pack `README.md`.
3. **User roles and permissions matrix** — *project-discovered*, not a fixed list. The scope step reads role definitions from the SUT's RBAC config (Django Group, Casbin policy, Cerbos schema, Spring Security, custom). If no role model is detected, the matrix collapses to `{anonymous}` and the audit waives criterion 3 with explanation.
4. **Full process execution** — entry-point ladder: UI > HTTP API > CLI > module-level fallback. Scaffold step picks the highest-fidelity entry point; never imports the SUT's internal modules and calls functions directly.
5. **Outcome validation** — assertions cover ≥ 2 of {response payload, DB row, log output, generated file, audit-trail entry, side-channel notification}.
6. **Minimal mocking** — only mock what's truly external: email senders, paid third-party APIs, non-deterministic LLM calls, slow scheduled jobs. Do *not* mock core app logic, DB writes, permission checks, ingestion, retrieval, or exports — *when* the project has a seedable test DB. If no test-DB infrastructure exists, scenario / workflow-dryrun fitness drops and HTTP-replay takes priority.
7. **Failure and edge handling** — each flow file contains ≥ 1 failure-path assertion (bad input / missing permission / partial failure / conflicting data / retry-recovery behavior).
8. **Repeatable regression structure** — known inputs, deterministic expected outputs. Enforced with a **double-run check**: run the flow twice, diff outputs.

---

## Type 1: Scenario Script

**Description:** Pytest scenario files under `tests/scenarios/` that exercise a feature end-to-end with stubbed external services.

### When It Fits Best

- Project has a test database and can seed state quickly.
- Entry point is HTTP (FastAPI, Flask, Django) or CLI (Click, typer, argparse).
- Team prefers imperative, procedural test code over Gherkin syntax.
- Flows combine multiple user roles in a single test.
- Need fine-grained control over assertion surfaces (DB rows, logs, API responses in sequence).

### When It Doesn't Fit

- **No test DB.** Scenario flows rely on state mutations persisted to a seeded DB. Without test-DB infrastructure (pytest-postgresql, testcontainers, sqlite), scenarios score low on criterion 6 (minimal mocking) and criterion 8 (determinism). HTTP-replay is a better fit.
- **Only UI entry point available.** Scenarios assume programmatic entry (HTTP request, CLI command, module import). UI automation adds brittle dependencies (browser, Selenium/Playwright pre-installed). If your SUT has *only* UI, shift to HTTP-replay or reconsider the flow's scope.
- **Team mandates Gherkin specs.** Scenarios are procedural Python; if your organization requires business-readable feature files, use BDD instead.
- **Over-mocking risk.** If you find yourself stubbing core app logic, permission checks, or data retrieval to make the test pass, you're testing the mock, not the app. Symptoms: "the test passes but the feature is broken in staging." Revisit minimal mocking (criterion 6).

### Tooling Defaults

- **Framework:** pytest
- **Fixtures:** pytest's built-in `tmp_path`, custom `seeded_db` fixture (from `tests/conftest.py`)
- **Data:** CSV/JSON files under `<scenario_dir>/fixtures/data-packs/`
- **Assertion surfaces:** DB queries, response `status_code` + `.json()`, log capture via `caplog`

### File Layout

```
tests/scenarios/
├── test_data_upload.py          # Main scenario
├── conftest.py                  # Per-role fixtures
└── data_upload/
    ├── fixtures/
    │   └── data-packs/
    │       ├── clean/
    │       │   ├── valid.csv
    │       │   └── README.md
    │       ├── messy/
    │       │   ├── duplicates.csv
    │       │   ├── mixed_encoding.csv
    │       │   └── README.md
    │       ├── edge-cases/
    │       │   ├── empty.csv
    │       │   ├── oversized.csv
    │       │   └── README.md
    │       └── duplicates/
    │           ├── same_id_twice.csv
    │           └── README.md
    └── test_data_upload_admin.py    # Per-role variant
```

### Quality Criteria Fit

| # | Criterion | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Realistic scenarios | 9 | Scenario flows map directly to user journeys; suited to multi-step workflows |
| 2 | Representative test data | 9 | Data packs structure built-in; easy to vary and document per pack |
| 3 | User roles/permissions | 8 | Parameterized via fixtures; assertion sets vary by role |
| 4 | Full process execution | 10 | Hits HTTP/CLI/module entry points; no internal imports |
| 5 | Outcome validation | 9 | Multiple surfaces naturally available: DB state, response, logs, files |
| 6 | Minimal mocking | 8 | Test DB means real DB state; only stub truly external services |
| 7 | Failure/edge handling | 9 | Easy to add variants for error paths and edge cases |
| 8 | Repeatable regression | 10 | Fixed data packs, no randomness, deterministic DB |

### Example Skeleton

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.parametrize("role,expected_status", [
    ("admin", 200),
    ("member", 403),
])
def test_upload_flow_complete_journey(seeded_db, role, expected_status):
    """End-to-end: user uploads file, system validates, stores, exports report."""
    client = TestClient(app)
    
    # Setup: seed test DB with user roles
    admin_user = seeded_db.query(User).filter_by(role=role).first()
    
    # Action 1: upload
    resp = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {admin_user.token}"},
        files={"file": ("data.csv", open("fixtures/data-packs/clean/valid.csv"))}
    )
    
    # Check: response
    assert resp.status_code == expected_status
    if expected_status == 200:
        # Check: DB persisted
        record = seeded_db.query(Upload).filter_by(user_id=admin_user.id).first()
        assert record is not None
        
        # Action 2: generate report
        resp2 = client.get(f"/reports/{record.id}")
        assert resp2.status_code == 200
        # Check: file created
        assert Path(f"exports/{record.id}.pdf").exists()
```

### Data-Pack Template

```
<scenario_dir>/fixtures/data-packs/
├── clean/
│   ├── valid.csv            (well-formed, happy-path data)
│   └── README.md            (describes: purpose, assumptions, expected outcome)
├── messy/
│   ├── duplicates.csv       (same ID twice)
│   ├── mixed_encoding.csv   (UTF-8 + Latin-1 mixed)
│   └── README.md
├── edge-cases/
│   ├── empty.csv            (zero rows)
│   ├── oversized.csv        (1M rows)
│   └── README.md
└── duplicates/
    ├── same_id_twice.csv    (focuses on duplicate handling)
    └── README.md
```

---

## Type 2: BDD Feature + Steps

**Description:** Gherkin `.feature` files plus step definitions (pytest-bdd primary, behave fallback) that read as acceptance criteria.

### When It Fits Best

- Team or stakeholders require business-readable acceptance criteria (Gherkin).
- Project already has Gherkin feature files or step libraries.
- Multiple teams (QA, product, dev) need to collaboratively author and review tests.
- Flows map clearly to "Given-When-Then" narratives.
- Test DB exists and test setup is straightforward.

### When It Doesn't Fit

- **No existing Gherkin infrastructure.** If you're creating your first `.feature` files from scratch, expect a ramp-up cost. The prose is more readable to stakeholders, but the step-definition code is less flexible than imperative Python.
- **Complex state transitions or multi-step retry logic.** Gherkin is linear. Complex orchestration (e.g., "retry the upload 3 times, then escalate to admin") quickly becomes verbose in feature syntax. Scenarios are more natural for this.
- **No step library.** If your team hasn't invested in shared step definitions (login, seed DB, assert on response), BDD overhead is high.
- **Low test-DB confidence.** Steps may be harder to debug when test data is implicit in the feature file.

### Tooling Defaults

- **Framework:** pytest-bdd (default) or behave (fallback)
- **Fixtures:** step definitions in `steps/` dir; shared DB fixtures in `conftest.py`
- **Data:** embedded in "Given" steps or referenced from `fixtures/data-packs/`
- **Assertion surfaces:** "Then" steps check DB, response payload, logs via Python assertions

### File Layout

```
tests/features/
├── data_upload.feature          # Gherkin scenarios
├── conftest.py                  # Feature-level fixtures
├── steps/
│   ├── step_auth.py            # "Given I am logged in as [role]"
│   ├── step_upload.py          # "When I upload [file]"
│   └── step_assertions.py      # "Then the DB contains [record]"
└── data_upload/
    ├── fixtures/
    │   └── data-packs/
    │       ├── clean/
    │       │   ├── valid.csv
    │       │   └── README.md
    │       ├── messy/
    │       │   └── ...
    │       ├── edge-cases/
    │       │   └── ...
    │       └── duplicates/
    │           └── ...
    └── conftest.py
```

### Quality Criteria Fit

| # | Criterion | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Realistic scenarios | 10 | Gherkin scenarios are inherently narrative; suited to user-facing workflows |
| 2 | Representative test data | 8 | Data packs referenced in "Given" steps; less direct than scenarios |
| 3 | User roles/permissions | 8 | Parameterized via Scenario Outlines; step definitions vary per role |
| 4 | Full process execution | 9 | Steps call HTTP endpoints / CLI; no internal module imports |
| 5 | Outcome validation | 8 | "Then" steps assert on multiple surfaces (DB, response, logs) |
| 6 | Minimal mocking | 7 | Depends on step-definition discipline; easy to over-mock in shared steps |
| 7 | Failure/edge handling | 8 | Additional scenarios (e.g., "Scenario: upload fails with duplicate") cover variants |
| 8 | Repeatable regression | 9 | Deterministic if step definitions are pure and data packs are fixed |

### Example Skeleton

```gherkin
# data_upload.feature
Feature: Data upload and report generation
  As a user
  I want to upload a CSV file
  So that the system processes and generates a report

  @happy-path
  Scenario Outline: Successful upload by <role>
    Given I am logged in as "<role>"
    And the database is seeded
    When I upload the file "fixtures/data-packs/clean/valid.csv"
    Then the response status is <status>
    And the database contains a new Upload record
    And a report file is generated
    
    Examples:
      | role   | status |
      | admin  | 200    |
      | member | 200    |
      | viewer | 403    |

  @failure-path
  Scenario: Upload fails on duplicate ID
    Given I am logged in as "admin"
    And an Upload with ID "12345" already exists
    When I upload the file "fixtures/data-packs/duplicates/same_id_twice.csv"
    Then the response status is 409
    And the database is unchanged
```

```python
# steps/step_upload.py
from pytest_bdd import when, then

@when('I upload the file "<filename>"')
def upload_file(client, filename, user_context):
    with open(filename) as f:
        resp = client.post(
            "/upload",
            headers={"Authorization": f"Bearer {user_context['token']}"},
            files={"file": f}
        )
    user_context["response"] = resp

@then("the database contains a new Upload record")
def check_db_record(seeded_db, user_context):
    record = seeded_db.query(Upload).order_by(Upload.id.desc()).first()
    assert record is not None
```

### Data-Pack Template

Same as Scenario (see above).

---

## Type 3: HTTP/API Replay

**Description:** VCR-style cassettes (vcrpy / pytest-recording) that replay request/response traces as regression checks.

### When It Fits Best

- Project has HTTP endpoints (REST, GraphQL, RPC) as the primary surface.
- No test-DB infrastructure or schema is complex/expensive to set up.
- External API calls are frequent and need to be mocked via recorded responses.
- Team wants to test the exact HTTP contract (status codes, payload shape, headers).
- Fast regression checks matter (replay is deterministic and fast).

### When It Doesn't Fit

- **Core business logic in the database.** HTTP-replay captures request/response but not DB state. If your flow's correctness depends on verifying a database transaction (e.g., "user's balance decreased by $50"), HTTP-replay alone won't catch bugs. Scenarios or BDD are more suitable.
- **Complex authorization logic per role.** HTTP-replay cassettes are recorded once per auth scenario. Adding a new role requires recording a new cassette, which is manual and error-prone. Scenarios/BDD are more flexible here.
- **Failure paths and edge cases hard to pre-record.** If your edge case is "what if the external API returns a 500 and we retry?", you must record the cassette in that state. For synthetic edge cases (invalid input, permission denied), consider whether a pre-recorded cassette is the right abstraction.
- **Cassettes go stale.** API contracts change. Cassettes > 90 days old may be recording a deprecated API. Enforcement (criterion 8) includes freshness checks.

### Tooling Defaults

- **Framework:** pytest with vcrpy or pytest-recording
- **Cassettes:** YAML or JSON files under `tests/cassettes/data/<scope>/` (one per recorded session)
- **Recording:** `--re-record` flag refreshes cassettes; requires live test API access
- **Matching:** cassettes matched by HTTP method, URL, headers; body is optional
- **Assertion surfaces:** response status, JSON payload, cassette metadata

### File Layout

```
tests/cassettes/
├── test_get_reports.py          # Main test file
├── conftest.py
└── data/
    └── get_reports/
        ├── data-packs/
        │   ├── clean/
        │   │   ├── valid_auth_header.yaml  (recorded cassette, "clean" variant)
        │   │   └── README.md
        │   ├── messy/
        │   │   ├── missing_auth_header.yaml
        │   │   └── README.md
        │   ├── edge-cases/
        │   │   ├── expired_token.yaml
        │   │   └── README.md
        │   └── duplicates/
        │       ├── duplicate_request.yaml
        │       └── README.md
        └── conftest.py
```

### Quality Criteria Fit

| # | Criterion | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Realistic scenarios | 7 | Good for API-driven workflows; limited to HTTP contract |
| 2 | Representative test data | 6 | Cassettes capture real payloads; less control over data variation |
| 3 | User roles/permissions | 6 | Can replay different auth headers; limited scope for authz testing |
| 4 | Full process execution | 10 | Exact HTTP record/replay; no abstraction loss |
| 5 | Outcome validation | 7 | Response payload validated; limited DB or side-effect visibility |
| 6 | Minimal mocking | 9 | No mocking needed if cassettes are replayed as-is |
| 7 | Failure/edge handling | 5 | Hard to add new failure paths; must pre-record or mock |
| 8 | Repeatable regression | 8 | Cassette replay is deterministic; requires freshness checks |

### Example Skeleton

```python
import pytest
from pytest_recording import record

@record("get_reports.yaml")
def test_get_reports_admin():
    """Replay recorded GET /reports response for admin user."""
    client = TestClient(app)
    resp = client.get(
        "/reports",
        headers={"Authorization": "Bearer admin-token"}
    )
    assert resp.status_code == 200
    assert "id" in resp.json()[0]

@record("get_reports_unauthorized.yaml")
def test_get_reports_no_auth():
    """Replay recorded 401 Unauthorized response."""
    client = TestClient(app)
    resp = client.get("/reports")
    assert resp.status_code == 401
```

### Data-Pack Template

```
tests/cassettes/data/<scope>/
├── clean/
│   ├── valid_request.yaml       (successful request, canonical response)
│   └── README.md
├── messy/
│   ├── missing_header.yaml      (invalid request, error response)
│   ├── malformed_json.yaml      (garbled payload)
│   └── README.md
├── edge-cases/
│   ├── empty_list.yaml          (valid request, empty results)
│   ├── slow_response.yaml       (valid request, 10-second latency)
│   └── README.md
└── duplicates/
    ├── same_request_twice.yaml  (duplicate request in sequence)
    └── README.md
```

---

## Type 4: Workflow / Orchestrator Dry-Run

**Description:** Harness that stubs each step of a multi-step workflow and asserts state transitions (smoke-test pattern).

### When It Fits Best

- Project has an orchestrator pattern: queue worker, state machine, multi-step UI wizard, CI/CD pipeline, multi-stage approval flow.
- Flows naturally decompose into discrete steps that can be tested in isolation and in sequence.
- Team wants to verify the entire workflow lifecycle (start → step 1 → step 2 → ... → completion).
- Early termination or retry paths are critical to test.
- Test DB exists to seed initial state and verify final state.

### When It Doesn't Fit

- **No orchestrator pattern.** If your codebase has no state machine, queue worker, or multi-step workflow, workflow-dryrun will score 0 on the "needs_orchestrator_pattern" gate and recommendation will not propose it. Re-scope to a simpler flow or choose a different type.
- **External service dependencies are mandatory.** If each step depends on a real external API (Stripe, Slack, email), you'll find yourself recording many mocks. HTTP-replay or actual integration testing may be better.
- **Workflow is UI-only.** Dry-runs assume a programmatic harness (Python queue, state machine library, orchestrator SDK). UI-driven workflows need Selenium/Playwright + scenario scripts.

### Tooling Defaults

- **Framework:** pytest with a workflow harness (custom or via orchestrator SDK)
- **Mocking:** Mock only the step workers; use the real orchestrator + test-DB state
- **Data:** seed initial state from `fixtures/data-packs/`; assert final state after each step
- **Assertion surfaces:** workflow state, step outputs, DB records, side-effect flags

### File Layout

```
tests/orchestration/
├── test_approval_workflow_dryrun.py      # Main workflow test
├── harness_approval_workflow.py          # Orchestrator harness
└── approval_workflow/
    ├── fixtures/
    │   └── data-packs/
    │       ├── clean/
    │       │   ├── valid_submission.json
    │       │   └── README.md
    │       ├── messy/
    │       │   ├── incomplete_form.json
    │       │   └── README.md
    │       ├── edge-cases/
    │       │   ├── extremely_large_amount.json
    │       │   └── README.md
    │       └── duplicates/
    │           ├── same_id_twice.json
    │           └── README.md
    └── conftest.py
```

### Quality Criteria Fit

| # | Criterion | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Realistic scenarios | 9 | End-to-end multi-step journeys; natural for workflow testing |
| 2 | Representative test data | 8 | Initial state varied per data pack; assertions per step |
| 3 | User roles/permissions | 8 | Parameterized across workflow steps; assertion sets vary |
| 4 | Full process execution | 8 | Orchestrator harness; not direct module calls |
| 5 | Outcome validation | 9 | State transitions verified per step; DB state + side effects |
| 6 | Minimal mocking | 8 | Stub step workers; exercise core orchestration logic |
| 7 | Failure/edge handling | 9 | Natural to test retry paths, partial failures, rejection states |
| 8 | Repeatable regression | 10 | Deterministic step orchestration with fixed data |

### Example Skeleton

```python
import pytest
from tests.orchestration.harness_approval_workflow import WorkflowHarness

@pytest.mark.parametrize("data_pack", ["clean", "messy", "edge-cases"])
def test_approval_workflow_complete_journey(seeded_db, data_pack):
    """Full workflow: submit → review → approve → execute."""
    harness = WorkflowHarness(seeded_db, data_pack="clean")
    
    # Step 1: submit
    harness.mock_step("submit_approval", return_value={"approval_id": "A123"})
    harness.run_step(timeout=5)
    assert seeded_db.query(Approval).filter_by(id="A123").first() is not None
    
    # Step 2: review (reviewer approves)
    harness.mock_step("send_notification", return_value={"sent": True})
    harness.advance()
    assert harness.state["current_step"] == "review"
    
    # Step 3: execute
    harness.mock_step("execute_action", return_value={"success": True})
    harness.advance()
    assert harness.state["current_step"] == "execute"
    
    # Final: verify side effects
    assert seeded_db.query(ActionLog).filter_by(approval_id="A123").count() > 0

@pytest.mark.parametrize("error_path", ["reviewer_rejects", "timeout_on_execute"])
def test_approval_workflow_failure_paths(seeded_db, error_path):
    """Verify workflow handles rejection and timeouts."""
    harness = WorkflowHarness(seeded_db, data_pack="edge-cases")
    
    if error_path == "reviewer_rejects":
        harness.mock_step("review_decision", return_value={"approved": False})
        harness.run_to_completion()
        assert harness.state["status"] == "rejected"
    
    if error_path == "timeout_on_execute":
        harness.mock_step("execute_action", side_effect=TimeoutError())
        harness.run_to_completion()
        assert harness.state["retry_count"] >= 1
```

### Data-Pack Template

Same as Scenario (see above).

---

## Recommendation Algorithm

The recommendation phase scores all four types against your project's signals:

**Signals considered:**
- Framework detected (pytest, unknown)
- Entry points available (UI, HTTP, CLI, module)
- Test-DB infrastructure present (testcontainers, pytest-postgresql, sqlite, none)
- Orchestrator patterns detected (state machine, queue worker, multi-step UI)
- Existing flow files by type (scenarios, features, cassettes, orchestration)
- Team role matrix (single-role, multi-role)

**Per-type penalties:**
- HTTP-replay: penalty if no HTTP endpoint detected
- Scenario / Workflow-dryrun: penalty if no test-DB infrastructure
- Workflow-dryrun: penalty if no orchestrator pattern detected

**Confidence:**
- Low-confidence detection (<0.7) surfaces as a warning in the prompt; user can override with `--framework` / `--entry-point` / `--no-db` flags.

**Output:**
- Primary recommendation (the best fit)
- Two alternatives (with scores)
- Confidence (0.0–1.0)
- Per-type scoring details (for transparency)

---

## Summary Table

| Type | Best For | Gating Signals | Effort | Flexibility |
|------|----------|---|--------|-------------|
| **Scenario** | Multi-step journeys, multiple roles, need control over state | HTTP/CLI entry, test DB | Medium | High |
| **BDD** | Stakeholder collaboration, Gherkin alignment | Existing features, test DB | Medium | Medium |
| **HTTP-Replay** | API contracts, no DB state, fast regression | HTTP endpoint, external APIs | Low | Low |
| **Workflow-Dryrun** | Multi-step orchestration, state transitions | Orchestrator pattern, test DB | High | Medium |
