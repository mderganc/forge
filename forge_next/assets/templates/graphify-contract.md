## Graphify (codebase map)

When **`graphify-out/`** exists:

1. **Refresh at ship** — run **`forge ship --step 1`** or **`$forge:ship`** before commit/PR/publish (background `forge graphify refresh` + GRAPHIFY banner; do not wait).
2. During investigation you may read **`graphify-out/GRAPH_REPORT.md`** or use **`graphify query`**, **`graphify path`**, **`graphify explain`** instead of blind grep — optional, not injected on every workflow step.
3. If **`graphify-out/wiki/index.md`** exists, prefer the wiki over bulk raw reads when navigating.

Workflow skills (`develop`, `plan`, `implement`, `code-review`, `test`, `diagnose`, `evaluate`) **do not** print per-step GRAPHIFY blocks.

Disable: **`FORGE_SKIP_GRAPHIFY=1`** or **`forge graphify off`**.
