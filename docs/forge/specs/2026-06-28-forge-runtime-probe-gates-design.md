# Design: self-adjusting runtime + structural probe gates

**Date:** 2026-06-28  
**Status:** Draft  
**Scope:** large (runtime layout + probes + gates)  
**Motivation:** Codex transcript (`rollout-2026-06-26`) — read-only mount aliases, silent probe hangs, evaluate loops, agent bypass.

---

## Goals

1. **Repo-only runtime** — all Forge state under `<repo>/.forge/` (sessions, memory, state, sidecars).
2. **Self-adjusting paths** — pick writable git-root alias automatically; no user `FORGE_REPO`.
3. **Loud probes** — every probe step prints `STRUCTURAL PROBES — {STATUS}`; sidecar always has `status`.
4. **Pause on non-OK** — `FAILED` | `SKIPPED` | `DEGRADED` | `DEFERRED` → gate blocks next step until user chooses.
5. **No agent bypass** — completion gates reject “structurally clean” claims without `OK` or recorded override.

## Non-goals

- Moving skill installs out of `~/.codex/skills` (still user-home; runtime stays in repo).
- Replacing `forge takeover` or individual workflow skills.
- Auto-ship on probe override.

---

## `.forge/` layout

```
.forge/
  adaptation.json
  sessions/{id}/session.json, handoff.md, sidecars/
  memory/
  state/          # resume-context, graphify prefs/status
```

Migrate existing `.codex/forge/` → `.forge/` once on first step 1; stop writing to `.codex/forge/`.

---

## Runtime adaptation (RAL)

On step 1, probe cwd/git aliases for writability; cache in `.forge/adaptation.json`. All `mkdir`/`open(w)` use `writable_repo_root`. Emit one informational line when remapping (`FORGE_ADAPT:`). If no writable alias → **exit 1** with clear error (not silent fallback).

---

## Structural probes

| Status | Meaning | Next step |
|--------|---------|-----------|
| `OK` | Ran successfully | Continue |
| `FAILED` | Tool error or fail | **Gate — pause** |
| `SKIPPED` | Could not run | **Gate — pause** |
| `DEGRADED` | Partial scope / timeout | **Gate — pause** |
| `DEFERRED` | Inline skipped; ship must run | **Gate — pause** |

Sidecar: `.forge/sessions/{id}/sidecars/.structural-probes.json`  
Gate sidecar: `.structural-probes-gate.json` (`gate_state`: `pending` | `cleared` | `overridden` | `deferred_to_ship`)

**User choices (multiselect):** retry | continue with override reason | defer to ship | stop (`forge takeover`)

Next `forge <skill> --step N` re-validates gate; pending → exit 1 and reprint gate.

**CI:** non-interactive → exit 1 on non-OK (loud banner, no auto-bypass).

---

## Implementation waves

| Wave | Work |
|------|------|
| **W0** | `.forge`-only `runtime_root()` + one-time migration + test/doc sweep |
| **W1** | RAL wrapping existing `repo_paths` (writable alias cache in `.forge/adaptation.json`) |
| **W2** | Loud probe banners + shared gate (refactor `code_review/structural_probes_gate.py`) + user pause |
| **W3** | Probe timeouts; ship runs deferred pass; CI override flags |
| ~~W4~~ | *Deferred:* intent router (“loop until clean”) — follow-up after W0–W2 ship |
| **W4** | Codex/Cursor/Claude template + prompt path updates (`.forge/`) |

**Ship order:** W0 → W1 → W2 → W3 → W4. **Semver:** minor if migration reads both trees; **major** if old `.codex/forge` writes are removed without dual-read period.

## Out of scope (v1)

- Natural-language intent routing / evaluate-loop detection (use `forge takeover` manually until W4 follow-up).
- Moving Codex skill install out of `~/.codex/skills`.

---

## Key files

- `scripts/shared/runtime_layout.py` — sole `.forge` root
- `scripts/shared/runtime_adaptation.py` (new)
- `scripts/shared/repo_paths.py` — alias map consumed by RAL
- `scripts/shared/structural_probes.py` — banners, status, never empty skip output
- `scripts/shared/structural_probes_gate.py` (new, split from code_review)
- `scripts/shared/orchestrator.py` — gate block + `require_confirmation`
- `forge_next/cli_install_codex.py` — bundle templates
