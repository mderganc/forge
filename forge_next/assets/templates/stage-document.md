# Stage 7 — Documentation & Merge

## Purpose
Produce documentation for the completed feature and handle feature branch integration.

## Lead Agent
**Doc Writer** — writes documentation

## PM Actions

### 1. Assign Documentation

Send to Doc Writer:

> **Task: Write documentation for completed feature**
>
> Read ALL memory files in `.codex/forge-codex/memory/`.
> Read the actual implementation code to verify.
> Use Codex runtime conventions from `templates/codex-runtime.md`.
>
> Produce as appropriate:
> - User-facing docs (how to use)
> - Developer docs (architecture, patterns, extension points)
> - API docs (endpoints, contracts, examples)
> - README updates (if setup/usage changed)
> - Changelog entry
> - Inline comments ONLY where logic is non-obvious
>
> Record whether you edited source files.

### 2. Review Loop

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Tech Writer | Docs match reality? Examples accurate? |
| Cross-review | QA Reviewer | Examples work? Terminology consistent? Undocumented behavior? |
| PM validation | PM | Coverage for users and developers? |

### 3. Source-File Change Gate

If Doc Writer edited ONLY docs/README/changelog:
  → Proceed to merge

If ANY source file edited (including inline comments):
  → Re-run Architect review
  → Re-run QA review
  → Critic challenge
  → Must reach clean before proceeding

### 4. Feature Branch Finalization

**All autonomy levels pause here.** PM asks:

Feature branch forge/[feature-name] is ready. How to integrate?

  1. Merge to main (squash)
  2. Merge to main (merge commit)
  3. Rebase onto main
  4. Create a pull request for external review
  5. Leave the branch as-is (I'll handle it)

Enter 1-5:

If PR (option 4): gh pr create with Stage 6 implementation summary as body.

### 5. Completion

Write to project.md:

## [YYYY-MM-DD HH:MM] Development Complete

### What was built
[summary]

### Team composition
[agents activated and why]

### Workflow stats
- Stages completed: 7
- Total review rounds: [count]
- Findings surfaced: [count]
- Findings resolved: [count]
- Items deferred to backlog: [count]
- Autonomy level: [level]

### Key decisions
[3-5 decisions with rationale]

### Files modified
[list]

### Remaining risks
[accepted risks]

### Beads epic
[id] — [N] children, [N] closed, [N] deferred

Update beads:
bd comments add [epic-id] "Development complete. [stats]"
bd close [epic-id] --reason "Feature complete"

### 6. Final Git

git add .codex/forge-codex/
git commit -m "workflow: Stage 7 complete — [feature name] documented"

Report to user:
Development complete. Backlog items (if any) are in .codex/forge-codex/backlog.md
and can be picked up in a future session. Run `resume` to continue forge-codex work.
