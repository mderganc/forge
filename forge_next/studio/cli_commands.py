"""CLI entrypoints for `forge studio` (internal / agent use)."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

from forge_next.studio import events as studio_events
from forge_next.studio import server as studio_server
from forge_next.studio.session import (
    create_session,
    load_session,
    resolve_session_dir,
    studio_sessions_root,
    update_session_url,
)


def _default_foreground() -> bool:
    if os.environ.get("CODEX_CI"):
        return True
    if sys.platform == "win32":
        return True
    if os.environ.get("MSYSTEM"):
        return True
    return False


def _resolve_foreground(args: argparse.Namespace) -> bool:
    """Foreground blocks until Ctrl+C; agents should use --json (background) or --background."""
    if getattr(args, "background", False):
        return False
    if getattr(args, "foreground", False):
        return True
    if getattr(args, "json", False):
        return False
    return _default_foreground()


def _tail_log(log_file: Path, *, max_lines: int = 40) -> str:
    if not log_file.is_file():
        return ""
    try:
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-max_lines:])


def _wait_server_ready(host: str, port: int, *, timeout_sec: float = 8.0) -> bool:
    import urllib.error
    import urllib.request

    bind_host = "127.0.0.1" if host in ("127.0.0.1", "::1", "localhost") else host
    url = f"http://{bind_host}:{port}/api/version"
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.75) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.15)
    return False


def _pick_port(host: str) -> int:
    del host  # loopback ephemeral bind uses 127.0.0.1
    from forge_next.studio.server import pick_ephemeral_port

    return pick_ephemeral_port()


def _spawn_background_server(
    *,
    host: str,
    port: int,
    session_dir: Path,
    log_file: Path,
) -> int:
    import subprocess

    env = os.environ.copy()
    env["FORGE_STUDIO_SESSION_DIR"] = str(session_dir.resolve())
    env["FORGE_STUDIO_HOST"] = host
    env["FORGE_STUDIO_PORT"] = str(port)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = open(log_file, "a", encoding="utf-8")
    kwargs: dict = {
        "env": env,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
    }
    if sys.platform == "win32":
        detached = getattr(subprocess, "DETACHED_PROCESS", 0)
        kwargs["creationflags"] = (  # type: ignore[attr-defined]
            subprocess.CREATE_NEW_PROCESS_GROUP | detached
        )
    else:
        kwargs["close_fds"] = True
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(
        [sys.executable, "-m", "forge_next.studio._serve"],
        **kwargs,
    )
    log_handle.close()
    return proc.pid


def cmd_start(args: argparse.Namespace, repo_root: Path) -> int:
    host = getattr(args, "host", None) or "127.0.0.1"
    port = int(args.port) if getattr(args, "port", None) else _pick_port(host)
    workflow = getattr(args, "workflow", None) or "develop"
    foreground = _resolve_foreground(args)

    session = create_session(repo_root, workflow=workflow, port=port)
    session_dir = studio_sessions_root(repo_root) / session["session_id"]
    from forge_next.studio import log as studio_log_mod

    log_path = studio_log_mod.ensure_studio_log_header(
        repo_root, session_id=session["session_id"], workflow=workflow
    )
    session["studio_log"] = str(log_path.resolve())
    content_dir = Path(session["screen_dir"])
    state_dir = Path(session["state_dir"])

    url_host = "localhost" if host in ("127.0.0.1", "::1") else host
    url = f"http://{url_host}:{port}/"

    pid_file = state_dir / "server.pid"
    log_file = state_dir / "server.log"

    payload = {
        "type": "server-started",
        "session_id": session["session_id"],
        "port": port,
        "url": url,
        "screen_dir": str(content_dir),
        "state_dir": str(state_dir),
        "studio_log": session.get("studio_log", ""),
        "foreground": foreground,
    }

    if foreground:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
        update_session_url(session_dir, url=url, port=port)
        if args.json:
            print(json.dumps(payload, ensure_ascii=True))
        else:
            print(json.dumps(payload, indent=2))
        try:
            studio_server.run_server(
                host=host,
                port=port,
                content_dir=content_dir,
                state_dir=state_dir,
            )
        except KeyboardInterrupt:
            return 0
        return 0

    pid = _spawn_background_server(host=host, port=port, session_dir=session_dir, log_file=log_file)
    pid_file.write_text(str(pid), encoding="utf-8")
    update_session_url(session_dir, url=url, port=port)
    if not _wait_server_ready(host, port):
        try:
            if platform.system() == "Windows":
                os.kill(pid, 9)  # noqa: S606
            else:
                os.kill(pid, 15)
        except OSError:
            pass
        pid_file.unlink(missing_ok=True)
        err = {
            "type": "server-failed",
            "session_id": session["session_id"],
            "port": port,
            "error": "Studio server did not respond on /api/version",
            "log_tail": _tail_log(log_file),
            "hint": "Check server.log; ensure forge-next is installed for this Python "
            f"({sys.executable}).",
        }
        print(json.dumps(err, ensure_ascii=True), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print(json.dumps(payload, indent=2))
    return 0


def cmd_stop(args: argparse.Namespace, repo_root: Path) -> int:
    session_dir = resolve_session_dir(repo_root, getattr(args, "session", None))
    if session_dir is None:
        print('{"error": "no active session"}', file=sys.stderr)
        return 1
    state_dir = session_dir / "state"
    pid_file = state_dir / "server.pid"
    if pid_file.is_file():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            if platform.system() == "Windows":
                os.kill(pid, 9)  # noqa: S606 — terminate studio child on Windows
            else:
                os.kill(pid, 15)
        except (OSError, ValueError):
            pass
        pid_file.unlink(missing_ok=True)
    active = studio_sessions_root(repo_root) / "active-session.json"
    if active.is_file():
        active.unlink()
    from forge_next.studio import log as studio_log_mod

    try:
        log_path = studio_log_mod.studio_log_path(repo_root)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\nSession `{session_dir.name}` ended.\n\n")
    except OSError:
        pass
    out = {
        "type": "server-stopped",
        "session_id": session_dir.name,
        "studio_log": str(studio_log_mod.studio_log_path(repo_root)),
    }
    print(json.dumps(out, ensure_ascii=True) if args.json else json.dumps(out, indent=2))
    return 0


def cmd_status(args: argparse.Namespace, repo_root: Path) -> int:
    session_dir = resolve_session_dir(repo_root, getattr(args, "session", None))
    if session_dir is None:
        print('{"active": false}', file=sys.stderr if not args.json else sys.stdout)
        return 1
    data = load_session(session_dir) or {}
    data["active"] = True
    data["session_dir"] = str(session_dir)
    port = data.get("port")
    host = "127.0.0.1"
    if isinstance(port, int):
        data["server_ready"] = _wait_server_ready(host, port, timeout_sec=1.0)
    else:
        data["server_ready"] = False
    print(json.dumps(data, ensure_ascii=True) if args.json else json.dumps(data, indent=2))
    return 0


def cmd_events(args: argparse.Namespace, repo_root: Path) -> int:
    session_dir = resolve_session_dir(repo_root, getattr(args, "session", None))
    if session_dir is None:
        print("[]" if args.json else "No active session", file=sys.stderr)
        return 1
    state_dir = session_dir / "state"
    events, _ = studio_events.read_events_since_cursor(
        state_dir, clear_cursor=bool(getattr(args, "clear", False))
    )
    if args.json:
        print(json.dumps(events, ensure_ascii=True))
    else:
        for ev in events:
            print(json.dumps(ev, ensure_ascii=True))
    return 0


def cmd_unlock(args: argparse.Namespace, repo_root: Path) -> int:
    from forge_next.studio import approved as studio_approved

    gate = getattr(args, "gate", None)
    if not gate:
        print('{"error": "pass --gate <id>"}', file=sys.stderr)
        return 1
    try:
        meta = studio_approved.unlock_gate(repo_root, str(gate))
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    out = {"type": "screen-unlocked", **meta}
    print(json.dumps(out, ensure_ascii=True) if args.json else json.dumps(out, indent=2))
    return 0


def cmd_approve(args: argparse.Namespace, repo_root: Path) -> int:
    session_dir = resolve_session_dir(repo_root, getattr(args, "session", None))
    if session_dir is None:
        print('{"error": "no active session"}', file=sys.stderr)
        return 1
    from forge_next.studio import approved as studio_approved

    try:
        meta = studio_approved.lock_current_screen(
            repo_root,
            session_dir,
            gate=getattr(args, "gate", None),
            replace=bool(getattr(args, "replace", False)),
        )
    except FileExistsError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    out = {"type": "screen-approved", **meta}
    print(json.dumps(out, ensure_ascii=True) if args.json else json.dumps(out, indent=2))
    return 0


def cmd_push(args: argparse.Namespace, repo_root: Path) -> int:
    session_dir = resolve_session_dir(repo_root, getattr(args, "session", None))
    if session_dir is None:
        print('{"error": "no active session"}', file=sys.stderr)
        return 1
    src = Path(args.file).expanduser().resolve()
    if not src.is_file():
        print(f'{{"error": "file not found: {src}"}}', file=sys.stderr)
        return 1
    from forge_next.studio import approved as studio_approved

    blocked = studio_approved.check_push_allowed(repo_root, src)
    if blocked:
        print(json.dumps({"error": blocked}, ensure_ascii=True), file=sys.stderr)
        return 1
    content_dir = session_dir / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    name = getattr(args, "name", None) or src.name
    if not name.endswith(".html"):
        name = f"{name}.html"
    dest = content_dir / name
    is_new = not dest.exists()
    shutil.copyfile(src, dest)
    state_dir = session_dir / "state"
    studio_server.register_screen_file(content_dir, state_dir, name)
    studio_server.bump_screen_version(reset_events=is_new, state_dir=state_dir)
    out = {
        "type": "screen-pushed",
        "file": str(dest),
        "version": studio_server.get_screen_version(state_dir),
    }
    print(json.dumps(out, ensure_ascii=True) if args.json else json.dumps(out, indent=2))
    return 0


def _configure_studio_subcommands(st_sub: argparse._SubParsersAction) -> None:
    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--repo", type=str, default=None, help="Target repo root")
        sp.add_argument("--session", type=str, default=None, help="Session id (default: active)")
        sp.add_argument("--json", action="store_true", dest="json", help="JSON stdout")

    start = st_sub.add_parser("start", help=argparse.SUPPRESS)
    start.add_argument("--workflow", choices=("develop", "plan"), default="develop")
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--port", type=int, default=None)
    start.add_argument("--foreground", action="store_true", default=None)
    start.add_argument("--background", action="store_true", help="Force background server thread")
    add_common(start)

    for name in ("stop", "status", "events", "push", "approve", "unlock"):
        sp = st_sub.add_parser(name, help=argparse.SUPPRESS)
        add_common(sp)
    approve_p = st_sub.choices["approve"]
    approve_p.add_argument("--gate", default=None, help="Gate id (default: infer from HTML)")
    approve_p.add_argument("--replace", action="store_true", help="Replace an existing locked gate")
    unlock_p = st_sub.choices["unlock"]
    unlock_p.add_argument("--gate", required=True, help="Gate id to unlock")
    events_p = st_sub.choices["events"]
    events_p.add_argument("--clear", action="store_true", help="Advance cursor after read")
    push_p = st_sub.choices["push"]
    push_p.add_argument("--file", required=True)
    push_p.add_argument("--name", default=None)


def build_standalone_studio_parser() -> argparse.ArgumentParser:
    """Parser for `forge studio …` (not registered on main `forge --help`)."""
    studio = argparse.ArgumentParser(
        prog="forge studio",
        description="Internal: localhost UI for develop/plan gates (agents only).",
    )
    st_sub = studio.add_subparsers(dest="studio_cmd", required=True)
    _configure_studio_subcommands(st_sub)
    return studio


def parse_studio_argv(argv: list[str]) -> argparse.Namespace:
    """Parse argv after the ``studio`` token (e.g. ``['start', '--repo', '.']``)."""
    return build_standalone_studio_parser().parse_args(argv)


def register_studio_parser(sub: argparse._SubParsersAction) -> None:  # noqa: ARG001 — optional argparse wiring
    """Legacy hook — studio is dispatched from ``forge_next.cli.main`` before ``--help``."""
    _ = sub


def _repo_root_from_args(repo_arg: str | None) -> Path:
    from forge_next.cli import resolve_repo_root

    start = Path(repo_arg).expanduser() if repo_arg else Path.cwd()
    root = resolve_repo_root(start)
    if root is None:
        raise SystemExit("Not in a repo; pass --repo <path>.")
    return root


def run_studio_command(args: argparse.Namespace) -> int:
    repo_arg = getattr(args, "repo", None)
    repo_root = _repo_root_from_args(repo_arg)
    sub = getattr(args, "studio_cmd", None)
    if sub == "start":
        return cmd_start(args, repo_root)
    if sub == "stop":
        return cmd_stop(args, repo_root)
    if sub == "status":
        return cmd_status(args, repo_root)
    if sub == "events":
        return cmd_events(args, repo_root)
    if sub == "push":
        return cmd_push(args, repo_root)
    if sub == "approve":
        return cmd_approve(args, repo_root)
    if sub == "unlock":
        return cmd_unlock(args, repo_root)
    raise SystemExit(f"Unknown studio subcommand: {sub!r}")
