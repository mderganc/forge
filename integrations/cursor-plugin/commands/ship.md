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

Follow **`.cursor/skills/ship/SKILL.md`** in this repo (or `~/.cursor/skills/ship/` if copied there). Use git and `gh`; do not skip safety rules (no secret commits, no force-push to main unless explicit).

Present results in prose with links (PR URL, commit SHA) — argv is fine for ship since the user expects git operations.

---
