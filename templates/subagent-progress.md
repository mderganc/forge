# Subagent Progress Reporting

Background Task / `spawn_agent` work must not leave the **main (PM) agent** silent until completion. Cursor does not stream interim subagent chat into the parent; Codex can use `send_input`, but both runtimes share this **file-based** heartbeat.

Apply together with `templates/codex-runtime.md` (lifecycle) and `templates/parallel-dispatch.md` (waves).

## Paths

| Runtime | Progress file |
|---------|----------------|
| Default | `.forge/state/subagent-progress/<agent-or-task-id>.json` |
| Session-scoped (preferred when a Forge session is active) | `<session-dir>/sidecars/subagent-progress/<agent-or-task-id>.json` |

Use a stable id from the dispatch prompt (`agent_id`, Task description slug, or plan task id). Create parent directories as needed.

Cursor also writes live state under `~/.cursor/subagents/` — the parent may Read those files as a supplement, not a replacement for the Forge progress file.

## Schema

```json
{
  "agent_id": "task-3-backend",
  "role": "backend-dev",
  "task": "Task 3 — auth middleware",
  "status": "in_progress",
  "phase": "tdd-red",
  "summary": "Wrote failing test for missing Authorization header",
  "updated_at": "2026-07-11T22:00:00+00:00",
  "blockers": []
}
```

| Field | Values / notes |
|-------|----------------|
| `status` | `started` \| `in_progress` \| `blocked` \| `done` \| `failed` |
| `phase` | Short label (`explore`, `tdd-red`, `tdd-green`, `review`, `merge`, …) |
| `summary` | One sentence the PM can relay to the user |
| `blockers` | List of strings; non-empty when `status` is `blocked` |

## Subagent rules (mandatory)

1. **Write on start** — first action after reading the dispatch: create/update the progress file with `status: started`.
2. **Update at every milestone** — at least when changing phase (e.g. tests written → implementing → suite green → self-review) and at least every ~5–10 tool-heavy steps on long runs. Do not batch silently until the end.
3. **Blocked / failed** — update immediately with `status: blocked` or `failed` and a concrete `summary` + `blockers`.
4. **Done** — set `status: done` with a completion summary **before** the final “report to PM” message.
5. Do **not** rely on chat alone for progress; the parent may only see your final message when you run in the background.

## Parent (PM) rules (mandatory)

1. **Include this protocol in every dispatch prompt** (see snippet below).
2. **Do not go silent** while background agents run: continue other work, and **Read** progress files (and optionally `~/.cursor/subagents/`) when you would otherwise wait. Relay a short status line to the user when `updated_at` / `summary` changes.
3. **Codex:** you may also `send_input` asking for a status pulse if the progress file is stale; still require the file update.
4. **Cursor:** prefer progress-file pulls over polling Task internals; react to completion notifications as today, then `close` / resume per lifecycle rules.
5. On wave or step boundaries, confirm every agent reached `done` or an explicit `blocked`/`failed` before closing agents.

## Dispatch snippet (paste into spawn / Task prompts)

```text
Progress reporting (required): follow templates/subagent-progress.md.
Write/update `.forge/state/subagent-progress/<your-id>.json` on start, at each
milestone (or every ~5–10 heavy steps), on blockers, and when done. Do not stay
silent until the final report — the parent only sees background completion at the end.
```

## What “regularly” means

| Cadence | When |
|---------|------|
| Immediate | Start, blocker, failure, completion |
| Milestone | Phase changes in the assigned protocol (TDD steps, review stages, investigation phases) |
| Heartbeat | Long open-ended work with no phase change yet — refresh `summary` + `updated_at` so the parent can show progress |

Completion-only reporting is a protocol violation.
