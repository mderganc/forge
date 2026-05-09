# Phase 7: Report + Handoff

**Lead: Doc-writer**

You will audit the flow against the eight quality criteria, run sample-quality probes to detect "performative" (checkbox-exercise) antipatterns, document the flow in the project memory, and prepare the handoff.

## Your Task

### 1. Criteria Audit (Criteria 1 and 8)

Review the flow against all eight criteria and mark each as **met** | **partial** | **missing**.

Criteria 1\u20138 (from plan):

1. **Realistic scenarios** \u2014 end-to-end user journeys, not synthetic CRUD.
2. **Representative test data** \u2014 clean, messy, edge-cases, duplicates packs.
3. **User roles/permissions matrix** \u2014 project-discovered roles, varied assertions.
4. **Full process execution** \u2014 entry-point ladder respected (UI > HTTP > CLI > module).
5. **Outcome validation** \u2014 \u2265 2 surfaces asserted per test.
6. **Minimal mocking** \u2014 only external services mocked (criteria 2/4 already enforced).
7. **Failure and edge handling** \u2014 \u2265 1 failure-path assertion (criterion 2/4 already enforced).
8. **Repeatable regression structure** \u2014 deterministic inputs/outputs (criterion 2/4 already enforced).

**Status key:**
- **Met:** Criterion is satisfied; no issues.
- **Partial:** Criterion is mostly satisfied; minor gaps or workarounds.
- **Missing:** Criterion is not addressed; flow needs rework.

### 2. Sample-Quality Probes

Run two automated quality checks:

#### Probe A: Data-Pack Byte-Diff

Calculate the byte-diff percentage between data-pack variants:

```
clean/ <-> messy/:   ___% byte difference
clean/ <-> edge-cases/:   ___% byte difference
clean/ <-> duplicates/:   ___% byte difference
```

- **< 5%:** Packs are too similar. **Finding:** "Messy pack performative \u2014 variants are near-identical; increase variation to test robustness."
- **5\u201350%:** Good variance. Packs are distinct.
- **> 50%:** Excessive variance (packs may be testing different features, not variants of the same).

**Codex command:**
```
exec_command bash -c '
  clean_size=$(du -sb tests/<scenario>/fixtures/data-packs/clean/ | cut -f1)
  messy_size=$(du -sb tests/<scenario>/fixtures/data-packs/messy/ | cut -f1)
  diff=$((messy_size - clean_size))
  pct=$((100 * diff / clean_size))
  echo "Byte diff: $pct%"
'
```

#### Probe B: Role-Matrix Assertion Diff

For multi-role flows, compare the assertion sets across roles:

```
Role: admin
  Assertions: [response.status_code == 200, db.query(...).count() > 0, assert "Success" in response.json()]

Role: member
  Assertions: [response.status_code == 403, assert "Forbidden" in response.json()]

Role: viewer
  Assertions: [same as member]
```

- **Identical assertions across roles:** **Finding:** "Role matrix performative \u2014 roles have identical assertions; differentiate by role expectations (e.g., admin succeeds, member is forbidden)."
- **Distinct assertions per role:** Good. Roles are testing different permission boundaries.

**Codex command:** Parse the test file(s) to extract assertion statements per role.

### 2.5 Pytest Reliability Audit

Confirm and document these best-practice checks:

- Fixtures that mutate state use `yield` teardown and default to function scope unless widening is justified.
- Temporary artifacts use `tmp_path` (or equivalent isolated temp dirs), not shared tracked paths.
- Parametrized role cases use readable IDs so failures map to role/scenario quickly.
- Tests avoid nondeterministic sources (`time`, `random`, UUID) unless explicitly stabilized.
- Any expected-failure marks are intentional and reviewed (no silent flaky masking).

### 3. Update Project Memory

Append to `.codex/forge-codex/memory/test-report.md`:

