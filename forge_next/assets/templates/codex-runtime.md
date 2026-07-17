# Codex Runtime Conventions

Use these conventions whenever forge-codex instructions mention generic actions like
reading files, editing code, tracking progress, or asking the user questions.

## Tool Mapping

- Progress tracking:
  Use `update_plan` for visible progress. Translate phase todos into plan steps
  with `pending`, `in_progress`, and `completed`.

- User questions:
  Ask the user directly in plain text by default.
  In Plan mode, `request_user_input` may be used if a structured picker is
  explicitly helpful, but forge-codex must not depend on it.

- File reading and search:
  Prefer `exec_command` with:
  - `rg` for text search
  - `rg --files` or `find` for file discovery
  - `sed -n`, `cat`, or similar for file reads

- File edits:
  Prefer `apply_patch` for manual edits.
  Use `exec_command` only for non-patch operations such as formatting, tests,
  git inspection, or running helper scripts.

- Multi-step shell work:
  Use `exec_command` and, if needed, `write_stdin` for interactive follow-up.

- Parallel work:
  Use `spawn_agent` only when delegation is explicitly allowed and the task is
  well-scoped. Coordinate with `send_input`, `wait_agent`, and `close_agent`.

  **Agent lifecycle is mandatory.** Every `spawn_agent` must be paired with a
  `close_agent` once the agent has reported its result or is no longer needed.
  Codex enforces a hard cap on concurrent agents — leaked sessions accumulate
  across waves and eventually block all further dispatch.

  **Progress reporting is mandatory.** Dispatched agents must not stay silent
  until completion. Follow `templates/subagent-progress.md`: agents write
  heartbeats to `.forge/state/subagent-progress/<id>.json` (or the session
  sidecar path); the parent Reads those files and relays short status to the
  user while work is in flight. On Codex, `send_input` may request a pulse if
  a progress file goes stale — still require the file update.

  Required pattern for every dispatched agent:
  1. `spawn_agent` to launch (prompt includes the subagent-progress snippet).
  2. While running: Read progress files / optional `send_input` status pulses;
     do not leave the parent chat silent until the final report.
  3. `wait_agent` (or `send_input` + `wait_agent`) until the agent reports.
  4. Capture the agent's output into orchestrator state or a memory file.
  5. `close_agent` immediately after — do **not** defer to "end of skill."
  6. If an agent is no longer useful (blocker, redundant, abandoned wave),
     close it the moment that becomes true; do not keep it open "just in case."

  Before advancing to the next wave, step, or phase, every agent spawned in the
  current scope must already be closed. If you cannot close an agent (it is
  still running and you need its output), `wait_agent` first. Never leave an
  agent open across a step boundary.

## Prompt Writing Rules

- When a template says "read", interpret that as "inspect with Codex tools",
  usually via `exec_command`.
- When a template says "write", interpret that as "edit or create files with
  Codex tools", usually via `apply_patch`.
- When a template says "search", interpret that as `rg` unless a different tool
  is clearly better.
- When a template says "ask the user", keep it to one concise question unless
  multiple questions are truly necessary.

## Agent Guidance

- Do not assume assistant-specific tools or slash commands exist.
- Prefer concrete Codex tool names in instructions when ambiguity would hurt.
- If a workflow boundary requires user approval, pause and ask directly instead
  of inventing a structured UI dependency.

## Session opt-in

- Step **1** prompt output may include **SESSION OPT-IN — Forge structured workflows**. Complete the user’s choice **before** mirroring the **Create Phase Todos** JSON below that block.
- In CI or headless automation, set **`FORGE_SKIP_SESSION_OPTIN=1`** to omit that banner.

## Announcing the active step (optional)

- At the start of executing a forge skill step, you may emit **one line**: which **`$forge:…`** skill and **`--step N`** you are following (Superpowers-style “announce the skill”). Keeps transcripts auditable without extra tools.
