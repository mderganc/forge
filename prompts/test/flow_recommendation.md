# Phase 2: Flow-Type Recommendation

**Lead: QA + Architect**

The system recommends the most appropriate mock-flow style from four types based on your project's infrastructure and the feature you're testing. You will score each type against the project signals and make a final recommendation with confidence and alternatives.

## The Eight Quality Criteria

Every mock flow must meet these criteria. Review them now as your evaluation rubric:

1. **Realistic scenarios** — flows describe end-to-end user journeys (setup, data upload, processing, review, export), not synthetic CRUD pings.
2. **Representative test data** — fixtures include malformed files, edge cases, incomplete records, duplicates, and well-formed controls. Lives under `<scope>/fixtures/data-packs/{clean,messy,edge-cases,duplicates}/`.
3. **User roles and permissions matrix** — *project-discovered*, not hardcoded. Reads RBAC config (Django Groups, Casbin, Cerbos, YAML). If none found, collapses to `{anonymous}` and audit waives criterion 3.
4. **Full process execution** — entry-point ladder: UI > HTTP > CLI > module. Never imports SUT internals and calls functions directly.
5. **Outcome validation** — assertions cover ≥ 2 of {response payload, DB row, log output, file, audit trail, notification}.
6. **Minimal mocking** — only mock externals: email senders, paid APIs, non-deterministic LLM, slow jobs. Do NOT mock core logic, DB, permissions, ingestion when test DB exists.
7. **Failure and edge handling** — each flow contains ≥ 1 failure-path assertion (bad input, missing permission, partial failure, retry behavior).
8. **Repeatable regression structure** — deterministic inputs and outputs. Enforced via double-run check.

## The Four Flow Types

See `templates/mock-flow-types.md` for full details. Here's a quick reference:

### Type 1: Scenario Script
- **Tooling:** pytest, custom fixtures
- **File layout:** `tests/scenarios/test_<scope>.py` + data-pack subdirs
- **When:** HTTP/CLI entry point + test DB + fine-grained control over assertions
- **Fit scores:** 9-10 on criteria 1,4,8; 8-9 on criteria 2,3,5,6,7
- **Anti-pattern:** No test DB (makes mocking hard); only UI entry point; over-mocking core logic

### Type 2: BDD / Gherkin
- **Tooling:** pytest-bdd (or behave), `.feature` files + step definitions
- **File layout:** `tests/features/<scope>.feature` + `steps/` + data-pack subdirs
- **When:** Team prefers business-readable specs + HTTP/CLI + test DB
- **Fit scores:** 10 on criterion 1 (Gherkin is realistic by design); 8-9 on others
- **Anti-pattern:** No test DB; team doesn't use Gherkin; complex multi-step workflows hard to express

### Type 3: HTTP/API Replay
- **Tooling:** pytest + vcrpy (cassettes = request/response recordings)
- **File layout:** `tests/cassettes/test_<scope>.py` + `data/<scope>/` cassette files
- **When:** HTTP-only entry point + no (or limited) test DB + external APIs you want to replay
- **Fit scores:** 10 on criterion 4 (exact replay); 7-8 on others; 5 on criterion 7 (hard to add new failures)
- **Anti-pattern:** No HTTP entry point; no existing cassettes to replay (requires manual recording)

### Type 4: Workflow Dry-Run
- **Tooling:** pytest + harness that orchestrates workflow steps
- **File layout:** `tests/orchestration/test_<scope>_dryrun.py` + harness + data packs
- **When:** Multi-step orchestrator (Celery, RQ, state machine, forge-style scripts) + test DB
- **Fit scores:** 9-10 on criteria 1,2,7,8; 8-9 on others
- **Anti-pattern:** No orchestrator pattern detected; single-step flows; no test DB

## Your Task

Score each of the four types on the eight criteria using a **0–10 scale** based on your project signals:

