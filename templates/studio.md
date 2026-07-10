# Forge Studio (agent / runtime only)

> **Not a user workflow.** End users never run `forge studio`. They use `forge:design` or `forge:plan` and may open a **local URL** during visual gates. Agents start/stop Studio and push HTML screens.

## When to use

Per question: **would the user understand this better by seeing it than reading it?**

| Browser (Studio) | Chat / AskQuestion |
|------------------|-------------------|
| Layout mockups, wireframes, side-by-side UI | Requirements, scope, tradeoff lists |
| Architecture diagrams as HTML | Conceptual A/B/C in prose |
| Gate 1 HMW “worldviews”, Gate 2 Q1 candidate cards | Gate 2 Q2 priority dimension, tiebreak |

## Screen layout (every gate)

1. **Design context** (agent-written) — `section.studio-design-notes` with goal, constraints, recommendation, tradeoffs.
2. **Interactive gate** — options, mockups, diagrams (`data-gate` / `data-choice`).
3. **Probing questions** (agent-written, recommended) — `section.studio-probes` with numbered `.studio-probe` blocks so the user answers *specific* topics (not one vague textarea).
4. **Extra feedback** (auto-appended) — freeform textarea only for anything not covered above.

Reference example: `forge_next/assets/studio/screen-example.html`.

### Probing questions (preferred for intent)

Ask **multiple concrete questions** per gate — each with sub-bullets the user can react to (color, layout, control type, labels, missing options). The user answers in plain language tied to that question.

**Agent rules:** Write 2–4 probes per visual gate. Each probe needs `data-probe-id` (stable slug) and `data-probe-prompt` (full question text). Include `.studio-probe-hints` bullets when helpful.

**Events:** `probe-response` (one question) or `probes-submit` (batch). Map `probe_id` + `prompt` + `text` into `project.md` under the gate — do not collapse into a single blob without structure.

## Opt-in (PM)

Separate message only:

> Some steps might be easier if I show mockups and design notes in your browser (local URL). You can pick options and leave feedback on the page. Opt in? (Token-heavy; you can still answer in chat.)

Record in `state.custom`: `studio_enabled`, `studio_declined`, or neither until answered.

## One session per repo

Only one active Studio session per repository (`active-session.json` under `.forge/studio/`). Stop at develop/plan handoff.

## Agent commands (internal)

From repo root (agents only — **do not** tell users to run these):

1. `forge studio start --repo . --workflow develop --json` (`--repo` on every studio subcommand; **`--json` runs in the background** so the server survives after the agent returns; use `--foreground` only for interactive debugging)
2. Tell the user: open the URL, review design notes, pick options, add feedback on the page, click **Done reviewing**, then continue in chat.
3. Write HTML to `screen_dir` or `forge studio push --file gate1.html` (start from `screen-example.html`)
4. `forge studio events --json` — read raw events (optional; log is canonical)
5. Read **`studio-log.md`** in runtime memory (`.forge/memory/studio-log.md`) — auto-appended on every browser action; also injected as `{{STUDIO_LOG}}` in develop/plan steps
6. Summarize gate outcomes into `project.md` / plan when the gate closes
7. `forge studio stop` at handoff

### Recording events (required)

| Event `type` | PM action |
|--------------|-----------|
| `click` | Single-select gate answer |
| `submit` | Multi-select gate answer (`choices[]`) |
| `probe-response` | One numbered probe: record `probe_id`, `prompt`, `text` under gate |
| `probes-submit` | Batch: `responses[]` with `probe_id`, `prompt`, `text` per item |
| `feedback` | Freeform overflow (bottom box) — only if not already captured in probes |
| `done` | User finished reviewing (not locked yet) |
| `approve` | User locked the screen — copy to `studio/approved/`; read `{{STUDIO_APPROVED}}` in later skills |
| `unlock` | User removed the lock — gate editable again; update plan references if needed |

Ignore empty `submit` with `choices: []`.

### Session log and locked references

