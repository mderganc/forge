# Graphify integration (optional)

Forge can surface **codebase graph context** in `forge resume` when Graphify
artifacts exist (for example `GRAPH_REPORT.md` or `graphify-out/GRAPH_REPORT.md`).

Graphify is **optional**. Core Forge workflows work without it.

## Practical setup (simple)

Think of it in three layers:

1. **You install Graphify** the way its docs say (same as any other CLI tool).
2. **You tell Forge how to run it** — either the `graphify` command is on your
   `PATH`, or you set **`FORGE_GRAPHIFY_COMMAND`** to the exact command you use
   to rebuild the graph for this repo.
3. **You run Forge once per clone:** `forge graphify refresh` (from the repo
   root, or pass `--repo` with the path). Forge writes a small
   **`graphify-status.json`** file next to your other Forge state. `forge resume`
   reads that file and any `GRAPH_REPORT.md` it finds — it does not guess your
   whole repo by itself.

Optional fourth step: **`forge graphify install-hook`** adds a git **post-commit**
snippet so step 3 re-runs after each commit, without ever failing the commit.

## Install Graphify

Install the Graphify tooling your project uses (CLI name may vary). If the
`graphify` executable is on `PATH`, Forge can invoke it during refresh.

Alternatively, set a full command line:

- **`FORGE_GRAPHIFY_COMMAND`** — shell command to rebuild the graph (split with
  POSIX rules). Example: `graphify build` or a project-specific wrapper.

## Refresh status file

From the target repository root:

- Run **Graphify refresh** via the Forge launcher so `.codex/forge/state/graphify-status.json`
  is updated (fail-soft: failures are recorded, not thrown).

## Auto-refresh on commit

Install a **fail-soft** `post-commit` hook fragment:

- Installs a marked block into `.git/hooks/post-commit` that runs the refresh
  command after each commit (`|| true` so commits never fail because of Graphify).

Uninstall removes only the Forge-managed block.

## `forge install` onboarding

Running **install** for Cursor/Claude/Codex integrations prints short Graphify
next steps so new users see how to wire codebase context into `forge resume`.
