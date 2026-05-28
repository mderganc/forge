# Structural quality probes (knip, madge, pyscn)

Use during **code-review** and **evaluate** Pass B (engineering quality). Pass A (spec/intent) is unchanged.

Install tools once: `forge install --structural-tools` or `forge structural-tools install`. Suppress with `FORGE_SKIP_STRUCTURAL_TOOLS=1`.

## When to run

| Skill | Step | Mode |
|-------|------|------|
| code-review | 3 (team dispatch) | all |
| evaluate | 4 | post |
| evaluate | 1 | review |

Read **`.structural-probes.json`** beside the workflow state file when the orchestrator prints a probe banner. Cite probe IDs (e.g. `K1`, `M2`, `P3`) in formal findings.

## Stack detection

| Signal | Run |
|--------|-----|
| `package.json` at repo root or under `apps/`, `packages/`, `integrations/` | knip, madge |
| `pyproject.toml` or meaningful `**/*.py` tree | pyscn |

If a stack is absent, expect `status: skip` in the sidecar — not a failure.

## Commands (override with env)

| Tool | Default resolution | Example |
|------|-------------------|---------|
| knip | `FORGE_KNIP_COMMAND` or Forge manifest / npx | `knip` (repo may need `knip.json`) |
| madge | `FORGE_MADGE_COMMAND` | `madge --circular src/` (adjust entry) |
| pyscn | `FORGE_PYSCN_COMMAND` | `pyscn check .` or `uvx pyscn@latest analyze --select deadcode,deps,clones .` |

**Quick mode:** prefer `pyscn check .` only; skip full `analyze` HTML report unless the user asks.

## Eight review lenses (Civil Learning → Forge roles)

| Lens | Focus | Lead reviewer | Tool signal |
|------|--------|---------------|-------------|
| 1 DRY / duplication | Repeated logic, merge only if simpler | Critic | pyscn clones |
| 2 Shared types | Duplicate/inconsistent types | Architect | mypy/tsc + graphify |
| 3 Dead code | Unused exports, files, unreachable code | Investigator | knip, pyscn deadcode |
| 4 Circular deps | Import cycles | Architect | madge `--circular` |
| 5 Weak types | `any`, `unknown`, loose casts | Architect | mypy, tsc |
| 6 Error handling | Silent catch, swallowed errors | Security, Critic | manual + bandit |
| 7 Legacy paths | Dead branches, fallback noise | Investigator | pyscn CFG dead code |
| 8 AI slop | Noise comments, stubs, TODO theater | Critic, Doc-writer | manual |

Default severity for raw tool hits: **warning** until a reviewer confirms **critical**.

## False-positive triage

- **knip:** barrel `index.ts`, framework entry files, test-only imports, monorepo workspace roots
- **madge:** type-only imports, bundler aliases — confirm with a second tool or import trace
- **pyscn:** `TYPE_CHECKING`, decorators (routes, pytest fixtures), `__all__`, dynamic imports

Do not recommend deletion without confirming references (grep + graphify path/query, not grep alone).

## Sidecar schema (`.structural-probes.json`)

```json
{
  "generated_at": "2026-01-01T00:00:00+00:00",
  "stack": {"python": true, "node": false},
  "probes": [
    {
      "tool": "pyscn",
      "status": "pass",
      "command": ["pyscn", "check", "."],
      "summary": "exit 0",
      "findings": [
        {"id": "P1", "severity": "warning", "path": "pkg/mod.py", "detail": "..."}
      ]
    }
  ]
}
```

`status`: `pass` | `fail` | `skip`.

## Related (repo-local, not Forge-installed)

Per-project hygiene: Black/Ruff, isort, mypy, pylint, bandit, pre-commit — configure in the target repo; see `templates/verification-protocol.md` Level 5.