| Path | Purpose |
|------|---------|
| `.forge/memory/studio-log.md` | Append-only feedback log (`{{STUDIO_LOG}}`) |
| `.forge/memory/studio-approved-index.md` | Index of **locked** approved screens (`{{STUDIO_APPROVED}}`) |
| `.forge/studio/approved/<gate>.html` | **Immutable** HTML the user approved — use for plan/implement |
| `.forge/studio/approved/manifest.json` | Machine-readable lock registry |
| `.forge/studio/<session-id>/content/*.html` | **Draft** screens (editable until approved) |

Bundled HTML examples for agents to copy: `forge_next/assets/studio/` (`screen-example.html`, `frame.html`, `studio.js`, `feedback-panel.html`).

### Approval (lock)

1. User clicks **Approve screen** on the gate (or agent runs `forge studio approve --repo .` after explicit chat confirmation).
2. Newest session HTML is copied to `.forge/studio/approved/<gate>.html` and registered in `manifest.json`.
3. `studio-approved-index.md` is regenerated; develop/plan/implement inject it as `{{STUDIO_APPROVED}}`.
4. **`forge studio push` is rejected** for HTML whose `data-studio-gate` is already locked (use a new gate id for drafts).
5. Re-lock same gate: `forge studio approve --replace` or browser approve after `--replace` policy in chat.
6. **Unlock:** user clicks **Unlock screen** or `forge studio unlock --repo . --gate <id>` — removes lock, allows push/edit again; drops entry from `{{STUDIO_APPROVED}}`.

## Design notes block (agent)

```html
<div data-studio-gate="gate1_hmw">
<section class="studio-design-notes" data-gate="gate1_hmw">
  <h2>Design context</h2>
  <p class="subtitle">Why we're asking this now.</p>
  <dl class="studio-notes-grid">
    <dt>Goal</dt><dd>...</dd>
    <dt>Constraints</dt><dd>...</dd>
    <dt>Recommendation</dt><dd><strong>...</strong> because ...</dd>
  </dl>
  <details class="studio-notes-detail">
    <summary>Tradeoffs and open questions</summary>
    <ul><li>...</li></ul>
  </details>
</section>
<!-- options / mockups here -->
</div>
```

Set `data-studio-gate` on the wrapper so feedback events use the correct gate id.

To skip auto-feedback (rare): `data-studio-skip-feedback` on the wrapper.

### Probe block markup

```html
<section class="studio-probes" data-gate="gate1_hmw">
  <h2>Refine this screen</h2>
  <p class="subtitle">Answer each question so we know exactly what you mean.</p>

  <article class="studio-probe" data-probe-id="visual_controls"
    data-probe-prompt="Is the color scheme fine? Different structure? Radio buttons or something else?">
    <header class="studio-probe-header">
      <span class="studio-probe-num">1</span>
      <p class="studio-probe-prompt">Is the color scheme fine? …</p>
    </header>
    <ul class="studio-probe-hints">
      <li>Color scheme</li>
      <li>Layout structure</li>
      <li>Control type</li>
    </ul>
    <label class="studio-probe-label" for="studio-probe-visual_controls">Your answer</label>
    <textarea id="studio-probe-visual_controls" class="studio-probe-answer" rows="3"
      placeholder="e.g. Yes, color is fine; use radio buttons; smaller button"></textarea>
    <button type="button" class="studio-probe-send">Send answer</button>
    <p class="studio-probe-status" role="status" aria-live="polite"></p>
  </article>

  <div class="studio-probes-actions studio-actions">
    <button type="button" class="studio-probes-submit-all">Send all answers</button>
  </div>
</section>
```

Copy from `screen-example.html` — do not hand-roll broken HTML.

## Option markup

Use `data-gate` and `data-choice` on `.option` elements; `onclick="studioToggle(this)"`. Multi-select: `data-multiselect` + `data-studio-submit` button.

## Runtime notes

| Runtime | Start recipe |
|---------|----------------|
| Codex | `--foreground` + background shell when `CODEX_CI` |
| Windows | Prefer `--foreground` |
| Cursor / Claude | `--background` when shell survives |

If bind fails: use AskQuestion gates; log `studio_bind_failed` in `project.md`.
