from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys

from forge_next.claude_graphify import (
    HOOK_MARKER,
    apply_claude_graphify_settings,
    audit_claude_graphify_hooks,
    hook_command,
    merge_graphify_hooks,
    resolve_forge_executable,
)
from forge_next.graphify_policy import (
    FORGE_DEVELOPER_INSTRUCTIONS_BODY,
    GRAPHIFY_DEVELOPER_INSTRUCTIONS_LEAD,
)
from forge_next.hooks import claude_graphify_hook as hook


def test_hook_command_uses_forge_executable_not_python_module(tmp_path: Path) -> None:
    forge = tmp_path / "forge"
    forge.write_text("", encoding="utf-8")
    cmd = hook_command("SessionStart", forge_exe=forge)
    assert "claude-graphify-hook SessionStart" in cmd
    assert " -m forge_next" not in cmd
    assert json.loads(cmd.split(" claude-graphify-hook", 1)[0]) == str(forge)


def test_resolve_forge_executable_prefers_pipx_bin_over_which(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next import claude_graphify as cg

    preferred_name = "forge.exe" if sys.platform == "win32" else "forge"
    preferred = tmp_path / "pipx-bin" / preferred_name
    preferred.parent.mkdir(parents=True)
    preferred.write_text("", encoding="utf-8")
    shadow = tmp_path / "shadow" / preferred_name
    shadow.parent.mkdir(parents=True)
    shadow.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        cg,
        "_pipx_forge_candidates",
        lambda home=None: [preferred],
    )
    monkeypatch.setattr(cg.shutil, "which", lambda _name: str(shadow))

    resolved = resolve_forge_executable()
    assert resolved == preferred.resolve()


def test_path_shadows_pipx_forge_detects_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next import claude_graphify as cg
    from forge_next.claude_graphify import path_shadows_pipx_forge

    preferred_name = "forge.exe" if sys.platform == "win32" else "forge"
    preferred = tmp_path / "pipx-bin" / preferred_name
    preferred.parent.mkdir(parents=True)
    preferred.write_text("", encoding="utf-8")
    shadow = tmp_path / "other" / preferred_name
    shadow.parent.mkdir(parents=True)
    shadow.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        cg,
        "_pipx_forge_candidates",
        lambda home=None: [preferred],
    )
    monkeypatch.setattr(cg.shutil, "which", lambda _name: str(shadow))

    shadowed, which_path, pipx_path = path_shadows_pipx_forge()
    assert shadowed is True
    assert which_path == shadow.resolve()
    assert pipx_path == preferred.resolve()


def test_pipx_forge_candidates_include_windows_exe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.claude_graphify import _pipx_forge_candidates

    home = tmp_path / "home"
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("PIPX_BIN_DIR", raising=False)
    monkeypatch.delenv("PIPX_HOME", raising=False)

    candidates = _pipx_forge_candidates(home)
    names = {c.name for c in candidates}
    if sys.platform == "win32":
        assert "forge.exe" in names
        assert any(
            c.parts[-4:] == ("pipx", "venvs", "forge-next", "Scripts")
            or (len(c.parts) >= 2 and c.parent.name == "Scripts")
            for c in candidates
            if c.name == "forge.exe"
        )
    else:
        assert "forge" in names
        assert any("forge-next" in c.parts and c.name == "forge" for c in candidates)


def test_audit_warns_on_python_module_hooks(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.json"
    cfg.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": '/usr/bin/python3.12 -m forge_next.hooks.claude_graphify_hook SessionStart',
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    warns = audit_claude_graphify_hooks(cfg)
    assert any("python -m forge_next" in w for w in warns)


def test_merge_graphify_hooks_adds_managed_entries() -> None:
    settings = merge_graphify_hooks({})
    hooks = settings["hooks"]
    assert "SessionStart" in hooks
    assert "PreToolUse" in hooks
    assert "UserPromptSubmit" in hooks
    assert any(HOOK_MARKER in str(h) for h in hooks["PreToolUse"])


def test_apply_claude_graphify_settings_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_forge = tmp_path / "bin" / "forge"
    fake_forge.parent.mkdir(parents=True)
    fake_forge.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "forge_next.claude_graphify.resolve_forge_executable",
        lambda: fake_forge,
    )
    monkeypatch.setattr(
        "forge_next.claude_graphify._verify_hook_launcher",
        lambda _f: None,
    )

    cfg = tmp_path / "settings.json"
    assert apply_claude_graphify_settings(cfg) == 0
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert HOOK_MARKER in json.dumps(data)
    assert "claude-graphify-hook" in json.dumps(data)


def test_codex_body_leads_with_graphify() -> None:
    assert FORGE_DEVELOPER_INSTRUCTIONS_BODY.startswith(GRAPHIFY_DEVELOPER_INSTRUCTIONS_LEAD[:40])


def test_session_start_spawns_background_refresh_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = Path(__file__).resolve().parents[1]
    if not (repo / "graphify-out" / "GRAPH_REPORT.md").is_file():
        pytest.skip("no graphify index in forge checkout")

    spawned: list[Path] = []

    def fake_spawn(cwd: Path, *, force: bool = False) -> bool:
        spawned.append(cwd)
        return True

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY_SESSION_REFRESH", raising=False)
    monkeypatch.setattr(hook, "_cwd", lambda _data: repo)
    monkeypatch.setattr("forge_next.graphify.spawn_refresh_background", fake_spawn)
    import io

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdin", type("R", (), {"read": lambda self: "{}"})())
    monkeypatch.setattr("sys.stdout", buf)
    hook.main(["SessionStart"])
    assert spawned == [repo]


def test_session_start_skips_refresh_when_opted_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = Path(__file__).resolve().parents[1]
    if not (repo / "graphify-out" / "GRAPH_REPORT.md").is_file():
        pytest.skip("no graphify index in forge checkout")

    spawned: list[Path] = []

    def fake_spawn(cwd: Path, *, force: bool = False) -> bool:
        spawned.append(cwd)
        return True

    monkeypatch.setenv("FORGE_SKIP_GRAPHIFY_SESSION_REFRESH", "1")
    monkeypatch.setattr(hook, "_cwd", lambda _data: repo)
    monkeypatch.setattr("forge_next.graphify.spawn_refresh_background", fake_spawn)
    import io

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdin", type("R", (), {"read": lambda self: "{}"})())
    monkeypatch.setattr("sys.stdout", buf)
    hook.main(["SessionStart"])
    assert spawned == []


def test_pre_tool_use_grep_emits_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = Path(__file__).resolve().parents[1]
    if not (repo / "graphify-out" / "GRAPH_REPORT.md").is_file():
        pytest.skip("no graphify index in forge checkout")

    monkeypatch.setattr(hook, "_cwd", lambda _data: repo)
    payload = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "foo"},
    }
    monkeypatch.setattr("sys.stdin", type("R", (), {"read": lambda self: json.dumps(payload)})())
    import io

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    hook.main(["PreToolUse"])
    out = buf.getvalue()
    assert "graphify STOP" in out
    assert "GRAPH_REPORT" in out
