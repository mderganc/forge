# Structural quality probes (knip, madge, pyscn, skylos)

Use during **code-review** and **evaluate** Pass B (engineering quality). Pass A (spec/intent) is unchanged.

Install tools once: `forge install` (default) or `forge structural-tools install`. Skip with `forge install --skip-structural-tools` or `FORGE_SKIP_STRUCTURAL_TOOLS=1`.

## Code-review step 3 (default: orchestrator runs probes)

On **code-review step 3**, the orchestrator **runs** stack-applicable probes before printing the step body and writes **`.structural-probes.json`**. **pyscn and skylos** run when the repo is Python-capable; **knip and madge** only when Node/TS markers are present (not on Python-only trees).

| File | Purpose |
|------|---------|
| `.structural-probes-inventory.json` | Repo facts (counts, `package.json` roots, stack hints) |
| `.structural-probes-plan.json` | Tools/roots used for the run (heuristic + orchestrator filters by stack) |
| `.structural-probes.json` | **Primary input** — probe output; cite `P*` / `Y*` / `K*` / `M*` IDs in Pass B |

**Agent workflow (step 3):**

1. Read **`.structural-probes.json`** from the banner path — **start with pyscn and skylos** on Python repos.
2. Fold probe findings into Pass B before dispatching reviewers or subagents.

**Planning-only:** `FORGE_STRUCTURAL_PROBES_MANUAL=1` — you edit the plan and run `forge structural-probes run --state-dir <state-dir>`.

## Evaluate (agent-driven unless `FORGE_STRUCTURAL_PROBES_AUTO=1`)

On **evaluate post step 4** and **evaluate review step 1**, the orchestrator usually writes inventory + plan; run probes when the banner says planning-only or you need to refresh results.

## Probe plan schema (`.structural-probes-plan.json`)

```json
{
  "tools": ["pyscn", "skylos"],
  "node_root": "frontend",
  "python_root": ".",
  "scope_paths": [
    "benchmark/dashboard/operator_editing_endpoints.py",
    "project_context/storage.py"
  ],
  "exclude_paths": [".venv", "node_modules", ".pyscn", "graphify-out"],
  "reasoning": "Review scoped to changed backend files; avoid .venv, node_modules, graphify-out, .pyscn.",
  "source": "agent"
}
```

## Tool guide

| Tool | When to include | Signal |
|------|-----------------|--------|
| **knip** | JS/TS package with real app code | Unused exports/files |
| **madge** | Same Node root as knip | Circular imports |
| **pyscn** | Meaningful Python **application** tree | Clones, complexity, CFG dead code |
| **skylos** | Same Python root as pyscn | Dead code, secrets, SAST, quality thresholds |

Do not run pyscn/skylos on repos where Python is only scripts/tooling next to a TS app. Do not run knip/madge without a real Node app root.

## Commands (override with env)

| Tool | Default resolution | Example |
|------|-------------------|---------|
| knip | `FORGE_KNIP_COMMAND` or Forge manifest / npx | `knip` (repo may need `knip.json`) |
| madge | `FORGE_MADGE_COMMAND` | `madge --circular src/` |
| pyscn | `FORGE_PYSCN_COMMAND` | `pyscn analyze --json --min-complexity=15 <paths>` (scoped); avoid `check .` on repo root |
| skylos | `FORGE_SKYLOS_COMMAND` | `skylos <paths> --json` (dead code); broad scans add `--exclude-folder` for `.venv`, `node_modules`, `.pyscn`, `graphify-out` |

**Code-review / evaluate:** orchestrator prefers **changed-file** `scope_paths` from git diff. Repo-root Python scans are skipped when large ignored dirs exist. Full skylos audit: `FORGE_SKYLOS_AUDIT=1`.

## Eight parallel subagents (Civil Learning)

**Eight parallel subagents:** see **`templates/structural-quality-eight-agents.md`**. The orchestrator prints the dispatch table on **code-review step 3** and **evaluate review step 1** only (not post-evaluate step 4 — probes only there). Default dispatch is **S3, S4, S8**; set `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1` for all eight. Skip with `FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS=1`.

| Lens | Subagent ID | Tool signal |
|------|-------------|-------------|
| 1 DRY / duplication | S1 | pyscn clones |
| 2 Shared types | S2 | mypy/tsc + graphify |
| 3 Dead code | S3 | knip, pyscn, skylos dead code |
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
- **skylos:** framework entrypoints, FastAPI routes, pytest fixtures, dynamic dispatch — use `--trace` when unsure

Do not recommend deletion without confirming references (graphify path/query preferred over blind grep).

## Results sidecar (`.structural-probes.json`)

`status` per tool: `pass` | `fail` | `skip` (including `not selected in probe plan`).

## Related (repo-local, not Forge-installed)

Per-project hygiene: Black/Ruff, isort, mypy, pylint, bandit, pre-commit — see `templates/verification-protocol.md` Level 5.
