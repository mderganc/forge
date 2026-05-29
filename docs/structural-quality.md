# Structural quality tools (knip, madge, pyscn)

Forge can install CLI probes used during **code-review** and **evaluate** Pass B (engineering quality): unused exports, circular dependencies, and Python structural analysis.

## Install

With the Forge launcher:

```bash
pipx install forge-next
forge install   # installs knip, madge, and pyscn by default; warns if any are missing
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

## What gets installed

| Tool | Stack | Install method |
|------|--------|----------------|
| **knip** | JavaScript / TypeScript | `npm install` under `~/.forge/structural-tools` (Windows) or `~/.local/share/forge/structural-tools` (Unix) |
| **madge** | JS/TS dependency graph | Same npm prefix |
| **pyscn** | Python structure / dead code / clones | `pipx install pyscn`, else `uv tool install pyscn`, else `uvx pyscn@latest` |

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

## Usage in workflows

During **forge code-review** (step 3) and **forge evaluate** (post step 4, review step 1), the orchestrator runs probes when tools are available and writes **`.structural-probes.json`** beside the session state. Agents follow [`templates/structural-quality-probes.md`](../templates/structural-quality-probes.md) (eight review lenses, triage rules, sidecar schema).

Example commands:

```bash
npx knip
npx madge --circular src/
pyscn check .
# or: uvx pyscn@latest analyze --json .
```

## Related

- [Graphify](graphify.md) — codebase navigation (complementary, not a replacement)
- Python hygiene stack (Black, Ruff, mypy, bandit, pre-commit) — configure per target repo
