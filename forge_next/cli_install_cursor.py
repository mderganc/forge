"""Install Cursor plugin pack from a extracted forge repo tree."""

from __future__ import annotations

import shutil
from pathlib import Path

from forge_next.cli_install_io import copytree_replace, default_cursor_local_plugins_dir

_CURSOR_SKILL_TEMPLATE_FILES = (
    "plan-modes.md",
    "writing-plans.md",
    "structural-quality-probes.md",
    "diagnose-execution-playbooks.md",
)


def _install_cursor_plugin_skills(repo_root: Path, plugin_root: Path) -> list[str]:
    """Bundle Codex SKILL.md packs under the Cursor plugin for agent discovery."""
    warnings: list[str] = []
    src = repo_root / "integrations" / "codex" / "skills"
    if not src.is_dir():
        warnings.append("Codex skills folder not found; Cursor plugin has commands only.")
        return warnings

    skills_dst = plugin_root / "skills"
    if skills_dst.exists():
        shutil.rmtree(skills_dst)
    shutil.copytree(src, skills_dst)

    templates_src = repo_root / "templates"
    templates_dst = skills_dst / "templates"
    if templates_src.is_dir():
        templates_dst.mkdir(parents=True, exist_ok=True)
        for name in _CURSOR_SKILL_TEMPLATE_FILES:
            src_file = templates_src / name
            if src_file.is_file():
                shutil.copy2(src_file, templates_dst / name)

    return warnings


def install_cursor_plugin(
    repo_root: Path,
    *,
    cursor_dir: str | None,
) -> tuple[str | None, list[str]]:
    """Copy integrations/cursor-plugin and bundle agent skills; return (path, warnings)."""
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
    warnings.extend(_install_cursor_plugin_skills(repo_root, dst))
    return str(dst), warnings
