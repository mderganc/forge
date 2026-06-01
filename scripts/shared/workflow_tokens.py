"""CLI / agent invocation tokens for Forge workflow commands."""

from __future__ import annotations

from pathlib import Path


def skill_token_from_script(script_path: Path) -> str:
    """Parent dir under scripts/ as a hyphenated CLI token (code_review → code-review)."""
    return script_path.parent.name.replace("_", "-")


def chain_command_to_agent_invocation(chain_cmd: str) -> str:
    """Map SKILL_CHAIN entries like 'evaluate --mode pre' to '$forge:evaluate --mode pre'."""
    chain_cmd = chain_cmd.strip()
    if not chain_cmd:
        return chain_cmd
    skill, sep, tail = chain_cmd.partition(" ")
    skill_h = skill.replace("_", "-")
    inv = f"$forge:{skill_h}"
    return f"{inv}{sep}{tail}" if sep else inv
