"""CLI / agent invocation tokens for Forge workflow commands."""

from __future__ import annotations

import os
from pathlib import Path


def skill_token_from_script(script_path: Path) -> str:
    """Parent dir under scripts/ as a hyphenated CLI token (code_review → code-review)."""
    return script_path.parent.name.replace("_", "-")


def _workflow_invocation_style() -> str:
    """``slash`` → ``/forge:…``; ``dollar`` → ``$forge:…`` (Codex)."""
    raw = os.environ.get("FORGE_WORKFLOW_INVOCATION", "").strip().lower()
    if raw in ("slash", "/", "cursor", "claude"):
        return "slash"
    if raw in ("dollar", "$", "codex"):
        return "dollar"

    for key in ("CURSOR_AGENT", "CURSOR_TRACE_ID", "CURSOR_SESSION_ID"):
        if os.environ.get(key, "").strip():
            return "slash"
    if os.environ.get("CLAUDE_CODE", "").strip():
        return "slash"
    if os.environ.get("CODEX_HOME", "").strip():
        return "dollar"

    try:
        from scripts.shared.orchestrator import _detect_repo_root

        root = _detect_repo_root()
        if (root / ".cursor").is_dir():
            return "slash"
    except Exception:
        pass

    return "dollar"


def workflow_invocation_prefix() -> str:
    """Agent-facing prefix: ``/forge:`` (Cursor/Claude) or ``$forge:`` (Codex)."""
    return "/forge:" if _workflow_invocation_style() == "slash" else "$forge:"


def chain_command_to_agent_invocation(chain_cmd: str) -> str:
    """Map SKILL_CHAIN entries like ``evaluate --mode pre`` to agent invocation tokens."""
    chain_cmd = chain_cmd.strip()
    if not chain_cmd:
        return chain_cmd
    skill, sep, tail = chain_cmd.partition(" ")
    skill_h = skill.replace("_", "-")
    inv = f"{workflow_invocation_prefix()}{skill_h}"
    return f"{inv}{sep}{tail}" if sep else inv
