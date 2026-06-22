---
name: forge:graphify
description: Graphify setup — refresh index for forge takeover, post-commit hook, or troubleshooting. Ship prints the GRAPHIFY banner; workflow steps use background refresh; see docs/graphify.md.
---

<invoke cmd="forge graphify refresh --background" />

Subcommands: `refresh` (default), `install-hook`, `uninstall-hook`. Pass `--repo` when not at the project root.

When `graphify-out/` exists, workflow skills enforce reading `GRAPH_REPORT.md` before codebase search. Claude: `forge claude-graphify`. Codex: `forge codex-agents --force`. Full guide in Forge repo **`docs/graphify.md`**.
