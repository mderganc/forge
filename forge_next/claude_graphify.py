"""Merge Graphify Claude Code hooks into ~/.claude/settings.json."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Substrings matched when replacing prior Forge hook installs.
HOOK_MARKERS = (
    "claude-graphify-hook",
    "forge_next.hooks.claude_graphify_hook",
)
HOOK_MARKER = HOOK_MARKERS[0]
MANAGED_NOTE = "forge-graphify-hooks (managed by forge-next; re-run forge claude-graphify)"


def default_claude_settings_path() -> Path:
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".claude" / "settings.json"


def resolve_forge_executable() -> Path:
    """Locate the ``forge`` CLI executable that ships forge-next (prefer pipx)."""
    candidates: list[Path] = []

    which_forge = shutil.which("forge")
    if which_forge:
        candidates.append(Path(which_forge))

    home = Path.home()
    candidates.extend(
        [
            home / ".local" / "bin" / "forge",
            home / ".local" / "pipx" / "venvs" / "forge-next" / "bin" / "forge",
        ]
    )

    bindir = Path(sys.executable).resolve().parent
    candidates.append(bindir / "forge")
    if os.name == "nt":
        candidates.append(bindir / "forge.exe")
        candidates.append(bindir / "forge.cmd")

    seen: set[Path] = set()
    for raw in candidates:
        try:
            p = raw.resolve()
        except OSError:
            continue
        if p in seen:
            continue
        seen.add(p)
        if p.is_file():
            return p

    raise FileNotFoundError(
        "Could not locate the `forge` executable. Install with `pipx install forge-next`, "
        "ensure `~/.local/bin` is on PATH, then run `pipx run forge-next claude-graphify`."
    )


def hook_command(event: str, *, forge_exe: Path | None = None) -> str:
    """Shell command for Claude settings.json.

    Invokes ``<absolute-forge> claude-graphify-hook <event>`` so Claude never needs
    ``python -m forge_next`` on a system interpreter that lacks the package.
    """
    forge = forge_exe or resolve_forge_executable()
    return f"{json.dumps(str(forge))} claude-graphify-hook {event}"


def hook_launcher_description(*, forge_exe: Path | None = None) -> str:
    forge = forge_exe or resolve_forge_executable()
    return f"forge CLI hook ({forge})"


def _verify_hook_launcher(forge: Path) -> str | None:
    """Run a dry hook invocation; return warning text or None."""
    try:
        proc = subprocess.run(
            [str(forge), "claude-graphify-hook", "SessionStart"],
            input="{}",
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except OSError as exc:
        return f"Could not execute {forge}: {exc}"
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        return f"Hook smoke test failed (exit {proc.returncode}): {err[:300]}"
    return None


def _managed_hook_block(event: str, *, forge_exe: Path) -> dict[str, Any]:
    return {
        "hooks": [
            {
                "type": "command",
                "command": hook_command(event, forge_exe=forge_exe),
            }
        ]
    }


def graphify_hooks_fragment(*, forge_exe: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Hooks to merge under settings['hooks']."""
    forge = forge_exe or resolve_forge_executable()
    return {
        "SessionStart": [_managed_hook_block("SessionStart", forge_exe=forge)],
        "UserPromptSubmit": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": hook_command("UserPromptSubmit", forge_exe=forge),
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
                        "command": hook_command("PreToolUse", forge_exe=forge),
                    }
                ],
            },
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": hook_command("PreToolUse", forge_exe=forge),
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
        if isinstance(h, dict) and any(m in str(h.get("command", "")) for m in HOOK_MARKERS):
            return True
    return False


def _merge_event_list(existing: list[Any], incoming: list[dict[str, Any]]) -> list[Any]:
    out: list[Any] = [e for e in existing if not _entry_is_managed(e)]
    out.extend(incoming)
    return out


def merge_graphify_hooks(
    settings: dict[str, Any],
    *,
    forge_exe: Path | None = None,
) -> dict[str, Any]:
    """Return settings dict with Graphify hooks merged (replaces prior managed hooks)."""
    hooks_root = settings.setdefault("hooks", {})
    if not isinstance(hooks_root, dict):
        hooks_root = {}
        settings["hooks"] = hooks_root

    fragment = graphify_hooks_fragment(forge_exe=forge_exe)
    for event, entries in fragment.items():
        current = hooks_root.get(event)
        if not isinstance(current, list):
            current = []
        hooks_root[event] = _merge_event_list(current, entries)

    settings["_forge_graphify"] = MANAGED_NOTE
    return settings


def audit_claude_graphify_hooks(settings_path: Path | None = None) -> list[str]:
    """Return warnings about Claude Graphify hook commands in settings.json."""
    sp = (settings_path or default_claude_settings_path()).expanduser()
    if not sp.is_file():
        return ["Claude settings.json not found; run `forge claude-graphify`."]
    try:
        data = json.loads(sp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"Could not parse {sp} as JSON."]
    if not isinstance(data, dict):
        return [f"Expected object in {sp}."]

    warnings: list[str] = []
    hooks_root = data.get("hooks")
    if not isinstance(hooks_root, dict):
        return ["No Claude hooks configured; run `forge claude-graphify`."]

    found_managed = False
    for event, entries in hooks_root.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not _entry_is_managed(entry):
                continue
            found_managed = True
            for h in entry.get("hooks") or []:
                if not isinstance(h, dict):
                    continue
                cmd = str(h.get("command", ""))
                if " -m forge_next.hooks.claude_graphify_hook" in cmd:
                    warnings.append(
                        f"Hook {event!r} uses `python -m forge_next...` ({cmd[:80]}...). "
                        "Re-run `forge claude-graphify` after `pipx upgrade forge-next`."
                    )
                elif "claude-graphify-hook" not in cmd:
                    warnings.append(f"Hook {event!r} does not invoke `claude-graphify-hook`: {cmd[:120]}")
    if not found_managed:
        warnings.append("No Forge Graphify hooks in settings.json; run `forge claude-graphify`.")
    return warnings


def apply_claude_graphify_settings(
    settings_path: Path,
    *,
    dry_run: bool = False,
) -> int:
    settings_path = settings_path.expanduser().resolve()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        forge_exe = resolve_forge_executable()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

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

    merged = merge_graphify_hooks(settings, forge_exe=forge_exe)
    out = json.dumps(merged, indent=2, ensure_ascii=True) + "\n"

    if dry_run:
        print(f"Would update {settings_path} with Graphify hooks (dry-run).")
        print(f"Hook launcher: {hook_launcher_description(forge_exe=forge_exe)}")
        return 0

    settings_path.write_text(out, encoding="utf-8", newline="\n")
    print(f"Updated {settings_path} with Graphify hooks ({MANAGED_NOTE}).")
    print(f"Hook launcher: {hook_launcher_description(forge_exe=forge_exe)}")

    smoke = _verify_hook_launcher(forge_exe)
    if smoke:
        print(f"WARNING: {smoke}", file=sys.stderr)
        return 1

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
