# Phase 4: Scaffolding

**Lead: Developer**

You will create the file skeleton for the mock flow based on the chosen type and the scope defined in step 3. The orchestrator will check that all required files and directories are present before allowing you to advance.

## Flow Type: {{FLOW_TYPE}}

Your scaffold must create the correct directory and file structure for {{FLOW_TYPE}}. Refer to `templates/mock-flow-types.md` for the exact layout.

## Your Task

1. **Read the scope:** Understand what journey, roles, and data packs you're creating for (from step 3 state).

2. **Create the file layout:** Based on {{FLOW_TYPE}}, create:
   - **Primary test file(s)** — the main pytest file or `.feature` file where assertions live
   - **Data-pack directory tree** — `fixtures/data-packs/{clean,messy,edge-cases,duplicates}/` with README.md files
   - **Role-parameterization harness** — if multiple roles, a conftest.py or step harness that parameterizes the test
   - **Entry-point invocation** — explicit code that calls the entry point (HTTP, CLI, etc.) — NOT internal module imports

3. **Populate stubs:** Each file should have a minimal stub:
   - Test file: empty test function(s) with docstrings
   - Data-pack READMEs: describe the variant (e.g., "clean: well-formed data, control baseline")
   - Conftest/harness: fixture definitions (empty for now; authoring step fills them)

4. **Gate Check:** After creation, the next invocation of step 4 will verify:
   - {{#if SCAFFOLD_GATE_FAILURES}}
     **Previous attempt had issues:**
     {{SCAFFOLD_GATE_FAILURES}}

     Please address the missing items listed above and re-run.
   {{/if}}
   - Primary test file exists and mentions the entry point (e.g., TestClient, subprocess.run, etc.)
   - Data-pack directories exist: `clean/`, `messy/`, `edge-cases/`, `duplicates/`
   - Each data-pack dir has a `README.md`
   - Role harness file exists (conftest.py or steps/ for BDD)
   - Entry-point invocation is present (grep for CLI command, HTTP request, or TestClient)

   If any are missing, step 4 will re-prompt with a corrective message.

## Example Scaffolds

### Scenario Script

```
tests/scenarios/
├── conftest.py                    # Multi-role fixtures
├── test_upload_flow.py            # Primary test (empty test function)
└── upload_flow/
    └── fixtures/
        └── data-packs/
            ├── clean/
            │   ├── valid.csv
            │   └── README.md       # "Well-formed data: 3 rows, valid CSV"
            ├── messy/
            │   ├── mixed_encoding.csv
            │   └── README.md       # "Mixed encoding: UTF-8 + UTF-16 variants"
            ├── edge-cases/
            │   ├── empty.csv
            │   ├── oversized.csv
            │   └── README.md       # "Edge cases: empty file, file > 1GB"
            └── duplicates/
                ├── dupe_ids.csv
                └── README.md       # "Duplicates: same ID appears twice"
```

### BDD

```
tests/features/
├── upload_flow.feature         # Main feature file (empty scenarios)
└── steps/
    ├── conftest.py             # Fixtures for role parameterization
    ├── step_upload.py          # Step implementations (stubs)
    └── fixtures/
        └── data-packs/         # Same structure as scenario
```

### HTTP Replay

```
tests/cassettes/
├── conftest.py                 # Recorder/replayer fixtures
├── test_upload_flow.py         # Test file (empty test)
└── data/
    ├── upload_flow/
    │   ├── cassettes/          # VCR cassette files (empty YAML for now)
    │   │   ├── admin.yaml
    │   │   └── member.yaml
    │   └── data-packs/         # Same structure as scenario
```

### Workflow Dry-Run

```
tests/orchestration/
├── conftest.py                 # Orchestrator fixtures
├── harness_upload.py           # Step harness (stubs)
├── test_upload_dryrun.py       # Main test (empty)
└── upload_flow/
    └── fixtures/
        └── data-packs/         # Same structure as scenario
```

## Codex Runtime Instructions

1. **Read the scope state:** The orchestrator has saved the scope to a sidecar; you may read it via:
   ```
   exec_command cat /path/to/state/.test-scope-step3.json
   ```

2. **Determine directories:** Use `_detect_test_layout` results (from step 1) to find if `tests/scenarios/` or `tests/features/` exists. Only create `tests/scenarios/` if none exist.

3. **Create files:** Use `apply_patch` or `exec_command mkdir -p` and `exec_command cat > file.py <<'EOF'...EOF` to create the structure.

4. **List created files:** Once done, log all files created for verification:
   ```
   exec_command find tests/<scenarios|features|cassettes|orchestration> -type f -o -type d | sort
   ```

5. **Verify entry-point invocation:** Ensure the primary test file contains code that invokes the entry point:
   - For HTTP: `TestClient(app).post(...)`
   - For CLI: `subprocess.run(["cli-command", ...])`
   - For module: `from app import feature; feature(...)`
   - NOT: `app.feature()` (internal import)

6. **State update:** The orchestrator will read the file list and check the gate. If all files are present, step advances to authoring.

The next step (Mock Authoring) will fill in the test logic, data packs, and assertions.
