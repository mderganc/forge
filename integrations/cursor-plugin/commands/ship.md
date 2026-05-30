---
name: forge:ship
description: Commit, push, PR, merge, publish — refresh Graphify at ship time, then finalize git steps.
---

## Graphify (first when `graphify-out/` exists)

```bash
forge ship --step 1
```

Workflow skills no longer print GRAPHIFY per step; refresh runs here before commit.

## What to tell the user first

- **Ship** finalizes your work: graphify preflight (optional), git status, commit, push, PR, merge/publish only if asked.
- Say what you want if not everything: e.g. "commit only", "open PR", "publish PyPI".

## What you run (agent)

1. **`forge ship --step 1`** when `graphify-out/` exists (unless `FORGE_SKIP_GRAPHIFY=1`).
2. Follow **`.cursor/skills/ship/SKILL.md`** for git/`gh` steps.

Present results in prose with links (PR URL, commit SHA).

---
