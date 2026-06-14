"""Studio status block helper for develop/plan orchestrators."""

from __future__ import annotations

from typing import Literal

from scripts.shared.orchestrator import SkillState

StudioContext = Literal["develop", "plan"]


def studio_status_block(state: SkillState, *, context: StudioContext = "develop") -> str:
    """Render STUDIO_STATUS template variable from workflow state."""
    if state.custom.get("studio_declined"):
        if context == "plan":
            return "Studio: declined — approval in chat only."
        return "Studio: declined — use chat/AskQuestion gates only."

    if state.custom.get("studio_enabled"):
        sid = state.custom.get("studio_session_id", "")
        if context == "plan":
            extra = f" Session: `{sid}`." if sid else ""
            return f"Studio: enabled for visual approval screens.{extra} See `templates/studio.md`."
        extra = (
            f" Session: `{sid}`."
            if sid
            else " Start session per `templates/studio.md` when entering visual gates."
        )
        return (
            f"Studio: enabled (agent-internal transport).{extra} "
            "User sees URL only — do not ask them to run `forge studio`."
        )

    if context == "plan":
        return "Studio: optional for step 5 approval — see `templates/studio.md`."
    return (
        "Studio: not enabled — offer opt-in at scope (step 2) per `templates/studio.md`, "
        "or use text gates."
    )
