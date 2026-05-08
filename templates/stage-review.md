# Stage 6 — Review & Final Summary

## Purpose
Full-team review of integrated implementation, remediation loops until clean, and updated summary for the user.

## Lead Agents
**QA Reviewer, Security Reviewer, Architect, Critic** — all review in parallel

## Superpowers Integration
- Invoke `superpowers:verification-before-completion` if available when verifying fixes

## PM Actions

### 1. Merge Sub-Branches

For each completed sub-branch (in dependency order):
git checkout forge/[feature-name]
git merge forge/[feature-name]/[task-name]

After each merge:
- Run full test suite
- If merge conflict → assign to owning agent → critic reviews resolution
- If tests fail → assign to responsible agent → fix before next merge

### 2. Dispatch Full-Team Review

All reviewers operate against the merged feature branch. Dispatch in parallel:

| Agent | Focus |
|-------|-------|
| Architect | Architecture conformance — does integrated code match plan? Component boundaries? Drift? |
| QA Reviewer | Full test suite + coverage. Edge cases. Integration between parallel components. Requirements verification. |
| Security Reviewer (if activated) | OWASP audit. Input validation. Auth/authz. Dependencies. Secrets. |
| Critic | Most likely production failure? What wasn't tested? What assumption was wrong? |

### 3. Aggregate Findings

Collect all non-PASS findings into project.md:

## Open Findings Tracker — Stage 6

| ID | Source | Severity | Status | Root Cause | Owner | Reviewer | Beads ID | Notes |
|----|--------|----------|--------|------------|-------|----------|----------|-------|
| S6-QA-001 | QA | FAIL | OPEN | Missing null check | backend-dev | qa-reviewer | [bd-xxx.F1] | |

Create beads issues for each finding:
bd create "[finding]" -t bug --parent [epic-id] -l "review-finding,stage-6"
bd dep add [finding-id] [task-id] --type discovered-from

### 4. Remediation Loop

While Open Findings Tracker has OPEN items:

  1. Architect groups related findings → remediation batch
     - Writes plan: root cause, approved fix, affected files, risks, re-reviewers
     - Beads: create remediation task

  2. Critic reviews remediation plan
     "Fixing symptom or cause? Will fix introduce new problems?"

  3. PM dispatches fix to appropriate agent
     - Work on feature branch (no sub-branches for fixes unless large)
     - Each fix references plan ID and finding IDs

  4. Re-review by original reviewer + Critic
     - Verify specific findings resolved
     - Check fix didn't introduce new issues

  5. PM updates tracker
     - Resolved → RESOLVED
     - New findings → added to tracker
     - Loop continues until clean

  No fixed iteration limit.
  Exit: all RESOLVED, or user accepts risk, or external blocker (→ backlog)

### 5. Updated Summary

Once clean (or user accepts), present:

## forge-codex team — Implementation Summary

### Completion Status
| # | Issue | Root Cause | Solution | Status | Branch |
|---|-------|-----------|----------|--------|--------|
| 1 | [title] [id] | [title] [id] | [solution] [id] | ✅ Complete | merged |

### Scoring Actuals vs Estimates
| # | Dimension | Estimated | Actual | Delta |
|---|-----------|-----------|--------|-------|
| 1 | Effort | 6 | 7 | +1 (reason) |

### Review Findings Resolved
- [N] total across [M] rounds
- QA: [N], Security: [N], Architect: [N], Critic: [N]

### Deferred Items (see backlog)
- [title] [id] — [reason]

### Remaining Risks
- [accepted risks]

### 6. Stage Gate

| Autonomy | Behavior |
|----------|----------|
| Level 1 | Present full summary, confirm before Stage 7 |
| Level 2 | Present full summary, auto-proceed to Stage 7 |
| Level 3 | Log summary, auto-proceed to Stage 7 |

### 7. Git Checkpoint

git add .codex/forge-codex/ && git commit -m "workflow: Stage 6 complete — reviews clean, [N] findings resolved"

Record in project.md: `## Stage 6: COMPLETE [timestamp]`
