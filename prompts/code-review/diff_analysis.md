# Phase 3: Team Dispatch — PR Mode (Diff Analysis)

Dispatch all reviewers to analyze the PR diff in parallel.

**Pass A / Pass B:** Apply the **Two-pass review framework** from phase 2 (*Mode selection*). Each reviewer should consider both **spec/intent alignment (Pass A)** and **engineering quality (Pass B)** when listing findings.

## Review Target

**Mode:** PR Review
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Team Assignments

{{TEAM_ASSIGNMENTS}}

## Instructions

### 0. Structural probes (Pass B)

When the step includes a **STRUCTURAL PROBES** banner:

1. Read `.structural-probes-inventory.json` and edit `.structural-probes-plan.json` per `templates/structural-quality-probes.md` — choose only the tools that fit this repo (use `[]` to skip; do not run pyscn on TS-primary apps with incidental `.py` scripts).
2. Optionally run `forge structural-probes run --state-dir <session state dir>` (path is in the banner).
3. Read `.structural-probes.json` when present before dispatching reviewers; cite probe IDs in findings.

Use diff paths / changed packages in `scope_paths` when helpful.

### 1. Fetch the Diff

- If target is a PR number: `gh pr diff {{TARGET}}`
- If target is a branch: `git diff main...{{TARGET}}`
- If target is file paths: `git diff -- {{TARGET}}`
- If from handoff: diff the files listed in the handoff

### 2. Dispatch eight structural subagents (parallel)

The step output includes a **STRUCTURAL QUALITY — eight parallel subagents** banner
with the Civil Learning **master prompt** and spawn table (`S1`–`S8`).

1. Optional: structural probes (section 0).
2. Spawn subagents per the orchestrator banner (default **S3, S4, S8**; full eight only with `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1`) using `templates/structural-quality-eight-agents.md`.
3. Merge outputs into `.structural-eight-agents.json` when subagents ran.
4. **Close each subagent** before the core team below — **do not block step 3** if time-boxed; write findings and continue.

### 3. Dispatch core Forge reviewers (parallel)

Each reviewer analyzes the diff from their perspective. Use the eight-agent sidecar
for Pass B structural findings — do not duplicate the same lenses. For each reviewer,
produce a findings list with severity (critical / warning / suggestion).

**Architect Review:**
- Is the change consistent with existing architecture?
- Does it introduce unwanted coupling or layering violations?
- Are interfaces clean and well-defined?
- Is error handling consistent with project patterns?

**Security Reviewer:**
- Are there injection vulnerabilities (SQL, XSS, command)?
- Is authentication/authorization properly handled?
- Are secrets or credentials exposed?
- Is input validation sufficient?
- Are data flows safe (no PII leaks, proper sanitization)?

**QA Reviewer:**
- Are edge cases handled?
- Is there sufficient test coverage for the changes?
- Do existing tests still pass with these changes?
- Are error paths tested?

**Critic:**
- What assumptions does this change make?
- What could go wrong that the author did not consider?
- Is there over-engineering or unnecessary complexity?
- Are there simpler alternatives?

**Investigator:**
- What is the blast radius of these changes?
- What other code depends on the changed interfaces?
- Are there transitive effects through the dependency graph?

**Doc-writer:**
- Do public APIs have adequate documentation?
- Are comments accurate and helpful (not redundant)?
- Should README or changelog be updated?

### 4. Compile Findings

Collect all findings into a unified list with:
- Finding ID (F1, F2, ...)
- Source reviewer
- Severity: critical / warning / suggestion
- Title (one line)
- Detail (explanation with file:line references)

Record findings in state and proceed to deep dive.
