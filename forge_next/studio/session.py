"""Session paths and metadata for Forge Studio."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
ACTIVE_SESSION_FILE = "active-session.json"


def _repo_runtime_root(repo_root: Path) -> Path:
    from scripts.shared.orchestrator import runtime_root

    return runtime_root(repo_root)


def studio_sessions_root(repo_root: Path) -> Path:
    return _repo_runtime_root(repo_root) / "studio"


def active_session_path(repo_root: Path) -> Path:
    return studio_sessions_root(repo_root) / ACTIVE_SESSION_FILE


def _new_session_id() -> str:
    return f"{os.getpid()}-{int(time.time())}"


def create_session(
    repo_root: Path,
    *,
    workflow: str = "develop",
    port: int | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    """Create session dirs and register as the sole active session for this repo."""
    root = studio_sessions_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    session_id = _new_session_id()
    session_dir = root / session_id
    content_dir = session_dir / "content"
    state_dir = session_dir / "state"
    content_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    session: dict[str, Any] = {
        "v": SCHEMA_VERSION,
        "session_id": session_id,
        "repo_root": str(repo_root.resolve()),
        "url": url or "",
        "port": port,
        "screen_dir": str(content_dir.resolve()),
        "state_dir": str(state_dir.resolve()),
        "workflow": workflow,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    session_path = session_dir / "session.json"
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")

    active = {"session_id": session_id, "session_dir": str(session_dir.resolve())}
    active_session_path(repo_root).write_text(
        json.dumps(active, indent=2) + "\n", encoding="utf-8"
    )
    return session


def infer_repo_root_from_session_dir(session_dir: Path) -> Path | None:
    """Walk parents from `.codex/forge/studio/<id>` to find the git/README repo root."""
    cur = session_dir.resolve()
    for _ in range(8):
        if (cur / ".git").is_dir() or (cur / "README.md").is_file():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return None


def load_session(session_dir: Path) -> dict[str, Any] | None:
    path = session_dir / "session.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    if not data.get("repo_root"):
        inferred = infer_repo_root_from_session_dir(session_dir)
        if inferred is not None:
            data["repo_root"] = str(inferred.resolve())
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def resolve_session_dir(repo_root: Path, session_id: str | None) -> Path | None:
    if session_id:
        candidate = studio_sessions_root(repo_root) / session_id
        return candidate if candidate.is_dir() else None
    active = active_session_path(repo_root)
    if not active.is_file():
        return None
    try:
        data = json.loads(active.read_text(encoding="utf-8"))
        sid = data.get("session_id")
        if sid:
            return studio_sessions_root(repo_root) / str(sid)
        sdir = data.get("session_dir")
        if sdir:
            p = Path(sdir)
            return p if p.is_dir() else None
    except (json.JSONDecodeError, OSError):
        return None
    return None


def update_session_url(session_dir: Path, *, url: str, port: int) -> None:
    data = load_session(session_dir)
    if not data:
        return
    data["url"] = url
    data["port"] = port
    (session_dir / "session.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
