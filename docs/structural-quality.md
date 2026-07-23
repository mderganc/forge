# Structural quality tools (knip, madge, jscn, pyscn, skylos)

Forge installs CLI probes and teaches the same lenses earlier via **`templates/structural-build-charter.md`** (design → plan → evaluate-pre → implement). Probes **verify** charter compliance; code-review is residual, not the first discovery of complexity/clone debt.

## Skill-chain roles

| Skill | Role |
|-------|------|
| **design** | Prefer shapes that satisfy the charter when scoring solutions |
| **plan** | Heavy charter callouts on steps 2–4; **step 2** auto-runs jscn/pyscn baseline (advisory, non-blocking) |
| **evaluate pre** | Critique the plan against the charter (completeness) |
| **implement** | Charter while writing; **step 4** (wave review) auto-runs full stack probes |
| **evaluate post / code-review** | Residual Pass B; eight agents on code-review step 3 / evaluate review step 1 |
| **test** | verification-protocol Level 5 names knip/madge/jscn/pyscn |

## Install

With the Forge launcher:

```bash
pipx install forge-next
forge install   # installs knip, madge, jscn, pyscn, and skylos by default; warns if any are missing
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

## Command overrides (trust boundary)

Forge may honor these environment variables when spawning probe or graph commands (values are split with `shlex` where supported):

| Variable | Effect |
|----------|--------|
| `FORGE_GRAPHIFY_COMMAND` | Replace default `graphify` CLI invocation |
| `FORGE_PYSCN_COMMAND` / `FORGE_JSCN_COMMAND` / `FORGE_SKYLOS_COMMAND` / … | Override structural probe binaries |

Use only in trusted CI or local dev. Do not set from untrusted input.

Skip in CI or automation:

```bash
export FORGE_SKIP_STRUCTURAL_TOOLS=1
```

Inventory scans use a pruned directory walk (they do **not** descend into `.venv`, `node_modules`, `graphify-out`, or vendored `forge_next-0.*` trees). If step 3/4 still feels slow, set `FORGE_SKIP_STRUCTURAL_TOOLS=1` as above.

**Repo hygiene:** Forge's own Python tree uses [`.pyscn.toml`](../.pyscn.toml) (`max_complexity = 15`) and [`docs/pyscn-quality-disposition.md`](pyscn-quality-disposition.md) for how to treat complexity/clone findings in CI and refactors.

## What gets installed

| Tool | Stack | Install method |
|------|--------|----------------|
| **knip** | JavaScript / TypeScript | `npm install` under `~/.forge/structural-tools` (Windows) or `~/.local/share/forge/structural-tools` (Unix) |
| **madge** | JS/TS dependency graph | Same npm prefix |
| **jscn** | JS/TS complexity, clones, deps, dead code | Same npm prefix (`@msderganc/jscn` on npm; [msderganc/jscn](https://github.com/msderganc/jscn)) |
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

**Teach then verify:** agents follow `templates/structural-build-charter.md` during design/plan/implement. Probes measure those lenses.

| When | Behavior |
|------|----------|
| **plan step 2** | Auto-runs **jscn and/or pyscn** only (complexity/clones). Advisory — does not block architecture |
| **implement step 4** | Auto-runs stack-applicable probes (full set). Soft confirmation if probes fail to run |
| **code-review step 3** | **On by default** — runs stack-applicable probes unless `--no-structural`; hard gate for steps 4+ until complete |
| **evaluate** post step 4 / review step 1 | Inventory/plan by default; auto with `FORGE_STRUCTURAL_PROBES_AUTO=1` |

### Code review: `--effort` and structural probes (always on)

`forge code-review` takes **`--effort light|standard|thorough`** (`--quick` is an alias for `--effort light`). Structural probes at step 3 are **on by default**; opt out only with **`--no-structural`**. Fan-out scales with effort (not whether probes run):

| Effort | Reviewer team | Structural fan-out |
|--------|----------------|--------------------|
| `light` | Architect + QA Reviewer | S3/S4/S8 quick subset |
| `standard` (default) | Architect + QA (+ Security when auth/data) | S3/S4/S8 quick subset |
| `thorough` | Full six-agent team | Full S1–S8 |

Escalate to `thorough` only when ≥2 corroborating signals agree (scope keyword **and** file breadth). Prefer **diff-scoped** findings; unrelated hits are advisory.

When structural probes are **disabled** via `--no-structural`, step 3 skips probes/eight-agents entirely and steps 4–6 proceed without a probe gate.

**The gate blocks on probe execution status, not on findings.** `probe_status` values that hold the gate `pending` are execution outcomes — `FAILED`, `SKIPPED`, `DEGRADED`, `DEFERRED` (probes didn't run or didn't finish cleanly) — never the number or severity of findings a probe reports. A probe run that completes and reports findings is `OK` and does not block; re-run step 3 or use `--allow-structural-probes-incomplete` (with override reason + follow-up) only when probes genuinely could not execute.

The **eight Civil Learning subagents** dispatch on **code-review step 3** (when structural is enabled) and **evaluate review step 1** only — default **trio**: S3, S4, S8 (dead code, cycles, AI slop) for light/standard; full eight for thorough (or `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1`). See [`templates/structural-quality-probes.md`](../templates/structural-quality-probes.md).

Skip probes: `FORGE_SKIP_STRUCTURAL_TOOLS=1`. Planning-only: `FORGE_STRUCTURAL_PROBES_MANUAL=1`. Skip eight subagents: `FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS=1`. Full eight-agent dispatch: `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1`.

Example commands:

```bash
npx knip
npx madge --circular src/
pyscn check .
skylos . --json
# or: uvx pyscn@latest analyze --json .
# or: skylos . -a --json
```

## Final report and completion summaries

After probes run (code-review step 3; evaluate post step 4 or review step 1), results live in **`.structural-probes.json`** beside session state.

- **Code-review step 6** and **evaluate final step** append a brief probe summary to orchestrator output.
- **`code-review-report.md`** and evaluate reports must include the full **Structural probes (Pass B)** section (orchestrator fills `{{STRUCTURAL_PROBES_SUMMARY}}` from the sidecar — do not re-run tools at report time).

Implementation: `scripts/shared/structural_probes.py` → `format_probe_summary_markdown()` / `resolve_probe_summary_for_state()`.

## Related

- [Graphify](graphify.md) — codebase navigation (complementary, not a replacement)
- Python hygiene stack (Black, Ruff, mypy, bandit, pre-commit) — configure per target repo
