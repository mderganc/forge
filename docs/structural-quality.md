# Structural quality tools (knip, madge, pyscn, skylos)

Forge can install CLI probes used during **code-review** and **evaluate** Pass B (engineering quality): unused exports, circular dependencies, and Python structural analysis.

## Install

With the Forge launcher:

```bash
pipx install forge-next
forge install   # installs knip, madge, pyscn, and skylos by default; warns if any are missing
```

Skip during install:

```bash
forge install --skip-structural-tools
# or: export FORGE_SKIP_STRUCTURAL_TOOLS=1
```

Or install / refresh tools only:

```bash
forge structural-tools install
```

From a Forge source checkout (no global `forge` yet):

```bash
# Linux/macOS
./scripts/install/structural_tools.sh

# Windows PowerShell
./scripts/install/structural_tools.ps1
```

Skip in CI or automation:

```bash
export FORGE_SKIP_STRUCTURAL_TOOLS=1
```

Inventory scans use a pruned directory walk (they do **not** descend into `.venv`, `node_modules`, `graphify-out`, or vendored `forge_next-0.*` trees). If step 3/4 still feels slow, set `FORGE_SKIP_STRUCTURAL_TOOLS=1` as above.

## What gets installed

| Tool | Stack | Install method |
|------|--------|----------------|
| **knip** | JavaScript / TypeScript | `npm install` under `~/.forge/structural-tools` (Windows) or `~/.local/share/forge/structural-tools` (Unix) |
| **madge** | JS/TS dependency graph | Same npm prefix |
| **pyscn** | Python clones / complexity / CFG dead code | `pipx install pyscn`, else `uv tool install pyscn`, else `uvx pyscn@latest` |
| **skylos** | Python dead code, SAST, secrets, quality | `pipx install skylos`, else `uv tool install skylos`, else `uvx skylos@latest` |

Install also warms the **npx** cache for pinned knip/madge versions when `npx` is available.

Manifest: `structural-tools.json` next to the prefix (see `forge doctor` → `structural_tools`).

## Verify

```bash
forge doctor
```

Override commands if needed:

- `FORGE_KNIP_COMMAND`
- `FORGE_MADGE_COMMAND`
- `FORGE_PYSCN_COMMAND`
- `FORGE_SKYLOS_COMMAND`
- `FORGE_SKYLOS_AUDIT` (set to `1` for full `skylos -a` on code-review step 3)

## Usage in workflows

During **forge code-review** step 3, the orchestrator **runs** stack-applicable probes and writes **`.structural-probes.json`** (**pyscn+skylos** when Python is present; **knip+madge** when Node is present). Planning-only: `FORGE_STRUCTURAL_PROBES_MANUAL=1`. **Evaluate** (post step 4, review step 1) still uses inventory/plan unless `FORGE_STRUCTURAL_PROBES_AUTO=1`. The **eight Civil Learning subagents** dispatch on **code-review step 3** and **evaluate review step 1** only (default **S3/S4/S8**). See [`templates/structural-quality-probes.md`](../templates/structural-quality-probes.md).

Skip probes: `FORGE_SKIP_STRUCTURAL_TOOLS=1`. Planning-only on code-review step 3: `FORGE_STRUCTURAL_PROBES_MANUAL=1`. Skip eight subagents: `FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS=1`. Full eight-agent dispatch: `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1`.

Example commands:

```bash
npx knip
npx madge --circular src/
pyscn check .
skylos . --json
# or: uvx pyscn@latest analyze --json .
# or: skylos . -a --json
```

## Related

- [Graphify](graphify.md) — codebase navigation (complementary, not a replacement)
- Python hygiene stack (Black, Ruff, mypy, bandit, pre-commit) — configure per target repo