```markdown
## Flow: {{FLOW_TYPE}} \u2014 {{FEATURE_NAME}}

**Scope:** {{JOURNEY}} | {{ROLES}} | {{FAILURE_PATHS}}

**Test File:** `tests/<scenarios|features|cassettes|orchestration>/test_<scope>.py`

**Data Packs:** clean, messy, edge-cases, duplicates

**Failure Paths:** [list from scope]

**Outcome Surfaces Asserted:**
- [surface 1: e.g., "HTTP response status"]
- [surface 2: e.g., "Database row state"]

**Criteria Audit:**
| # | Criterion | Status |
|---|-----------|--------|
| 1 | Realistic scenarios | met/partial/missing |
| 2 | Representative test data | met/partial/missing |
| 3 | User roles/permissions | met/partial/missing |
| 4 | Full process execution | met/partial/missing |
| 5 | Outcome validation | met/partial/missing |
| 6 | Minimal mocking | met/partial/missing |
| 7 | Failure/edge handling | met/partial/missing |
| 8 | Repeatable regression | met/partial/missing |

**Sample-Quality Probes:**
- Data-pack byte-diff (clean vs. messy): X%
- Role-matrix assertion-diff: [identical/distinct]

**Findings:**
- [finding 1, if any \u2014 e.g., "Messy pack performative"]
- [finding 2, if any]

**Last Run:** [timestamp]

**Status:** \u2713 green | \u2717 needs rework
```

### 4. Update Scenario Index (Fix 4)

If `tests/scenarios/README.md` exists (or `tests/features/` equivalent), add a row to the scenario index table:

```markdown
| {{FEATURE_NAME}} | {{FLOW_TYPE}} | {{ROLES}} | {{FAILURE_PATHS}} | [date] | green |
```

**Note:** Fix 4 will provide the parser-gated update logic. For now, the prompt instructs you to use the column format above and append a row if the file exists. If parsing fails, leave the file unchanged and note the error.

### 5. Write Handoff

Create `handoff-test.md` in the project root (or in `.codex/forge-codex/`):

```markdown
# Test Handoff \u2014 Mock Flow Complete

**Feature:** {{FEATURE_NAME}}
**Flow Type:** {{FLOW_TYPE}}
**Status:** All tests green + deterministic

**Next Steps:**
- [If there are open findings, list them]
- [If all criteria met, suggest: "Ready for integration testing" or "Regression coverage complete"]

**Contacts:**
- Test author: [you]
- Test review: [QA lead, if different]
```

## Codex Runtime Instructions

1. **Read the flow audit state:** The orchestrator has collected flow metadata. Understand:
   - Test file locations
   - Data packs created
   - Failure paths tested
   - Roles parameterized

2. **Run the criteria audit:** For each of the 8 criteria, read the test code and scope, then mark:
   - **Met:** Criterion is satisfied.
   - **Partial:** Criterion is mostly satisfied; document the gap.
   - **Missing:** Criterion is not addressed.

3. **Run sample-quality probes:**
   - **Data-pack byte-diff:** Use `du -sb` to compare sizes; calculate percentage.
   - **Role-matrix assertion-diff:** Parse the test file (grep for assertions in each role block); note if identical or distinct.

4. **Update test-report.md:** Append a new section with the criteria audit table and probe results. Use `apply_patch` or `exec_command cat >> file <<'EOF'...EOF`.

5. **Update scenario index (if exists):** Check if `tests/scenarios/README.md` or equivalent exists. If so, append a row with the flow metadata. If file has a markdown table, append; otherwise, note that Fix 4 parser is needed.

6. **Write handoff:** Create `handoff-test.md` with the summary and next steps. Use `exec_command cat > file <<'EOF'...EOF` or `apply_patch`.

7. **State update:** Populate `state.custom["criteria_audit"]` with the 8-criterion statuses. The orchestrator will save this.

The mock flow is now complete and documented. The handoff-test.md will be read by the next skill in the workflow chain.
