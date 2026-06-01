"""Threading HTTP server for Forge Studio."""

from __future__ import annotations

import json
import mimetypes
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from forge_next.studio import assets as studio_assets
from forge_next.studio import events as studio_events

_VERSION_FILE = "screen.version"


def _version_path(state_dir: Path) -> Path:
    return state_dir / _VERSION_FILE


def bump_screen_version(*, reset_events: bool = False, state_dir: Path | None = None) -> int:
    if state_dir is None:
        return 0
    state_dir.mkdir(parents=True, exist_ok=True)
    path = _version_path(state_dir)
    cur = 0
    if path.is_file():
        try:
            cur = int(path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            cur = 0
    cur += 1
    path.write_text(str(cur), encoding="utf-8")
    if reset_events:
        studio_events.clear_events(state_dir)
    return cur


def get_screen_version(state_dir: Path) -> int:
    path = _version_path(state_dir)
    if not path.is_file():
        return 0
    try:
        return int(path.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return 0


def is_full_document(html: str) -> bool:
    return html.lstrip().lower().startswith("<!doctype") or html.lstrip().lower().startswith("<html")


def get_newest_screen(content_dir: Path) -> Path | None:
    if not content_dir.is_dir():
        return None
    candidates: list[tuple[float, Path]] = []
    for path in content_dir.glob("*.html"):
        try:
            candidates.append((path.stat().st_mtime, path))
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def append_page_chrome(body: str) -> str:
    """Append feedback UI unless the fragment opts out or already includes it."""
    if "data-studio-skip-feedback" in body or 'class="studio-feedback"' in body:
        return body
    try:
        panel = studio_assets.asset_text("feedback-panel.html").strip()
    except Exception:
        return body
    return body.rstrip() + "\n\n" + panel + "\n"


def wrap_fragment(body: str, *, title: str = "Forge Studio") -> str:
    frame = studio_assets.asset_text("frame.html")
    injection = f'<script>\n{studio_assets.asset_text("studio.js")}\n</script>'
    if "</head>" in frame.lower():
        idx = frame.lower().find("</head>")
        frame = frame[:idx] + injection + "\n" + frame[idx:]
    else:
        frame = injection + frame
    inner = append_page_chrome(body)
    if "{{CONTENT}}" in frame:
        return frame.replace("{{CONTENT}}", inner).replace("{{TITLE}}", title)
    return frame + inner


def _studio_token_from_env() -> str:
    return os.environ.get("FORGE_STUDIO_TOKEN", "").strip()


def _request_studio_token(headers) -> str:
    got = (headers.get("X-Forge-Studio-Token") or "").strip()
    if got:
        return got
    auth = headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def _studio_token_ok(headers) -> bool:
    expected = _studio_token_from_env()
    if not expected:
        return True
    return _request_studio_token(headers) == expected


WAITING_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Forge Studio</title></head>
<body><main style="font-family:system-ui,sans-serif;padding:2rem;max-width:40rem;margin:auto">
<h1>Forge Studio</h1>
<p>Waiting for the agent to push a screen…</p>
</main></body></html>"""


def build_handler(
    content_dir: Path,
    state_dir: Path,
    on_activity: Callable[[], None] | None = None,
) -> type[BaseHTTPRequestHandler]:
    content_dir = content_dir.resolve()
    state_dir = state_dir.resolve()

    class StudioHandler(BaseHTTPRequestHandler):
        server_version = "ForgeStudio/1.0"

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _touch(self) -> None:
            if on_activity:
                on_activity()

        def _send_json(self, code: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _repo_root(self) -> Path | None:
            from forge_next.studio.session import load_session

            meta = load_session(state_dir.parent) or {}
            raw = meta.get("repo_root")
            if not raw:
                return None
            return Path(str(raw))

        def do_GET(self) -> None:  # noqa: N802
            self._touch()
            path = self.path.split("?", 1)[0]
            if path == "/api/version":
                self._send_json(200, {"version": get_screen_version(state_dir)})
                return
            if path == "/api/locks":
                repo = self._repo_root()
                if repo is None:
                    self._send_json(200, {"gates": []})
                    return
                from forge_next.studio import approved as studio_approved

                self._send_json(200, {"gates": studio_approved.locked_gates(repo)})
                return
            if path == "/studio.js":
                data = studio_assets.asset_bytes("studio.js")
                token = _studio_token_from_env()
                if token:
                    prefix = f"window.__FORGE_STUDIO_TOKEN__ = {json.dumps(token)};\n".encode(
                        "utf-8"
                    )
                    data = prefix + data
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/" or path == "/index.html":
                screen = get_newest_screen(content_dir)
                if screen is None:
                    html = WAITING_HTML
                else:
                    raw = screen.read_text(encoding="utf-8")
                    html = raw if is_full_document(raw) else wrap_fragment(raw, title=screen.stem)
                    if "studio.js" not in html and "</head>" in html.lower():
                        idx = html.lower().find("</head>")
                        inj = f'<script src="/studio.js"></script>'
                        html = html[:idx] + inj + html[idx:]
                    elif "studio.js" not in html:
                        html += '<script src="/studio.js"></script>'
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if path.startswith("/files/"):
                name = Path(path[7:]).name
                fp = content_dir / name
                if not fp.is_file():
                    self.send_error(404)
                    return
                data = fp.read_bytes()
                ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            self._touch()
            if self.path.split("?", 1)[0] != "/api/event":
                self.send_error(404)
                return
            if not _studio_token_ok(self.headers):
                self._send_json(401, {"error": "studio token required (FORGE_STUDIO_TOKEN)"})
                return
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(400, {"error": "invalid json"})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"error": "expected object"})
                return
            event_type = str(payload.get("type", "click"))
            gate = payload.get("gate")
            choice = payload.get("choice")
            choices = payload.get("choices")
            text = payload.get("text")
            probe_id = payload.get("probe_id")
            prompt = payload.get("prompt")
            responses = payload.get("responses")
            label = payload.get("label") or ""
            if not label and text:
                label = str(text)[:200]
            row: dict = {"type": event_type}
            if gate is not None:
                row["gate"] = str(gate)
            if choice is not None:
                row["choice"] = str(choice)
            if isinstance(choices, list):
                row["choices"] = [str(c) for c in choices]
            if probe_id is not None:
                row["probe_id"] = str(probe_id)
            if prompt is not None:
                row["prompt"] = str(prompt)[:2000]
            if isinstance(responses, list):
                cleaned_responses = []
                for item in responses:
                    if not isinstance(item, dict):
                        continue
                    entry: dict[str, str] = {}
                    if item.get("probe_id") is not None:
                        entry["probe_id"] = str(item["probe_id"])
                    if item.get("prompt") is not None:
                        entry["prompt"] = str(item["prompt"])[:2000]
                    if item.get("text") is not None:
                        entry["text"] = str(item["text"]).strip()[:8000]
                    if entry.get("text"):
                        cleaned_responses.append(entry)
                if cleaned_responses:
                    row["responses"] = cleaned_responses
            if text is not None:
                cleaned = str(text).strip()
                if cleaned:
                    row["text"] = cleaned[:8000]
            if label:
                row["label"] = str(label)
            session_dir = state_dir.parent
            from forge_next.studio.session import load_session
            from forge_next.studio import log as studio_log_mod

            meta = load_session(session_dir) or {}
            repo_raw = meta.get("repo_root")
            if event_type == "approve" and repo_raw:
                from forge_next.studio import approved as studio_approved

                try:
                    lock_meta = studio_approved.lock_current_screen(
                        Path(str(repo_raw)),
                        session_dir,
                        gate=str(gate) if gate is not None else None,
                    )
                except FileExistsError as exc:
                    self._send_json(409, {"error": str(exc)})
                    return
                except (FileNotFoundError, ValueError) as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                row["gate"] = lock_meta["gate"]
                row["html_path"] = lock_meta["html_path"]
                row["label"] = f"Approved and locked: {lock_meta['gate']}"

            if event_type == "unlock" and repo_raw:
                from forge_next.studio import approved as studio_approved

                if gate is None:
                    self._send_json(400, {"error": "gate required for unlock"})
                    return
                try:
                    unlock_meta = studio_approved.unlock_gate(Path(str(repo_raw)), str(gate))
                except FileNotFoundError as exc:
                    self._send_json(404, {"error": str(exc)})
                    return
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                    return
                row["gate"] = unlock_meta["gate"]
                row["label"] = f"Unlocked: {unlock_meta['gate']}"

            saved = studio_events.append_event(state_dir, row)
            if repo_raw:
                try:
                    studio_log_mod.append_studio_log(Path(str(repo_raw)), saved)
                except OSError:
                    pass
            self._send_json(200, {"ok": True, "event": saved})

    return StudioHandler


def register_screen_file(content_dir: Path, state_dir: Path, filename: str) -> None:
    """Bump version file so the browser reloads (content_dir reserved for future use)."""
    _ = content_dir
    bump_screen_version(state_dir=state_dir)


def run_server(
    *,
    host: str,
    port: int,
    content_dir: Path,
    state_dir: Path,
    idle_timeout_sec: int = 30 * 60,
) -> None:
    last_activity = [time.time()]

    def touch() -> None:
        last_activity[0] = time.time()

    handler_cls = build_handler(content_dir, state_dir, touch)
    httpd = ThreadingHTTPServer((host, port), handler_cls)

    def watchdog() -> None:
        while True:
            time.sleep(60)
            if time.time() - last_activity[0] > idle_timeout_sec:
                httpd.shutdown()
                break

    threading.Thread(target=watchdog, daemon=True).start()
    httpd.serve_forever(poll_interval=0.5)


def pick_ephemeral_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(( "127.0.0.1", 0))
        return int(s.getsockname()[1])
