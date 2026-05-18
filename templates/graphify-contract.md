## Graphify (codebase map)

When **`graphify-out/`** exists, treat the knowledge graph as the primary map:

1. Read **`graphify-out/GRAPH_REPORT.md`** before grep/glob/semantic search or bulk source reads for architecture questions.
2. If **`graphify-out/wiki/index.md`** exists, navigate the wiki instead of raw files.
3. For cross-module relationships, prefer **`graphify query`**, **`graphify path`**, or **`graphify explain`**.
4. After editing tracked code in this session, run **`graphify update .`** (AST-only, no API cost).

Forge step output includes a **GRAPHIFY** banner on every step when an index is present.
