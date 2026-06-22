---
description: |
  Infer epic from repo state and drive Forge skills until ship-ready.
  Replaces resume and iterate.
---

# Forge Takeover

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

<invoke cmd="forge takeover" />

| Argument | Purpose |
|----------|---------|
| `--issue` | GitHub issue number or URL |
| `--design` | Path to design spec |
| `--goal` | Override default ship-ready goal |
| `--cleanup` | Legacy state file cleanup (dry-run) |

Polls `.takeover-gates/*.json` between child skills. See `forge takeover --help`.
