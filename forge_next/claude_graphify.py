"""Merge Graphify Claude Code hooks into ~/.claude/settings.json."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

HOOK_MARKER = "forge_next.hooks.claude_graphify_hook"
MANAGED_NOTE = "forge-graphify-hooks (managed by forge-next; re-run forge claude-graphify)"


def default_claude_settings_path() -> Path:
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".claude" / "settings.json"


def _hook_command(event: str) -> str:
    return f'python -m forge_next.hooks.claude_graphify_hook {event}'


def _managed_hook_block(event: str) -> dict[str, Any]:
    return {
        "hooks": [
            {
                "type": "command",
                "command": _hook_command(event),
            }
        ]
    }


def graphify_hooks_fragment() -> dict[str, list[dict[str, Any]]]:
    """Hooks to merge under settings['hooks']."""
    return {
        "SessionStart": [_managed_hook_block("SessionStart")],
        "UserPromptSubmit": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command("UserPromptSubmit"),
                    }
                ],
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Grep|Glob|Read",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command("PreToolUse"),
                    }
                ],
            },
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": _hook_command("PreToolUse"),
                    }
                ],
            },
        ],
    }


def _entry_is_managed(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        return False
    for h in hooks:
        if isinstance(h, dict) and HOOK_MARKER in str(h.get("command", "")):
            return True
    return False


def _merge_event_list(existing: list[Any], incoming: list[dict[str, Any]]) -> list[Any]:
    out: list[Any] = [e for e in existing if not _entry_is_managed(e)]
    out.extend(incoming)
    return out


def merge_graphify_hooks(settings: dict[str, Any]) -> dict[str, Any]:
    """Return settings dict with Graphify hooks merged (replaces prior managed hooks)."""
    hooks_root = settings.setdefault("hooks", {})
    if not isinstance(hooks_root, dict):
        hooks_root = {}
        settings["hooks"] = hooks_root

    fragment = graphify_hooks_fragment()
    for event, entries in fragment.items():
        current = hooks_root.get(event)
        if not isinstance(current, list):
            current = []
        hooks_root[event] = _merge_event_list(current, entries)

    settings["_forge_graphify"] = MANAGED_NOTE
    return settings


def apply_claude_graphify_settings(
    settings_path: Path,
    *,
    dry_run: bool = False,
) -> int:
    settings_path = settings_path.expanduser().resolve()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Could not parse {settings_path}: {exc}", file=sys.stderr)
            return 1
        if not isinstance(settings, dict):
            print(f"Expected JSON object in {settings_path}", file=sys.stderr)
            return 1
    else:
        settings = {}

    merged = merge_graphify_hooks(settings)
    out = json.dumps(merged, indent=2, ensure_ascii=True) + "\n"

    if dry_run:
        print(f"Would update {settings_path} with Graphify hooks (dry-run).")
        return 0

    settings_path.write_text(out, encoding="utf-8", newline="\n")
    print(f"Updated {settings_path} with Graphify hooks ({MANAGED_NOTE}).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="claude-graphify",
        description=(
            "Install cross-platform Graphify hooks into Claude Code settings.json "
            "(SessionStart, UserPromptSubmit for forge:*, PreToolUse for Grep/Glob/Read/Bash)."
        ),
    )
    p.add_argument(
        "--settings",
        type=str,
        default=None,
        help="Path to settings.json (default: ~/.claude/settings.json)",
    )
    p.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    return p


def main(argv: list[str] | None = None) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    args = build_parser().parse_args(argv)
    path = Path(args.settings).expanduser() if args.settings else default_claude_settings_path()
    rc = apply_claude_graphify_settings(path, dry_run=bool(args.dry_run))
    raise SystemExit(rc)
