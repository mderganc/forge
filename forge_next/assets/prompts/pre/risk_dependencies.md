# Phase 5: Risk & Dependency Analysis (Pre-Implementation)

You are analyzing the plan for dependency risks, failure modes, and rollback gaps.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Your Task

If the plan introduces **knip/madge/pyscn** workflow probes, note external dependencies (Node.js, npm, pipx/uv) and false-positive triage — see `templates/structural-quality-probes.md`.

### 1. Dependency Graph Validation

Examine the task ordering and dependencies in the plan:

- Are all task dependencies explicitly declared? Are there implicit dependencies that would cause failures if tasks ran in the wrong order?
- Are there circular dependencies between tasks?
- Is the critical path identified? Could reordering reduce total implementation time?
- Are there missing prerequisites — tasks that must happen before a planned step but aren't listed?

### 2. Risk Assessment Per Step

For each significant plan step, assess:

| Dimension | Scale |
|-----------|-------|
| **Likelihood** | How likely is this step to fail or cause problems? (high / medium / low) |
| **Impact** | If it fails, how bad? (catastrophic / serious / moderate / minor) |
| **Detectability** | Would we notice before production? (yes / maybe / no) |

Focus on steps with high likelihood + high impact, or any step with low detectability.

### 3. Rollback Strategy Audit

For each plan step:

- Is there a viable way to undo this step if it fails partway through?
- Are there irreversible operations (data migrations, external API calls, destructive deletes) without explicit acknowledgment?
- If step N fails, can we safely roll back to the state after step N-1?

Flag any step that lacks a rollback path, especially if it modifies persistent state.

### 4. Pre-Mortem (per `templates/pre-mortem.md`)

Apply prospective hindsight: "It is 6 months from now. This plan was implemented and **failed catastrophically**. What happened?"

Generate 3-5 failure scenarios across these categories:

| Category | Example Failures |
|----------|-----------------|
| **Technical** | Doesn't scale, data corruption, race condition, dependency breaks |
| **Process** | Tests don't cover the real failure mode, rollback doesn't work, migration irreversible |
| **Integration** | Breaks downstream consumers, incompatible with existing feature, silent semantic change |
| **Assumption** | User behavior differs, data distribution different, constraint changes |
| **External** | Dependency deprecated, API changes, security vulnerability in approach |

For each scenario: state what failed, why (root cause), and what was missed during planning.

Map high-likelihood or high-impact scenarios to **concrete mitigations** — specific actions, not vague "test more" statements.

## Output

For each issue found, create a finding with severity:
- "critical" — No rollback for destructive operation, circular dependency, high-likelihood + high-impact risk without mitigation
- "warning" — Risky ordering, missing dependency declaration, moderate risk without mitigation
- "suggestion" — Task ordering optimization, nice-to-have mitigation

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "risk_dependencies", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if no issues.
