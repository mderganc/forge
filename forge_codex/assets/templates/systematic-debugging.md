# Systematic Debugging Protocol

Used by develop Stage 1 for bugfix tasks and by the diagnose skill. Provides structured evidence gathering, hypothesis testing, and root cause isolation.

## Core Principle

> Debugging is an investigation, not a guessing game. Every action must either gather evidence or test a hypothesis. Never change code "to see if it helps" without a hypothesis for why it should help.

## Phase 1 — Evidence Gathering

Before forming any hypothesis, collect baseline evidence. Work through this checklist:

### Evidence Gathering Checklist

- [ ] **Error output:** Exact error message, stack trace, exit code. Copy verbatim — do not paraphrase.
- [ ] **Reproduction steps:** Exact sequence to trigger the bug. Note: "it happens sometimes" means the repro is incomplete.
- [ ] **Environment:** OS, runtime version, relevant config, environment variables, feature flags.
- [ ] **Logs:** Relevant log entries around the time of failure. Include timestamps.
- [ ] **Recent changes:** `git log --oneline -20` on affected files. What changed recently?
- [ ] **Scope:** Does this affect all users/inputs, or specific ones? What's the discriminator?
- [ ] **Working comparison:** Find a code path, input, or version where the equivalent behavior works correctly.

Record all evidence in a structured block:

```
## Gathered Evidence
- Error: [verbatim error output]
- Repro steps: [numbered steps]
- Environment: [details]
- Logs: [relevant entries with timestamps]
- Recent changes: [commits touching affected area]
- Scope: [who/what is affected, discriminator]
- Working comparison: [what works, and how it differs]
```

## Phase 2 — Hypothesis Formation

From the evidence, form hypotheses. Each hypothesis must meet two criteria:

1. **Falsifiable:** There must be a concrete test that could prove it wrong.
2. **Predictive:** It must predict specific observable outcomes beyond the known symptom.

### Hypothesis Format

```
### Hypothesis [N]: [Title]
**Claim:** [What you think is happening and why]
**Predicts:** [What else should be true if this hypothesis is correct — observable, testable]
**Disproves if:** [What result would rule this out]
**Test:** [Specific action to run — command, code inspection, query]
```

Form 2-3 hypotheses before testing any of them. This prevents anchoring on the first idea.

## Phase 3 — Pattern Analysis

Compare broken vs working code paths systematically:

1. **Identify the working equivalent.** Find a code path that does something similar and works.
2. **Diff the paths.** What's structurally different? Data flow, error handling, dependencies, config.
3. **Isolate the divergence.** At what point does the broken path diverge from the working one?
4. **Check if the divergence explains the symptom.** If yes, you have a strong hypothesis. If no, the divergence is a red herring.

```
## Pattern Analysis
- Working path: [description, file:line]
- Broken path: [description, file:line]
- Divergence point: [where they differ]
- Divergence explains symptom: [yes/no, reasoning]
```

## Phase 4 — Hypothesis Testing

Test each hypothesis using the evidence chain format:

```
### Evidence Chain — Hypothesis [N]
**Hypothesis:** [restate]
**Prediction:** [what should be observable]
**Test:** [what you did — be specific]
**Result:** [what actually happened — paste output]
**Verdict:** CONFIRMED | DENIED | INCONCLUSIVE
**Next:** [if confirmed: drill deeper with five-why | if denied: test next hypothesis | if inconclusive: what additional evidence is needed]
```

### Testing Rules

1. Test one variable at a time.
2. Prefer non-destructive tests (read-only queries, logging, assertions) before making changes.
3. Record results immediately — do not rely on memory.
4. A denied hypothesis is progress. Record it to avoid revisiting.

## Phase 5 — Isolation Techniques

When the root cause is still unclear after initial hypothesis testing, apply these techniques:

### Binary Search / Git Bisect

When you know "it worked before" and "it's broken now":

```bash
git bisect start
git bisect bad HEAD
git bisect good <last-known-good-commit>
# Git will checkout a midpoint — test the repro case
git bisect good  # or git bisect bad
# Repeat until the first bad commit is identified
git bisect reset
```

Record the result: `First bad commit: [hash] [message]`

### Minimal Reproduction Case

Reduce the reproduction case to the smallest possible input/setup:

1. Start with the full repro.
2. Remove components one at a time (dependencies, config, input fields, middleware).
3. After each removal, test if the bug still reproduces.
4. Stop when removing anything further makes the bug disappear.

The minimal repro is the debugging deliverable — it goes into the investigation findings and becomes the basis for the regression test.

```
## Minimal Reproduction
**Setup:** [minimal environment/config needed]
**Steps:**
1. [step]
2. [step]
**Expected:** [what should happen]
**Actual:** [what happens instead — paste output]
```

## Phase 6 — Root Cause Confirmation

Once you have a confirmed hypothesis, drill deeper using `templates/five-why-protocol.md`:

- The confirmed hypothesis becomes Why 1.
- Continue asking "why" until you reach an actionable root cause.
- The root cause should explain the full chain from symptom to cause.

## Output Format

The debugging session produces a structured investigation report:

```
## Investigation Summary
**Symptom:** [user-visible problem]
**Root cause:** [actionable root cause from five-why chain]
**Evidence chain:** [list of confirmed hypotheses with evidence]
**Denied hypotheses:** [list — these are valuable for reviewers]
**Minimal reproduction:** [repro case]
**Suggested fix:** [what to change and why]
```

## Rules

1. **Never guess-and-check.** Every code change must be preceded by a hypothesis and prediction.
2. **Preserve evidence.** Don't clean up logs, temp files, or debug output until the investigation is complete.
3. **Record denied hypotheses.** They narrow the search space and prevent other agents from repeating the same investigation.
4. **Minimal repro is mandatory.** If you can't reproduce it, you can't confirm a fix.
5. **One root cause per investigation.** If you discover multiple bugs, file separate investigations for each.
