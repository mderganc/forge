# Pre-Mortem Analysis

Based on Gary Klein's prospective hindsight technique. Used at approval gates in develop, plan, and diagnose to surface hidden failure modes before committing to a solution.

## Core Principle

> Standard risk analysis asks "what could go wrong?" A pre-mortem declares "it has gone wrong" and asks "what happened?" This cognitive reframe consistently surfaces risks that forward-looking analysis misses.

## Protocol

### Step 1: Set the Scene

State: "Imagine it is 6 months from now. This solution was implemented and has **failed catastrophically**. The team is doing a post-mortem. What happened?"

### Step 2: Silent Generation (per agent)

Each dispatched agent independently generates 3-5 failure scenarios. No discussion, no filtering. Each scenario must:
- State what went wrong (the observable failure)
- State why (the root cause of the failure)
- State what was missed during planning/review

Categories to consider:
| Category | Example Failures |
|----------|-----------------|
| **Technical** | Doesn't scale, breaks under load, data corruption, race condition, dependency breaks |
| **Process** | Tests don't cover the real failure mode, rollback doesn't actually work, migration is irreversible |
| **Integration** | Breaks downstream consumers, incompatible with existing feature, changes semantics silently |
| **Assumption** | User behavior differs from expected, data distribution is different, constraint we relied on changes |
| **External** | Dependency is deprecated, API changes, security vulnerability discovered in approach |

### Step 3: Round-Robin Collection

Collect all failure scenarios. No evaluation yet — just list them.

```
## Pre-Mortem Failure Scenarios
1. [Agent]: [Failure] — because [root cause] — missed because [blind spot]
2. [Agent]: [Failure] — because [root cause] — missed because [blind spot]
...
```

### Step 4: Categorize and Prioritize

Group scenarios by category (technical, process, integration, assumption, external). For each:
- **Likelihood:** How plausible is this failure? (high/medium/low)
- **Impact:** How bad if it happens? (catastrophic/serious/moderate/minor)
- **Detectable:** Would we notice before production? (yes/maybe/no)

### Step 5: Map to Mitigations

For every high-likelihood or high-impact scenario:

```
## Pre-Mortem Mitigations
| Scenario | Likelihood | Impact | Mitigation | Owner |
|----------|-----------|--------|------------|-------|
| [failure] | high | serious | [specific action to prevent or detect] | [agent/task] |
```

### Step 6: Update Plan

- Add new mitigations to the risk register
- Add new test cases for detectable failure modes
- Flag unmitigatable risks for user awareness
- Record any scenarios that change the recommendation

## When to Run

- **develop** — Phase 6 (approval): Before presenting solutions to the user
- **plan** — Phase 4 (review loop): During plan review, per wave
- **diagnose** — Phase 5 (solutions): Before selecting a fix approach

## Rules

1. **Never skip this for non-trivial changes.** Trivial = single file, no behavioral change. Everything else gets a pre-mortem.
2. **The "it failed" framing is mandatory.** Don't soften to "it might fail." The certainty of failure is what triggers deeper thinking.
3. **Record everything.** Scenarios that seem unlikely are often the ones that actually happen.
4. **Mitigations must be specific.** "We'll test more" is not a mitigation. "Add a load test that simulates 10x peak traffic" is.
