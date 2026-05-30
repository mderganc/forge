"""Central Graphify enforcement toggles (env, repo prefs, implement wave defer).

Use this module everywhere Forge would inject Graphify reminders or spawn refresh:
orchestrator banners, background refresh, Claude PreToolUse hooks.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

_TRUTHY = frozenset({"1", "true", "yes", "on"})

PREFS_FILENAME = "graphify-prefs.json"

# Graphify orchestrator banners + foreground refresh run only on ship (end of workflow).
GRAPHIFY_ORCHESTRATOR_SKILL = "ship"

# Legacy pref: defer_implement_waves (no longer affects banners; kept for prefs migration).
IMPLEMENT_WAVE_STEPS = frozenset({3, 4, 5})


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def _runtime_state_dir(repo_root: Path) -> Path:
    import sys

    root = repo_root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.shared.orchestrator import runtime_state_dir

    return runtime_state_dir(root)


def graphify_prefs_path(repo_root: Path) -> Path:
    return _runtime_state_dir(repo_root) / PREFS_FILENAME


def read_graphify_prefs(repo_root: Path) -> dict[str, Any]:
    path = graphify_prefs_path(repo_root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_graphify_prefs(repo_root: Path, prefs: dict[str, Any]) -> Path:
    path = graphify_prefs_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.close(fd)
        Path(tmp).write_text(json.dumps(prefs, indent=2) + "\n", encoding="utf-8")
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return path


def graphify_fully_disabled(repo_root: Path | None = None) -> bool:
    """True when Graphify banners, hooks, and automatic refresh should not run."""
    if _env_truthy("FORGE_SKIP_GRAPHIFY"):
        return True
    if repo_root is None:
        return False
    prefs = read_graphify_prefs(repo_root)
    return bool(prefs.get("disabled"))


def graphify_refresh_disabled(repo_root: Path | None = None) -> bool:
    """True when automatic background ``forge graphify refresh`` must not spawn."""
    if _env_truthy("FORGE_SKIP_GRAPHIFY_REFRESH"):
        return True
    return graphify_fully_disabled(repo_root)


def graphify_defer_implement_waves(repo_root: Path) -> bool:
    prefs = read_graphify_prefs(repo_root)
    return bool(prefs.get("defer_implement_waves"))


def should_show_graphify_banner(
    skill_name: str,
    step: int,
    repo_root: Path,
) -> bool:
    """Whether the per-step GRAPHIFY orchestrator block should print (ship only)."""
    if graphify_fully_disabled(repo_root):
        return False
    slug = skill_name.strip().lower()
    return slug == GRAPHIFY_ORCHESTRATOR_SKILL


def graphify_deferred_note(skill_name: str, step: int, repo_root: Path) -> str:
    """Unused — workflow skills no longer print per-step GRAPHIFY blocks."""
    return ""


def set_graphify_disabled(repo_root: Path, *, disabled: bool) -> Path:
    prefs = read_graphify_prefs(repo_root)
    prefs["disabled"] = bool(disabled)
    if not disabled:
        prefs.pop("disabled", None)
    if not prefs:
        path = graphify_prefs_path(repo_root)
        path.unlink(missing_ok=True)
        return path
    return write_graphify_prefs(repo_root, prefs)


def set_graphify_defer_implement_waves(repo_root: Path, *, defer: bool) -> Path:
    prefs = read_graphify_prefs(repo_root)
    if defer:
        prefs["defer_implement_waves"] = True
    else:
        prefs.pop("defer_implement_waves", None)
    if not prefs:
        path = graphify_prefs_path(repo_root)
        path.unlink(missing_ok=True)
        return path
    return write_graphify_prefs(repo_root, prefs)


def graphify_prefs_summary(repo_root: Path) -> str:
    if graphify_fully_disabled(repo_root):
        if _env_truthy("FORGE_SKIP_GRAPHIFY"):
            return "disabled (FORGE_SKIP_GRAPHIFY is set)"
        return "disabled (repo prefs)"
    parts: list[str] = [f"orchestrator banners on `{GRAPHIFY_ORCHESTRATOR_SKILL}` only"]
    if graphify_defer_implement_waves(repo_root):
        parts.append("legacy defer_implement_waves pref set (no effect on banners)")
    if _env_truthy("FORGE_SKIP_GRAPHIFY_REFRESH"):
        parts.append("auto-refresh suppressed (FORGE_SKIP_GRAPHIFY_REFRESH)")
    return ", ".join(parts)
