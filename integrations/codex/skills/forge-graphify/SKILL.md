---
name: forge:graphify
description: Optional Graphify integration — refresh codebase index metadata for forge resume, or manage a fail-soft git post-commit hook. Use when setting up or troubleshooting Graphify with Forge.
---

<invoke cmd="forge graphify refresh" />

Subcommands (run via launcher with the same `forge graphify …` prefix): `refresh` (default above), `install-hook`, `uninstall-hook`. Pass `--repo` when the project root is not the current directory.
