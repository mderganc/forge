"""Install Cursor plugin pack from a extracted forge repo tree."""

from __future__ import annotations

from pathlib import Path

from forge_next.cli_install_io import copytree_replace, default_cursor_local_plugins_dir


def install_cursor_plugin(
    repo_root: Path,
    *,
    cursor_dir: str | None,
) -> tuple[str | None, list[str]]:
    """Copy integrations/cursor-plugin; return (install path key value, warnings)."""
    warnings: list[str] = []
    src = repo_root / "integrations" / "cursor-plugin"
    if not src.is_dir():
        warnings.append("Cursor plugin folder not found in downloaded repo.")
        return None, warnings
    base = (
        Path(cursor_dir).expanduser()
        if cursor_dir
        else default_cursor_local_plugins_dir()
    )
    dst = base / "forge"
    copytree_replace(src, dst)
    return str(dst), warnings
