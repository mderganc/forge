"""Shared workflow gate utilities for sidecar load/validate/override patterns."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def gate_sidecar_path(
    state_path: Path,
    filename: str,
    *,
    legacy_filename: str | None = None,
) -> Path:
    """Resolve gate sidecar beside the workflow state file."""
    primary = state_path.parent / filename
    if primary.is_file():
        return primary
    if legacy_filename:
        legacy = state_path.parent / legacy_filename
        if legacy.is_file():
            return legacy
    return primary


def load_gate_json(path: Path) -> dict[str, Any] | None:
    """Load JSON gate sidecar; return None when missing or invalid."""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def validate_override_bypass(
    allow_incomplete: bool,
    override_reason: str,
    override_follow_up: str,
    *,
    reason_field_label: str = "override reason",
    follow_up_field_label: str = "override follow-up",
    success_message: str | None = None,
    override_timestamp: str = "",
) -> tuple[bool, str]:
    """Validate override flags for gate bypass; return (ok, message)."""
    if not allow_incomplete:
        return True, ""

    reason = (override_reason or "").strip()
    if not reason:
        return False, f"Gate bypass requires non-empty {reason_field_label}."

    follow = (override_follow_up or "").strip()
    if not follow:
        return False, f"Gate bypass requires non-empty {follow_up_field_label}."

    if success_message is not None:
        return True, success_message

    ts = override_timestamp or "(timestamp not set)"
    return True, f"Gate overridden — reason recorded (timestamp={ts})."


def exit_if_gate_fails(
    ok: bool,
    msg: str,
    *,
    error_prefix: str = "ERROR: ",
    error_label: str = "",
    echo_msg_on_success: bool = False,
) -> None:
    """Exit with stderr message when gate validation fails."""
    if ok:
        if echo_msg_on_success and msg:
            print(msg, file=sys.stderr)
        return

    if error_label:
        print(f"{error_prefix}{error_label}{msg}", file=sys.stderr)
    else:
        print(f"{error_prefix}{msg}" if error_prefix and not msg.startswith(error_prefix) else msg, file=sys.stderr)
    sys.exit(1)
