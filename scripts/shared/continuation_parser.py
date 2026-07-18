"""Parse forge continuation command lines (``$forge:skill --phase …``)."""

from __future__ import annotations

import shlex


def _parse_skill_token(token: str) -> str | None:
    if token.startswith("/forge:") or token.startswith("$forge:"):
        return token.split(":", 1)[1]
    return None


def _consume_flag(
    parts: list[str],
    index: int,
    flag: str,
) -> tuple[str | None, int]:
    if parts[index] == flag and index + 1 < len(parts):
        return parts[index + 1], index + 2
    return None, index + 1


def parse_continuation_command(cmd: str) -> tuple[int | None, str | None]:
    """Extract step (from ``--step`` or ``--phase``) and state path from a continuation line."""
    if not cmd.strip():
        return None, None
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return None, None

    from scripts.shared.skill_phases import step_for_phase

    next_step: int | None = None
    state_path: str | None = None
    phase_raw: str | None = None
    skill_token: str | None = None
    i = 0
    while i < len(parts):
        token = parts[i]
        skill = _parse_skill_token(token)
        if skill:
            skill_token = skill
            i += 1
            continue
        if token == "--step":
            value, i = _consume_flag(parts, i, "--step")
            if value is not None:
                try:
                    next_step = int(value)
                except ValueError:
                    pass
            continue
        if token == "--phase":
            phase_raw, i = _consume_flag(parts, i, "--phase")
            continue
        if token == "--state":
            state_path, i = _consume_flag(parts, i, "--state")
            continue
        if token == "--session":
            sid, i = _consume_flag(parts, i, "--session")
            if sid:
                try:
                    from scripts.shared.session_store import session_json_path

                    state_path = str(session_json_path(sid))
                except Exception:
                    state_path = sid
            continue
        i += 1

    if next_step is None and phase_raw and skill_token:
        try:
            next_step = step_for_phase(skill_token, phase_raw)
        except SystemExit:
            pass
    return next_step, state_path
