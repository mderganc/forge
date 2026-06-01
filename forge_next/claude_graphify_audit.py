"""Claude Graphify hook audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _audit_hook_command(event: str, hook: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    cmd = str(hook.get("command", ""))
    if " -m forge_next.hooks.claude_graphify_hook" in cmd:
        warnings.append(
            f"Hook {event!r} uses `python -m forge_next...` ({cmd[:80]}...). "
            "Re-run `forge claude-graphify` after `pipx upgrade forge-next`."
        )
    elif "claude-graphify-hook" not in cmd:
        warnings.append(
            f"Hook {event!r} does not invoke `claude-graphify-hook`: {cmd[:120]}"
        )
    return warnings


def audit_managed_entries(hooks_root: dict[str, Any]) -> tuple[bool, list[str]]:
    """Scan hooks for Forge-managed Graphify entries; return (found_any, warnings)."""
    from forge_next.claude_graphify import _entry_is_managed

    warnings: list[str] = []
    found_managed = False
    for event, entries in hooks_root.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not _entry_is_managed(entry):
                continue
            found_managed = True
            for h in entry.get("hooks") or []:
                if isinstance(h, dict):
                    warnings.extend(_audit_hook_command(str(event), h))
    return found_managed, warnings


def load_claude_settings(settings_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not settings_path.is_file():
        return None, ["Claude settings.json not found; run `forge claude-graphify`."]
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, [f"Could not parse {settings_path} as JSON."]
    if not isinstance(data, dict):
        return None, [f"Expected object in {settings_path}."]
    return data, []
