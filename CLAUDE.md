## graphify

This project has a knowledge graph at `graphify-out/` with god nodes, community structure, and cross-file relationships.

### Repo rules (always)

- ALWAYS read `graphify-out/GRAPH_REPORT.md` before reading source files, running grep/glob searches, or answering architecture questions. The graph is your primary map of the codebase.
- IF `graphify-out/wiki/index.md` EXISTS, navigate it instead of reading raw files.
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse EXTRACTED + INFERRED edges instead of scanning files.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

### Forge workflow skills (`forge:*` slash commands)

When you run a Forge workflow (`/forge:develop`, `/forge:plan`, etc.):

1. **Follow every GRAPHIFY block** printed at the top of each `forge … --step` output (when `graphify-out/` exists).
2. **Hard rule — Graphify** in each slash command body repeats the same contract.
3. Claude hooks (if installed via `forge claude-graphify`) remind you on **Grep**, **Glob**, **Read**, and search-like **Bash** before raw search.

Install or refresh hooks after upgrading **forge-next**:

```bash
pipx upgrade forge-next
forge claude-graphify
```

Full documentation: [`docs/graphify.md`](docs/graphify.md).  
CI: set `FORGE_SKIP_GRAPHIFY=1` to suppress per-step GRAPHIFY banners.
