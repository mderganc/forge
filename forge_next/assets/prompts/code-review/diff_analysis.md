# Phase 3: Team Dispatch — PR Mode (Diff Analysis)

Dispatch all reviewers to analyze the PR diff in parallel.

## Review Target

**Mode:** PR Review
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Team Assignments

{{TEAM_ASSIGNMENTS}}

## Instructions

### 1. Fetch the Diff

- If target is a PR number: `gh pr diff {{TARGET}}`
- If target is a branch: `git diff main...{{TARGET}}`
- If target is file paths: `git diff -- {{TARGET}}`
- If from handoff: diff the files listed in the handoff

### 2. Dispatch Reviewers in Parallel

Each reviewer analyzes the diff from their perspective. For each reviewer, produce
a findings list with severity (critical / warning / suggestion).

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

### 3. Compile Findings

Collect all findings into a unified list with:
- Finding ID (F1, F2, ...)
- Source reviewer
- Severity: critical / warning / suggestion
- Title (one line)
- Detail (explanation with file:line references)

Record findings in state and proceed to deep dive.
