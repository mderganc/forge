"""Install Claude command pack and optional Graphify hooks."""

from __future__ import annotations

from pathlib import Path

from forge_next.cli_install_io import copytree_replace, default_claude_commands_dir


def install_claude_commands(
    repo_root: Path,
    *,
    claude_dir: str | None,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    src = repo_root / "integrations" / "claude" / "commands"
    if not src.is_dir():
        warnings.append("Claude commands folder not found in downloaded repo.")
        return None, warnings
    base = (
        Path(claude_dir).expanduser()
        if claude_dir
        else default_claude_commands_dir()
    )
    dst = base / "forge"
    copytree_replace(src, dst)
    return str(dst), warnings


def apply_claude_graphify_hooks() -> tuple[str | None, list[str]]:
    from forge_next.claude_graphify import (
        apply_claude_graphify_settings,
        default_claude_settings_path,
    )

    warnings: list[str] = []
    rc = apply_claude_graphify_settings(default_claude_settings_path())
    if rc == 0:
        return str(default_claude_settings_path()), warnings
    warnings.append(
        "Claude Graphify hooks were not written; run `forge claude-graphify` "
        "after fixing settings.json."
    )
    return None, warnings
