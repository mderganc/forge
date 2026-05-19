---
name: forge:graphify
description: Optional Graphify setup — refresh index metadata for forge resume or manage the post-commit hook.
---

## Hard rule — what the user sees

**Never show terminal commands** unless they explicitly ask for copy-paste.

## What to tell the user first

- **Graphify** is optional: it feeds **codebase structure** into `forge resume` and enforces **GRAPHIFY** blocks on every workflow step when `graphify-out/` exists.
- Default flow: **refresh** metadata once per clone; optionally **install-hook** so each commit re-refreshes in the background (fail-soft).
- **Codex / Claude policy:** `forge codex-agents --force`, `forge claude-graphify` (see **`docs/graphify.md`**).
- They need Graphify installed **or** **`FORGE_GRAPHIFY_COMMAND`**. Full guide: **`docs/graphify.md`** in the Forge repo.

## What you run (agent)

Invoke **graphify** through the launcher: default **refresh**; use **install-hook** or **uninstall-hook** when the user wants the git hook added or removed. Use **`--repo`** if working outside the project root. Paraphrase outcomes—do not paste raw argv.

---
