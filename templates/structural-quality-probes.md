# Structural quality probes (knip, madge, pyscn)

Use during **code-review** and **evaluate** Pass B (engineering quality). Pass A (spec/intent) is unchanged.

Install tools once: `forge install` (default) or `forge structural-tools install`. Skip with `forge install --skip-structural-tools` or `FORGE_SKIP_STRUCTURAL_TOOLS=1`.

## Agent-driven selection (default)

On **code-review step 3**, **evaluate post step 4**, and **evaluate review step 1**, the orchestrator writes:

| File | Purpose |
|------|---------|
| `.structural-probes-inventory.json` | Repo facts (counts, `package.json` roots, stack hints) |
| `.structural-probes-plan.json` | **You** choose `tools`, roots, `reasoning` (heuristic draft included) |
| `.structural-probes.json` | Tool output after you run probes |

**Workflow:**

1. Read the inventory (and `graphify-out/GRAPH_REPORT.md` when present).
2. Decide which tools apply to the **app under review** (not vendored Forge/tooling trees).
3. Edit `.structural-probes-plan.json` — set `tools` to any subset of `knip`, `madge`, `pyscn` (use `[]` to skip all).
4. Run: `forge structural-probes run --state-dir <state-dir>`
5. Read `.structural-probes.json` and cite probe IDs (`K1`, `M2`, `P3`) in findings.

**Automation / CI:** set `FORGE_STRUCTURAL_PROBES_AUTO=1` to apply the heuristic plan and run probes without the agent step.

## Probe plan schema (`.structural-probes-plan.json`)

```json
{
  "tools": ["knip", "madge"],
  "node_root": "client",
  "python_root": null,
  "scope_paths": ["client/src"],
  "reasoning": "TS app lives under client/; root pyproject is tooling only — skip pyscn.",
  "source": "agent"
}
```

## Tool guide

| Tool | When to include | Signal |
|------|-----------------|--------|
| **knip** | JS/TS package with real app code | Unused exports/files |
| **madge** | Same Node root as knip | Circular imports |
| **pyscn** | Meaningful Python **application** tree | Dead code, clones, complexity |

Do not run pyscn on repos where Python is only scripts/tooling next to a TS app.

## Commands (override with env)

| Tool | Default resolution | Example |
|------|-------------------|---------|
| knip | `FORGE_KNIP_COMMAND` or Forge manifest / npx | `knip` (repo may need `knip.json`) |
| madge | `FORGE_MADGE_COMMAND` | `madge --circular src/` |
| pyscn | `FORGE_PYSCN_COMMAND` | `pyscn check .` |

**Quick mode:** prefer `pyscn check .` only; skip full `analyze` HTML unless the user asks.

## Eight parallel subagents (Civil Learning)

**Default Pass B dispatch:** spawn **eight parallel subagents** with the Civil Learning master prompt and per-agent missions — see **`templates/structural-quality-eight-agents.md`**. The orchestrator prints the dispatch table on code-review step 3 and evaluate post step 4 / review step 1.

| Lens | Subagent ID | Tool signal |
|------|-------------|-------------|
| 1 DRY / duplication | S1 | pyscn clones |
| 2 Shared types | S2 | mypy/tsc + graphify |
| 3 Dead code | S3 | knip, pyscn deadcode |
| 4 Circular deps | S4 | madge `--circular` |
| 5 Weak types | S5 | mypy, tsc |
| 6 Error handling | S6 | manual + bandit |
| 7 Legacy paths | S7 | pyscn CFG dead code |
| 8 AI slop | S8 | manual |

After the eight agents finish, the **core Forge team** (Architect, Security, QA, etc.) runs for Pass A and synthesis — they consume `.structural-eight-agents.json` instead of redoing the same lenses.

Default severity for raw tool hits: **warning** until a reviewer confirms **critical**.

## False-positive triage

- **knip:** barrel `index.ts`, framework entry files, test-only imports, monorepo workspace roots
- **madge:** type-only imports, bundler aliases — confirm with a second tool or import trace
- **pyscn:** `TYPE_CHECKING`, decorators (routes, pytest fixtures), `__all__`, dynamic imports

Do not recommend deletion without confirming references (graphify path/query preferred over blind grep).

## Results sidecar (`.structural-probes.json`)

`status` per tool: `pass` | `fail` | `skip` (including `not selected in probe plan`).

## Related (repo-local, not Forge-installed)

Per-project hygiene: Black/Ruff, isort, mypy, pylint, bandit, pre-commit — see `templates/verification-protocol.md` Level 5.
