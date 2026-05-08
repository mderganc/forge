# Phase 5: Mock Authoring

**Lead: Developer**

You will fill in the test logic: populate data packs, write role-parameterized assertions, implement failure-path scenarios, and validate outcomes across \u2265 2 surfaces. This is the "RED" phase of TDD: write the failing test first, then implement.

## Quality Criteria (Your Acceptance Bar)

Before you start, review these criteria \u2014 your code must satisfy them:

1. **Realistic scenarios** \u2014 test real user journeys, not synthetic CRUD pings.
2. **Representative test data** \u2014 data packs include clean, messy, edge-cases, duplicates.
3. **User roles/permissions matrix** \u2014 test each role with appropriate assertions.
4. **Full process execution** \u2014 use the detected entry point (HTTP, CLI, etc.), never import internals.
5. **Outcome validation** \u2014 assertions touch \u2265 2 surfaces (response, DB, logs, files, etc.).
6. **Minimal mocking** \u2014 only stub external services; exercise core logic with real calls.
7. **Failure and edge handling** \u2014 \u2265 1 failure-path assertion (bad input, missing permission, etc.).
8. **Repeatable regression structure** \u2014 deterministic data, no randomness.

## Your Task

{{#if AUTHORING_GATE_FAILURES}}
**Previous attempt had issues:**
{{AUTHORING_GATE_FAILURES}}

Please address the missing items and re-run step 5.
{{/if}}

### 1. Populate Data Packs

Using the sample inputs from step 3, create representative data variants:

- **clean/** \u2014 Your sample data as-is. Control baseline. README says: "Well-formed data; control baseline."
- **messy/** \u2014 Variants with encoding issues, extra whitespace, line-ending mismatches. README says: "Encoding variations, whitespace, line-ending issues; tests robustness."
- **edge-cases/** \u2014 Empty, oversized, malformed, boundary-condition files. README says: "Boundary conditions: empty, oversized, partial, invalid format."
- **duplicates/** \u2014 Intentional duplicate records. README says: "Duplicate IDs and conflicting records; tests idempotency and conflict handling."

Each pack should include a README.md describing the variant (see examples above).

**Codex command:** For each variant, use `apply_patch` or `exec_command cat > file <<'EOF'...EOF` to populate files.

### 2. Write Role-Parameterized Assertions

If your flow tests multiple roles:

- **Conftest fixture or BDD steps:** Define fixtures or step definitions that parameterize by role (e.g., fixture `authenticated_client` returns a TestClient with role-specific auth headers).
- **Per-role assertion sets:** Role `admin` may assert `status == 200`; role `member` may assert `status == 403`. Use `@pytest.mark.parametrize` or BDD scenario outlines.
- **Assertion surfaces:** Each role should make assertions on \u2265 2 surfaces. Examples:
  - Response status + response body + DB state
  - CLI return code + stdout + file created
  - API response + log entry

**Gate check:** Identical assertion sets across roles trigger a "role matrix performative" finding in step 7. Roles should test different behaviors.

### 3. Implement Failure-Path Scenarios

Write \u2265 1 test case that exercises a failure scenario from step 3:

```python
def test_upload_flow_bad_input_validation_fails():
    """Bad input: malformed CSV triggers validation error."""
    client = TestClient(app)
    with open("data-packs/messy/invalid_format.csv") as f:
        response = client.post("/upload", files={"file": f})
    assert response.status_code == 400
    assert "validation" in response.json()["error"].lower()
    # Check DB: no record was created
    assert not db.query(Record).filter_by(source="invalid_format.csv").first()
```

Expected: test fails at this point (RED phase of TDD). You're writing the test first.

### 4. Implement Test Logic

Fill in the primary test functions:

- **Happy path:** Call the entry point with `clean/` data. Assert success across \u2265 2 surfaces.
- **Failure paths:** Call with `messy/` or `edge-cases/` data. Assert expected failures.
- **Role matrix:** Parameterize by role; each role has role-specific assertions.

Use the entry-point correctly:
- **HTTP:** `TestClient(app).post("/endpoint", ...)`
- **CLI:** `subprocess.run(["command", ...], capture_output=True)`
- **Module:** Likely not applicable for end-to-end flows.

### 5. Stub External Mocks

For external services (email, payment API, LLM), create minimal mocks:

```python
@pytest.fixture
def mock_email(monkeypatch):
    sent = []
    def send_email(to, subject, body):
        sent.append({"to": to, "subject": subject})
        return True
    monkeypatch.setattr("app.email.send", send_email)
    return sent

def test_upload_flow_success(mock_email):
    # ... test code ...
    assert len(mock_email) == 1  # Email was sent
    assert mock_email[0]["subject"] == "Upload Complete"
```

### 6. Run the Test (RED Phase)

Once authoring is complete, run the test:

```
cd /path/to/project
python -m pytest tests/<scenarios|features|cassettes|orchestration>/test_<scope>.py -v
```

Expected: **FAIL**. You've written the test first; it should fail because the app logic doesn't exist yet (or isn't wired to the test harness).

If the test passes immediately, either:
- The feature already exists (good \u2014 scaffold is reusing existing code)
- The test is too permissive (fix it)

**Important:** Do NOT implement the app feature yet. Authoring stops here. The next step (Execution) will run the test against the actual feature code.

## Gate Check (Before Advancing)

The orchestrator will verify:

- \u2713 \u2265 1 failure-path assertion exists (grep for test name or exception)
- \u2713 \u2265 2 outcome surfaces asserted per test (response + DB, CLI + file, etc.)
- \u2713 Only allowed externals are mocked (check mock list against scope)

If any check fails, step 5 will re-prompt with a corrective message.

## Codex Runtime Instructions

1. **Read the scope and scaffold state:** Understand the journey, roles, entry point, external services, and created files.

2. **Populate data packs:** For each variant (clean, messy, edge-cases, duplicates), create sample data files using the sample inputs from step 3. Use `exec_command cat > file <<'EOF'` to write files.

3. **Write test code:** Fill in the test functions in the primary test file. Use `apply_patch` to modify the scaffold files. Follow the TDD pattern: write failing tests first.

4. **Implement fixtures:** In conftest.py or steps file, define role-parameterization fixtures. Example:
   ```python
   @pytest.fixture(params=["admin", "member", "viewer"])
   def authenticated_client(request, app):
       client = TestClient(app)
       client.headers["X-Role"] = request.param
       return client
   ```

5. **Run the test locally:** Once you've written the failing test, verify it fails as expected:
   ```
   exec_command cd /path/to/project && python -m pytest tests/.../test_<scope>.py -v --tb=short
   ```

6. **Verify outcome surfaces:** For each test, ensure assertions touch \u2265 2 surfaces:
   ```
   - Response status
   - Response body or DB state
   - Log output or file created
   ```

7. **Gate verification:** The orchestrator will count failure-path assertions and outcome surfaces. If the gate fails, re-run step 5 and address the missing items.

The next step (Execution) will run the test against the actual feature implementation and check for determinism via double-run.
