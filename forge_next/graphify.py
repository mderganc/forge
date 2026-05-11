"""Graphify integration: refresh index metadata and optional git post-commit hook.

Graphify is optional third-party tooling. Forge never requires it for core
workflows; `forge resume` reads `graphify-status.json` when present.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HOOK_BEGIN = "# >>> forge-graphify-hook (managed by forge-next)"
HOOK_END = "# <<< forge-graphify-hook"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _git_head(repo: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return (r.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _write_status(repo: Path, payload: dict) -> None:
    """Write graphify-status.json under Forge runtime state directory."""
    # Import inside function so `forge graphify` works with minimal path setup.
    import sys

    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from scripts.shared.orchestrator import ensure_runtime_dirs, runtime_state_dir

    ensure_runtime_dirs(repo)
    out = runtime_state_dir(repo) / "graphify-status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, suffix=".tmp")
    try:
        os.close(fd)
        Path(tmp).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        Path(tmp).replace(out)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def refresh(repo_root: Path) -> int:
    """Attempt to run Graphify (or FORGE_GRAPHIFY_COMMAND), then write status.

    Returns 0 always (fail-soft for CI/hooks); failures are recorded in JSON.
    """
    head = _git_head(repo_root)
    custom = (os.environ.get("FORGE_GRAPHIFY_COMMAND") or "").strip()
    cmd: list[str] | None = None
    if custom:
        try:
            cmd = shlex.split(custom)
        except ValueError as e:
            _write_status(
                repo_root,
                {
                    "status": "error",
                    "last_refresh": _utc_iso(),
                    "error": f"Invalid FORGE_GRAPHIFY_COMMAND: {e}",
                    "repo_head": head,
                    "graphify_available": False,
                },
            )
            return 0
    elif shutil.which("graphify"):
        cmd = ["graphify"]

    if not cmd:
        _write_status(
            repo_root,
            {
                "status": "missing",
                "last_refresh": _utc_iso(),
                "error": "Graphify not found on PATH. Install Graphify or set FORGE_GRAPHIFY_COMMAND.",
                "repo_head": head,
                "graphify_available": False,
            },
        )
        return 0

    try:
        r = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=600,
        )
        ok = r.returncode == 0
        err_tail = ((r.stderr or "") + (r.stdout or ""))[-800:]
        _write_status(
            repo_root,
            {
                "status": "fresh" if ok else "error",
                "last_refresh": _utc_iso(),
                "error": None if ok else (err_tail or f"exit {r.returncode}"),
                "repo_head": head,
                "graphify_available": True,
            },
        )
    except subprocess.TimeoutExpired:
        _write_status(
            repo_root,
            {
                "status": "error",
                "last_refresh": _utc_iso(),
                "error": "Graphify command timed out",
                "repo_head": head,
                "graphify_available": True,
            },
        )
    except OSError as e:
        _write_status(
            repo_root,
            {
                "status": "error",
                "last_refresh": _utc_iso(),
                "error": str(e),
                "repo_head": head,
                "graphify_available": bool(cmd),
            },
        )
    return 0


def _hook_body() -> str:
    return "\n".join(
        [
            HOOK_BEGIN,
            "# Rebuild Graphify metadata after each commit (fail-soft).",
            'REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"',
            'if command -v forge >/dev/null 2>&1 && [ -n "$REPO_ROOT" ]; then',
            '  (cd "$REPO_ROOT" && forge graphify refresh) || true',
            "fi",
            HOOK_END,
            "",
        ]
    )


def install_post_commit_hook(repo_root: Path) -> tuple[bool, str]:
    """Insert or replace the Forge Graphify block in .git/hooks/post-commit."""
    hook_path = repo_root / ".git" / "hooks" / "post-commit"
    block = _hook_body()
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    existing = hook_path.read_text(encoding="utf-8", errors="replace") if hook_path.exists() else ""
    if HOOK_BEGIN in existing and HOOK_END in existing:
        pre, _, rest = existing.partition(HOOK_BEGIN)
        _, _, post = rest.partition(HOOK_END)
        new_content = pre + block + post.lstrip("\n")
    else:
        sep = "\n" if existing and not existing.endswith("\n") else ""
        new_content = existing + sep + block
    hook_path.write_text(new_content, encoding="utf-8")
    try:
        hook_path.chmod(hook_path.stat().st_mode | 0o111)
    except OSError:
        pass
    return True, f"Updated {hook_path} with Forge Graphify post-commit block."


def uninstall_post_commit_hook(repo_root: Path) -> tuple[bool, str]:
    """Remove the Forge Graphify block from .git/hooks/post-commit."""
    hook_path = repo_root / ".git" / "hooks" / "post-commit"
    if not hook_path.is_file():
        return True, "No post-commit hook present; nothing to remove."
    text = hook_path.read_text(encoding="utf-8", errors="replace")
    if HOOK_BEGIN not in text or HOOK_END not in text:
        return True, "Forge Graphify block not found in post-commit hook."
    pre, _, rest = text.partition(HOOK_BEGIN)
    _, _, post = rest.partition(HOOK_END)
    new_content = pre + post
    hook_path.write_text(new_content.lstrip("\n"), encoding="utf-8")
    return True, f"Removed Forge Graphify block from {hook_path}."


def graphify_install_notice_lines() -> list[str]:
    """Human-readable onboarding for `forge install` output."""
    return [
        "",
        "Graphify (optional — gives `forge resume` a codebase map, not your chat history):",
        "  1) Install Graphify so a `graphify` command works on your PATH, **or** set environment variable",
        "     FORGE_GRAPHIFY_COMMAND to exactly how you run it (e.g. `graphify build` — use your project’s real command).",
        "  2) In each **git clone** of your app repo, run **forge graphify refresh** once from that repo",
        "     (or `forge graphify refresh --repo \"C:/path/to/repo\"` from any directory).",
        "     That writes **graphify-status.json** under your Forge runtime state folder (e.g. `.codex/forge/state/`).",
        "  3) Optional: **forge graphify install-hook** in the same repo adds a **post-commit** snippet so every",
        "     commit re-runs refresh in the background (`|| true` so commits never fail).",
        "     Remove later with **forge graphify uninstall-hook**.",
        "  4) Open **docs/graphify.md** in the Forge package/repo for the full picture.",
        "",
    ]
