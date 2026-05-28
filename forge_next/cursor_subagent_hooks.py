"""Install Cursor sub-agent lifecycle hooks into a project's .cursor/hooks.json."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

HOOK_MARKER = "cursor-subagent-hook"
MANAGED_NOTE = "forge-subagent-lifecycle-hooks (managed by forge-next; re-run forge cursor-subagent-hooks)"


def hook_command(event: str, *, forge_exe: Path | None = None) -> str:
    import json

    from forge_next.claude_graphify import resolve_forge_executable

    forge = forge_exe or resolve_forge_executable()
    return f"{json.dumps(str(forge))} cursor-subagent-hook {event}"


def hooks_fragment(*, forge_exe: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    from forge_next.claude_graphify import resolve_forge_executable

    forge = forge_exe or resolve_forge_executable()
    cmd = lambda event: hook_command(event, forge_exe=forge)
    return {
        "preToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": cmd("preToolUse"),
                        "timeout": 5,
                    }
                ],
            }
        ],
        "subagentStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": cmd("subagentStart"),
                        "timeout": 5,
                    }
                ],
            }
        ],
        "subagentStop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": cmd("subagentStop"),
                        "timeout": 5,
                    }
                ],
            }
        ],
        "postToolUse": [
            {
                "matcher": "Task",
                "hooks": [
                    {
                        "type": "command",
                        "command": cmd("postToolUse"),
                        "timeout": 5,
                    }
                ],
            }
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


def merge_cursor_subagent_hooks(
    hooks_doc: dict[str, Any],
    *,
    forge_exe: Path | None = None,
) -> dict[str, Any]:
    hooks_root = hooks_doc.setdefault("hooks", {})
    if not isinstance(hooks_root, dict):
        hooks_root = {}
        hooks_doc["hooks"] = hooks_root
    fragment = hooks_fragment(forge_exe=forge_exe)
    for event, entries in fragment.items():
        current = hooks_root.get(event)
        if not isinstance(current, list):
            current = []
        hooks_root[event] = _merge_event_list(current, entries)
    hooks_doc["version"] = hooks_doc.get("version") or 1
    hooks_doc["_forge_subagent_lifecycle"] = MANAGED_NOTE
    return hooks_doc


def apply_cursor_subagent_hooks(
    repo_root: Path,
    *,
    dry_run: bool = False,
) -> int:
    from forge_next.claude_graphify import resolve_forge_executable

    repo_root = repo_root.resolve()
    hooks_path = repo_root / ".cursor" / "hooks.json"
    hooks_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        resolve_forge_executable()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if hooks_path.is_file():
        try:
            doc = json.loads(hooks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Could not parse {hooks_path}: {exc}", file=sys.stderr)
            return 1
        if not isinstance(doc, dict):
            doc = {"version": 1, "hooks": {}}
    else:
        doc = {"version": 1, "hooks": {}}

    merged = merge_cursor_subagent_hooks(doc)
    out = json.dumps(merged, indent=2, ensure_ascii=True) + "\n"
    if dry_run:
        print(f"Would write {hooks_path} (dry-run; no changes).")
        print(out)
        return 0

    hooks_path.write_text(out, encoding="utf-8", newline="\n")
    print(f"Wrote {hooks_path}")
    print("Restart Cursor or reload hooks after changing hooks.json.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cursor-subagent-hooks",
        description="Install Cursor hooks that remind agents to close unused sub-agents before each tool call.",
    )
    p.add_argument("--repo", type=str, default=None, help="Repo root (default: cwd)")
    p.add_argument("--dry-run", action="store_true", help="Print merged hooks.json without writing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo).expanduser().resolve() if args.repo else Path.cwd().resolve()
    return apply_cursor_subagent_hooks(root, dry_run=bool(args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
