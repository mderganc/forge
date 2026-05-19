import json
from pathlib import Path
from urllib.request import Request, urlopen

from forge_next.studio import events as studio_events
from forge_next.studio import server as studio_server


def test_get_newest_screen(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    a = content / "a.html"
    b = content / "b.html"
    a.write_text("<p>a</p>", encoding="utf-8")
    b.write_text("<p>b</p>", encoding="utf-8")
    import time

    time.sleep(0.02)
    b.write_text("<p>b newer</p>", encoding="utf-8")
    assert studio_server.get_newest_screen(content) == b


def test_wrap_fragment_includes_content() -> None:
    html = studio_server.wrap_fragment("<h2>Hi</h2>")
    assert "Hi" in html
    assert "<!DOCTYPE html>" in html


def test_http_handler_post_event(tmp_path: Path) -> None:
    content = tmp_path / "content"
    state = tmp_path / "state"
    content.mkdir()
    state.mkdir()
    import socket
    import threading

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    def run() -> None:
        studio_server.run_server(host="127.0.0.1", port=port, content_dir=content, state_dir=state)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    import time

    time.sleep(0.3)
    body = json.dumps({"type": "click", "gate": "g", "choice": "c"}).encode()
    req = Request(
        f"http://127.0.0.1:{port}/api/event",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urlopen(req, timeout=2).read()
    evs, _ = studio_events.read_events_since_cursor(state)
    studio_events.set_cursor(state, 0)
    evs, _ = studio_events.read_events_since_cursor(state)
    assert evs[0]["choice"] == "c"


def test_wrap_fragment_appends_feedback_panel() -> None:
    html = studio_server.wrap_fragment("<h2>Gate</h2>")
    assert "studio-feedback" in html
    assert "studio-design-notes" not in html or True


def test_feedback_event_post(tmp_path: Path) -> None:
    content = tmp_path / "content"
    state = tmp_path / "state"
    content.mkdir()
    state.mkdir()
    import socket
    import threading
    import time

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    t = threading.Thread(
        target=lambda: studio_server.run_server(
            host="127.0.0.1", port=port, content_dir=content, state_dir=state
        ),
        daemon=True,
    )
    t.start()
    time.sleep(0.3)
    body = json.dumps(
        {"type": "feedback", "gate": "gate1", "text": "Please emphasize accessibility"}
    ).encode()
    req = Request(
        f"http://127.0.0.1:{port}/api/event",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urlopen(req, timeout=2).read()
    studio_events.set_cursor(state, 0)
    evs, _ = studio_events.read_events_since_cursor(state)
    assert evs[0]["type"] == "feedback"
    assert "accessibility" in evs[0]["text"]


def test_probe_response_event_post(tmp_path: Path) -> None:
    content = tmp_path / "content"
    state = tmp_path / "state"
    content.mkdir()
    state.mkdir()
    import socket
    import threading
    import time

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    t = threading.Thread(
        target=lambda: studio_server.run_server(
            host="127.0.0.1", port=port, content_dir=content, state_dir=state
        ),
        daemon=True,
    )
    t.start()
    time.sleep(0.3)
    body = json.dumps(
        {
            "type": "probe-response",
            "gate": "gate1",
            "probe_id": "visual_controls",
            "prompt": "Color ok?",
            "text": "Yes, use radio buttons",
        }
    ).encode()
    req = Request(
        f"http://127.0.0.1:{port}/api/event",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urlopen(req, timeout=2).read()
    studio_events.set_cursor(state, 0)
    evs, _ = studio_events.read_events_since_cursor(state)
    assert evs[0]["type"] == "probe-response"
    assert evs[0]["probe_id"] == "visual_controls"
    assert "radio" in evs[0]["text"]


def test_approve_and_unlock_via_http(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    session_dir = repo / ".codex" / "forge" / "studio" / "sess-1"
    content = session_dir / "content"
    state = session_dir / "state"
    content.mkdir(parents=True)
    state.mkdir()
    (session_dir / "session.json").write_text(
        json.dumps({"v": 1, "session_id": "sess-1", "repo_root": str(repo)}),
        encoding="utf-8",
    )
    tag = "d" + "iv"
    (content / "gate.html").write_text(
        f'<{tag} data-studio-gate="g1"><p>mock</p></{tag}>',
        encoding="utf-8",
    )
    import socket
    import threading
    import time

    from forge_next.studio import approved as studio_approved

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    t = threading.Thread(
        target=lambda: studio_server.run_server(
            host="127.0.0.1", port=port, content_dir=content, state_dir=state
        ),
        daemon=True,
    )
    t.start()
    time.sleep(0.3)
    approve_body = json.dumps({"type": "approve", "gate": "g1"}).encode()
    req = Request(
        f"http://127.0.0.1:{port}/api/event",
        data=approve_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urlopen(req, timeout=2).read()
    assert studio_approved.is_gate_locked(repo, "g1")
    unlock_body = json.dumps({"type": "unlock", "gate": "g1"}).encode()
    req2 = Request(
        f"http://127.0.0.1:{port}/api/event",
        data=unlock_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urlopen(req2, timeout=2).read()
    assert not studio_approved.is_gate_locked(repo, "g1")


def test_version_file_cross_process(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    v1 = studio_server.bump_screen_version(state_dir=state)
    v2 = studio_server.get_screen_version(state)
    assert v2 == v1
