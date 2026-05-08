# Stage 3 — User Approval

## Purpose
Present the user with a scored, numbered summary of all issues, root causes, and solution options with cons/risks, impact, effort, and auto-calculated priority. Get explicit approval before implementation.

## Lead Agent
**PM** — presents summary and handles user interaction

## Always Pauses
This stage pauses for Levels 1 and 2. Level 3 auto-selects recommended solutions but logs the full summary.

## PM Actions

### 1. Build Approval Summary

Read `investigation.md` and `solutions.md` to compile:

## forge-codex team — Approval Summary

### Issue 1: [Finding title] [beads-id]
**Root Cause:** [root cause description] [beads-id]

| # | Solution | Q | T | C | R | E | P | Rec? |
|---|----------|---|---|---|---|---|---|------|
| 1a | [Solution A] | 7 | 4 | 3 | 8 | 6 | 5.5 | ★ |
| 1b | [Solution B] | 5 | 6 | 7 | 4 | 3 | 5.8 | |

**Legend:** Q=Quality, T=Time, C=Cost, R=Risk Reduction, E=Effort, P=Priority (auto)

**Solution 1a (★ Recommended):** [one-line approach]
  - Pros: [key benefits]
  - Cons/Risks: [key downsides, failure modes]
  - Reversibility: [easy/moderate/hard]

**Solution 1b:** [one-line approach]
  - Pros: [key benefits]
  - Cons/Risks: [key downsides, failure modes]
  - Reversibility: [easy/moderate/hard]

---

## Summary

| Issue | Recommended | Priority | Effort | Status |
|-------|------------|----------|--------|--------|
| 1 | 1a - [name] | 5.5 | 6 | ⏳ Pending |

**Total estimated effort:** [sum or range]

### 2. Handle User Response

| User Says | PM Action |
|-----------|-----------|
| "Approve all" / "looks good" | Accept all recommended, proceed to Stage 4 |
| "Approve 1a, 2b" | Accept specified solutions, proceed to Stage 4 |
| "Reject 2" / "defer 2" | Close beads issue, write to backlog, proceed with remaining |
| "I don't like any option for issue 1" | Loop to Stage 2 for that root cause only |
| "Root cause for issue 1 is wrong" | Loop to Stage 1 for that finding only |
| "Add requirement: must support X" | Loop to Stage 1 — new requirement |
| "Change priority" / "effort wrong" | Update scores, re-present |
| "Cancel all" | Close epic, everything to backlog |

### 3. Partial Approval — Deferred Items

For deferred items:
1. Close beads issue: bd close [id] --reason "Deferred by user: [reason]"
2. Write to `.codex/forge-codex/backlog.md`:

## Deferred: [title] [beads-id]
**Date:** [YYYY-MM-DD]
**Original Epic:** [epic beads-id]
**Root Cause:** [description] [beads-id]
**Recommended Solution:** [description]
**All Solution Options:**
- [A]: Q=N T=N C=N R=N E=N P=N — [one-line + key cons]
- [B]: Q=N T=N C=N R=N E=N P=N — [one-line + key cons]
**Scores (recommended):** Q=N T=N C=N R=N E=N P=N
**Cons/Risks:** [from solution evaluation]
**Reason Deferred:** [user's stated reason]
**Context:** [enough detail to pick up cold]
**Beads ID:** [id]

### 4. Loop Behavior

When looping back to Stage 1 or 2:
- Only affected subset is re-investigated/re-solutioned
- Previous work on unaffected items preserved
- Beads issues updated (not recreated)
- Memory files get new sections appended
- After subset completes, re-present FULL summary with updated items

### 5. Record Decisions

Update project.md:

## Stage 3: Approved Solutions
- Issue 1: Solution 1a [beads-id] — APPROVED
- Issue 2: Solution 2b [beads-id] — APPROVED
- Issue 3: [beads-id] — DEFERRED (reason)

No git checkpoint — decisions recorded in project.md and beads.
