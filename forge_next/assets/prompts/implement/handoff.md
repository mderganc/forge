# Phase 7: Handoff

Write handoff and render dashboard.

## Handoff Content

Write `{{MEMORY_DIR}}/handoff-implement.md` with:
- Feature branch name
- Files created/modified (list)
- Tests written (list)
- Findings resolved during implementation
- Documentation produced
- Beads state
- Structural compliance / residual `J*`/`P*` for code-review (`templates/structural-build-charter.md`)

## Dashboard

Render skill completion dashboard with:
- Skill name and status
- Start and completion timestamps
- Agents dispatched
- Findings summary (open vs resolved)
- Beads state
- Quick mode indicator

## Git Checkpoint

```
git add {{RUNTIME_DIR}}/ && git commit -m "workflow: implementation complete"
```

## Closure checklist (before merge / PR)

- [ ] **Branch:** on the intended feature branch; unrelated work reverted or on another branch.
- [ ] **Tests:** suite relevant to this change is green (or documented exceptions).
- [ ] **Worktree:** if you used `git worktree`, remove or archive the extra checkout when done (`git worktree remove …` when appropriate).
- [ ] **PR / link:** open or update the pull request (or note merge target) in handoff memory.

## Suggested Next

`code-review`
