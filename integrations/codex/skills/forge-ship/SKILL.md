---
name: forge:ship
description: >-
  Finalize coding work: commit, push, open/update PR, merge, and publish
  (PyPI/npm/etc.). Use when the user says ship, finalize, release, commit and
  push, open a PR, merge, or publish after implementation or review.
---

# forge:ship — finalize coding

No CLI orchestrator — execute the **ship** workflow in the agent using git and `gh`.

Read and follow the full procedure in the Forge repo skill:

`.cursor/skills/ship/SKILL.md`

(relative to the Forge checkout, or the copy under `~/.cursor/skills/ship/` if installed personally.)

## Quick contract

1. Preflight: `git status`, diff, log, branch tracking; `gh pr view` if relevant.
2. **Commit** only when the user asked to commit or ship; never commit secrets.
3. **Push** / **PR** / **merge** / **publish** only when requested or part of full **ship**.
4. Use **`gh`** for GitHub; on Windows use `--body-file` for PR bodies if heredoc is awkward.
5. After code edits with `graphify-out/`, run **`graphify update .`** before commit.
6. **forge-next** releases: bump `pyproject.toml` version per **AGENTS.md**, then build + `twine upload` when publishing.

Report: commit SHA, branch, PR URL, merge/publish outcome.
