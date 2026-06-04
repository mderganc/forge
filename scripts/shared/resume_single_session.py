"""Render output for a single active Forge resume session."""

from __future__ import annotations

from pathlib import Path


def render_complete_session(session: dict, ctx_lines: list[str]) -> str:
    skill = session["skill"]
    current = session.get("current_step", 1)
    max_step = session.get("max_step", 6)
    lines = [
        "FORGE-CODEX RESUME",
        "=" * 60,
        "",
        f"**Session `{skill}` is complete** ({current}/{max_step}).",
        f"**State file:** `{session['path']}`",
        "",
    ]
    lines.extend(ctx_lines)
    lines.extend([
        "The final step has been executed. No resume command is needed.",
        "",
        "You may:",
        "  - Delete the state file to start fresh next time",
        "  - Run `resume` again to advance to the next pipeline skill",
        "  - Run `status` to see the overall workflow state",
    ])
    return "\n".join(lines)


def render_retry_exhausted_session(
    session: dict,
    ctx_lines: list[str],
    *,
    failure_count: int,
    cleanup_hint: str,
) -> str:
    skill = session["skill"]
    current = session.get("current_step", 1)
    max_step = session.get("max_step", 6)
    lines = [
        "FORGE-CODEX RESUME",
        "=" * 60,
        "",
        f"**Active session:** `{skill}` ({current}/{max_step})",
        f"**State file:** `{session['path']}`",
        "",
    ]
    lines.extend(ctx_lines)
    lines.extend([
        f"**Step {current} has failed {failure_count} times.**",
        "",
        "Inspect logs for the underlying error before retrying. If the failure",
        "is not recoverable, clear state with:",
        "",
        f"    {cleanup_hint}",
        "",
        "Then start the workflow over from step 1.",
    ])
    return "\n".join(lines)


def _diagnose_sidecar_lines(session: dict) -> list[str]:
    skill = session["skill"]
    current = session.get("current_step", 1)
    if skill != "diagnose" or current < 3:
        return []
    state_dir = Path(session["path"]).parent
    sidecars = [
        (".diagnose-feedback-loop.json", "Phase 2 — feedback loop"),
        (".diagnose-hypotheses.json", "Phase 3 — hypothesis register"),
        (".diagnose-mece-tree.json", "Phase 3 — MECE tree"),
        (".diagnose-first-principles.json", "Phase 1–2 — first-principles"),
        (".diagnose-five-whys.json", "Phase 3–4 — five-whys chains"),
        (".diagnose-technique-coverage.json", "coverage matrix (20 techniques)"),
    ]
    missing = [f"`{name}` ({hint})" for name, hint in sidecars if not (state_dir / name).exists()]
    if not missing:
        return []
    out = ["", "**Diagnose note:** Missing sidecar(s) beside state:", ""]
    out.extend(f"- {m}" for m in missing)
    out.append(
        "Backfill via the listed phases before deepen (step 3), analysis (step 4), or solutions (step 5). "
        "If blocked at step 3, set `repro_loop_override_reason` on diagnose state only after user input."
    )
    return out


def render_active_session(
    session: dict,
    ctx_lines: list[str],
    *,
    status: str,
    cmd: str,
    snap,
    mem_summary: str,
    resume_context,
    conflict: bool,
) -> str:
    from scripts.shared.resume import _resume_command

    skill = session["skill"]
    current = session.get("current_step", 1)
    max_step = session.get("max_step", 6)
    lines = [
        "FORGE-CODEX RESUME",
        "=" * 60,
        "",
        f"**Active session:** `{skill}` ({current}/{max_step})",
        f"**Status:** {status}",
        f"**State file:** `{session['path']}`",
        "",
    ]
    lines.extend(ctx_lines)
    lines.extend(_diagnose_sidecar_lines(session))

    conf = resume_context.continuation_confidence(session, snap, mem_summary)
    sugg = resume_context.suggested_continuation_lines(
        session=session,
        snap=snap,
        memory_summary=mem_summary,
        successor_skill=None,
    )
    lines.append(f"**Suggested continuation (confidence: {conf})**")
    lines.append("")
    lines.extend(f"- {s}" for s in sugg)
    lines.append("")

    if conflict:
        snap_cmd = ""
        if snap and snap.get("skill") and snap.get("state_path"):
            fake_sess = {
                "skill": snap.get("skill"),
                "path": snap.get("state_path"),
                "current_step": snap.get("current_step"),
                "last_completed_step": snap.get("last_completed_step"),
                "max_step": snap.get("max_step", 6),
                "started_at": snap.get("started_at"),
            }
            snap_cmd = _resume_command(fake_sess)
        lines.extend([
            "## Source conflict (JSON state vs continuity snapshot)",
            "",
            "The active workflow state and `resume-context.json` disagree on skill, step, or state path.",
            "**Ask the user which source to trust** before running any resume command.",
            "",
            "**Option A — State-based resume (recommended default):**",
            "",
            f"    {cmd}",
            "",
            "**Option B — Snapshot-based continuation (if memory reflects reality):**",
            "",
        ])
        if snap_cmd:
            lines.append(f"    {snap_cmd}")
        else:
            lines.append("    (snapshot incomplete — reconcile or delete `resume-context.json`.)")
        lines.append("")
        return "\n".join(lines)

    lines.extend([
        "━" * 60,
        "CONTINUATION — IMMEDIATE ACTION REQUIRED",
        "━" * 60,
        "Execute this command to resume:",
        "",
        f"    {cmd}",
        "",
        "DO NOT STOP. Execute the command now to continue the workflow.",
    ])
    return "\n".join(lines)
