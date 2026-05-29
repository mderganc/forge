---
name: forge:ship
description: Commit, push, open or update a PR, merge, and publish — finalize coding without retyping git steps.
---

## Hard rule — Graphify

If `graphify-out/` exists and you changed code this session: run `graphify update .` before committing.

## What to tell the user first

- **Ship** finalizes your work: preflight, optional commit, push, PR, and (only if you ask) merge or publish.
- Say what you want if not everything: e.g. "commit only", "open PR", "publish PyPI".

## What you run (agent)

Follow **`.cursor/skills/ship/SKILL.md`** in the Forge repo (or a personal copy under `~/.cursor/skills/ship/`). Use git and `gh`; obey commit/PR safety (no secrets, no force-push to main unless explicit).

Summarize: commit SHA, branch, PR URL, merge/publish status.

---
