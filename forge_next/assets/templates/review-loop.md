# Review Loop Protocol

Every stage in the forge-codex team workflow uses this review loop. Scale depth with task/plan size (`templates/scope-size-model.md`).

## The Loop

Round N:
  Step 1: SELF-REVIEW (producing agent)
    The agent that produced the artifact reviews its own work.
    Guiding question: "What did I miss? What assumption did I not validate?"

  Step 2: CROSS-AGENT REVIEW (assigned reviewer)
    A different agent reviews from their specialist perspective.
    Assignment varies by stage (see stage skill files).
    **Small / low-risk:** may combine Steps 2–3 into one combined cross/critic pass.

  Step 3: CRITIC CHALLENGE (critic)
    Devil's advocate review. Assumes the artifact is wrong.
    Guiding question: "What's the strongest argument against this work?"
    Also flag **scope creep** and **over-decomposition**.

  Step 4: PM VALIDATION (PM — independent of critic)
    PM checks completeness, consistency, scope fidelity, and readiness to proceed.
    PM challenges independently — not just rubber-stamping the critic.

## Loop-reduction policy

1. **Batch** all first-pass findings before requesting changes.
2. After a fix, **re-review only changed files and unresolved critical/warning blockers** — do not rerun the full roster for suggestion-only changes.
3. **Suggestions are advisory** — record them; they neither reopen a phase nor block handoff.
4. **Cap low-risk loops at two rounds** (initial + focused verification). If critical/warning remain, escalate to the user rather than looping indefinitely.
5. **Full extra rounds** only when the fix changes design boundary, public contract, security posture, or structural probe results materially.

EXIT CONDITION: No open **FAIL** or blocking **WARN** in the same round (suggestions may remain).
CONTINUE: Blocking finding → producing agent addresses it → Round N+1 (focused).

## Finding Severity

| Severity | Meaning | Blocks Exit? |
|----------|---------|-------------|
| FAIL | Incorrect, broken, or dangerous | Yes |
| WARN | Suboptimal, risky, or incomplete | Yes for medium/large by default; for **small/low-risk**, PM may treat as advisory with recorded rationale |
| PASS / suggestion | Acceptable or nice-to-have | No |

WARN is treated as blocking by default on medium/large work. For small/low-risk, prefer advisory WARN unless security/data-integrity is involved. Only the PM + Architect can reclassify a WARN, and the reclassification must be recorded with rationale.

## Finding Format

### [PASS|WARN|FAIL]: [title]
**ID:** [STAGE-ROLE-NNN] (e.g., S1-QA-001)
**Status:** OPEN | RESOLVED | ADVISORY
**Location:** [file:line or artifact section]
**Description:** What was found
**Impact/Risk:** What could go wrong
**Fix:** How to fix

## Review Summary (required at end of each round)

## Review Summary — Round N
**Open blocking findings:** [count]
**Advisory suggestions:** [count]
**Resolved findings verified:** [count]
**Review status:** CLEAN | REQUIRES_FIXES | ESCALATE

## Source Data Precedence

> Source data always takes precedence over synthesis.

When evaluating evidence, always weight first-hand source data (logs, code, test output, metrics, grep results, git history, stack traces) above synthesized conclusions from any agent or LLM judge. Both may be cited, but:

1. **Present source data first.** Raw evidence appears before any interpretation or rating.
2. **Ground every judgment in source.** A synthesized conclusion without cited source data is an unverified claim — treat it as a hypothesis, not a finding.
3. **When source and synthesis conflict, source wins.** If raw test output contradicts a synthesized assessment, the test output is authoritative.
4. **LLM judge ratings supplement, not replace.** When an LLM judge has scored or rated an artifact, include the rating alongside the source data it was derived from. The source data is the primary evidence; the rating is a secondary signal.

This principle applies at every review step (self-review, cross-agent, critic, PM validation).

## Rules

1. Follow the loop-reduction policy above — do not loop forever on low-risk work.
2. Each round's findings are appended to the producing agent's memory file.
3. Every **blocking** finding gets a beads issue (if beads available) with label `review,stage-N`.
4. Resolved findings are verified by the original reviewer before marking RESOLVED.
5. The PM tracks aggregate finding counts in `project.md`.
6. Every finding must cite source data (file:line, test output, log entry, metric). Findings backed only by synthesis or ratings without source references are incomplete and must be substantiated before they can block exit.
7. Reject **scope creep** and **over-decomposition** (too many waves/tasks for a localized change).