- **10:** Type is an excellent fit; criterion is well-served.
- **7–9:** Good fit; criterion is largely met with minor caveats.
- **4–6:** Possible but with workarounds; criterion requires extra care.
- **1–3:** Poor fit; criterion is hard to satisfy with this type.
- **0:** Type is ruled out for this project (e.g., workflow-dryrun when no orchestrator exists).

### Scoring Template

For **each type**, evaluate:
- How well does it handle the 8 quality criteria?
- Does your project have the infrastructure it needs?
- Are there anti-patterns that would undermine this choice?

**Scenario Script Score:**
- Criterion 1 (Realistic scenarios): ___/10 – [reasoning]
- Criterion 2 (Representative test data): ___/10 – [reasoning]
- Criterion 3 (User roles/permissions): ___/10 – [reasoning]
- Criterion 4 (Full process execution): ___/10 – [reasoning]
- Criterion 5 (Outcome validation): ___/10 – [reasoning]
- Criterion 6 (Minimal mocking): ___/10 – [reasoning]
- Criterion 7 (Failure/edge handling): ___/10 – [reasoning]
- Criterion 8 (Repeatable regression): ___/10 – [reasoning]
- **Type Total:** [average of scores above]

[Repeat the template for BDD, HTTP Replay, and Workflow Dry-Run types]

## Recommendation Output

Once you've scored all four types, write a summary and save it as a sidecar JSON file. The orchestrator will use this to advance to the next step.

### Instruction for Saving the Sidecar

Create a file named `.test-recommendation-step2.json` in the state directory (the orchestrator will tell you the path) with this structure:

```json
{
  "chosen": "scenario|bdd|http-replay|workflow-dryrun",
  "reasoning": "[2–3 sentence explanation of why this type best fits your project and feature]",
  "confidence": 0.0,
  "alternatives": [
    {
      "type": "bdd",
      "score": 7.5,
      "reason": "[why this is a fallback option]"
    }
  ]
}
```

**Confidence:** 0.0–1.0. Use 1.0 if you're certain; 0.7–0.9 if there are minor uncertainties; <0.7 if multiple types score equally.

### If User Passed `--flow-type` Override

If the user specified `--flow-type <type>` on the command line, acknowledge it:

> **User Override Detected:** You passed `--flow-type={{FLOW_TYPE_OVERRIDE}}`, so the recommendation sidecar is being pre-populated with that choice. The remaining steps will proceed with {{FLOW_TYPE_OVERRIDE}}. If you'd like to reconsider, delete the `.test-recommendation-step2.json` file and re-run step 2.

Then do NOT score — just acknowledge and exit. The sidecar is already written with the user's choice.

## Codex Runtime Instructions

1. **Read the flow types doc:** `exec_command cat templates/mock-flow-types.md | head -200` to review the full details (you may have seen a summary above, but the doc has more examples).

2. **Understand project signals:**
   - Framework: {{FRAMEWORK}} ({{FRAMEWORK_CONFIDENCE}}% confidence)
   - Entry point: {{ENTRY_POINT}} ({{ENTRY_POINT_CONFIDENCE}}% confidence)
   - Test DB: {{TEST_DB}}
   - Roles: {{ROLES}}
   - Orchestrator pattern: [detected from project structure]

3. **Score each type:** Use the scoring template above. Your reasoning should reference:
   - The eight quality criteria
   - How well the type fits the project's infrastructure
   - The feature's characteristics (scope, entry point, roles, data complexity)

4. **Write the sidecar:** Once scoring is complete, write the JSON file named `.test-recommendation-step2.json` to the state directory. Use `apply_patch` or direct `exec_command echo` to create it (the orchestrator will show the path).

   Example using echo:
   ```
   exec_command echo '{...json...}' > /path/to/state/.test-recommendation-step2.json
   ```

5. **Verify:** Run `exec_command cat /path/to/state/.test-recommendation-step2.json` to confirm the file was written correctly.

The next step will ingest this sidecar and proceed to scope definition.
