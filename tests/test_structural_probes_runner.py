"""Tests for scripts.shared.structural_probes."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.shared import structural_probes as sp


def test_should_run_probes_matrix() -> None:
    assert sp.should_run_probes("code-review", 3)
    assert not sp.should_run_probes("code-review", 2)
    assert sp.should_run_probes("evaluate", 4, mode="post")
    assert sp.should_run_probes("evaluate", 1, mode="review")
    assert not sp.should_run_probes("evaluate", 4, mode="pre")


def test_detect_stack_python_only(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("x=1\n", encoding="utf-8")
    stack = sp.detect_stack(tmp_path)
    assert stack["python"] is True
    assert stack["node"] is False


def test_detect_stack_ts_primary_with_few_python_scripts(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"app"}', encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='tooling'\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    for i in range(8):
        (src / f"mod{i}.ts").write_text("export {}\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "gen.py").write_text("print('x')\n", encoding="utf-8")

    stack = sp.detect_stack(tmp_path)
    assert stack["node"] is True
    assert stack["python"] is False


def test_source_counts_skip_venv_without_descending(tmp_path: Path) -> None:
    """Regression: rglob walked .venv and timed out; pruned os.walk must not."""
    (tmp_path / "module.py").write_text("x = 1\n", encoding="utf-8")
    venv_pkg = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    venv_pkg.mkdir(parents=True)
    for i in range(500):
        (venv_pkg / f"dep{i}.py").write_text("pass\n", encoding="utf-8")

    assert sp._count_source_files(tmp_path, ".py") == 1
    inv = sp.build_stack_inventory(tmp_path)
    assert inv["counts"]["py"] == 1


def test_probe_ignore_skips_vendored_forge_next_snapshots(tmp_path: Path) -> None:
    live = tmp_path / "forge_next" / "pkg.py"
    live.parent.mkdir(parents=True)
    live.write_text("x = 1\n", encoding="utf-8")
    snap = tmp_path / "forge_next-0.14.9" / "duplicate.py"
    snap.parent.mkdir(parents=True)
    snap.write_text("y = 2\n", encoding="utf-8")

    assert sp._path_under_probe_ignore(snap, tmp_path) is True
    assert sp._path_under_probe_ignore(live, tmp_path) is False


def test_detect_stack_finds_package_json_under_client(tmp_path: Path) -> None:
    client = tmp_path / "client"
    client.mkdir()
    (client / "package.json").write_text('{"name":"ui"}', encoding="utf-8")
    (client / "src").mkdir()
    (client / "src" / "App.tsx").write_text("export default function App() {}\n", encoding="utf-8")

    stack = sp.detect_stack(tmp_path)
    assert stack["node"] is True
    assert sp.node_probe_root(tmp_path) == client.resolve()


def test_code_review_step3_uses_detected_repo_root_for_probes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = tmp_path / "consumer-app"
    app.mkdir()
    (app / "package.json").write_text('{"name":"consumer"}', encoding="utf-8")
    (app / "src").mkdir()
    (app / "src" / "index.ts").write_text("export const x = 1;\n", encoding="utf-8")

    captured: list[Path] = []

    def fake_inject(_body, *, repo_root, **kwargs):
        captured.append(Path(repo_root).resolve())
        return _body, None, {"stack": {"python": False, "node": True}, "probes": []}

    monkeypatch.chdir(app)
    monkeypatch.setattr(sp, "inject_structural_probes_section", fake_inject)

    import scripts.code_review.code_review as cr
    from scripts.shared.orchestrator import SkillState, save_state

    state_path = app / ".codex" / "forge" / "state" / "code-review-probe-root.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    st = SkillState(skill_name="code-review", max_step=6, current_step=2)
    st.custom = {"mode": "pr", "target": ".", "target_tokens": ["."]}
    save_state(st, state_path)

    monkeypatch.setattr(cr, "load_template", lambda _name: "{{body}}")
    monkeypatch.setattr(cr, "render_template", lambda template, _vars: template)
    monkeypatch.setattr(cr, "format_step_output", lambda *a, **k: "ok")

    cr.handle_step_n(3, state_file=str(state_path))

    assert captured
    assert captured[0] == app.resolve()


def test_run_probes_skip_without_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "mod.py").write_text("def f():\n    pass\n", encoding="utf-8")
    state_dir = tmp_path / "state"
    monkeypatch.setattr(
        "forge_next.structural_tools.resolve_pyscn_command",
        lambda: None,
    )
    monkeypatch.setattr(
        "forge_next.structural_tools.resolve_knip_command",
        lambda: None,
    )
    monkeypatch.setattr(
        "forge_next.structural_tools.resolve_madge_command",
        lambda: None,
    )
    payload = sp.run_probes(tmp_path, state_dir=state_dir)
    knip = next(p for p in payload["probes"] if p["tool"] == "knip")
    assert knip["status"] == "skip"
    sidecar = state_dir / sp.SIDECAR_NAME
    assert sidecar.is_file()
    loaded = json.loads(sidecar.read_text(encoding="utf-8"))
    assert loaded["stack"]["node"] is False


def test_inject_post_evaluate_step4_omits_eight_agents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.delenv("FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS", raising=False)

    body, _, _ = sp.inject_structural_probes_section(
        "body",
        skill_name="evaluate",
        step=4,
        repo_root=tmp_path,
        state_dir=state_dir,
        mode="post",
    )
    assert "agent selects tools" in body
    assert "STRUCTURAL QUALITY — eight parallel subagents" not in body


def test_inject_code_review_step3_includes_eight_agents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.delenv("FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS", raising=False)

    body, _, _ = sp.inject_structural_probes_section(
        "body",
        skill_name="code-review",
        step=3,
        repo_root=tmp_path,
        state_dir=state_dir,
    )
    assert "STRUCTURAL QUALITY — eight parallel subagents" in body
    assert "S3, S4, S8" in body


def test_inject_planning_banner_writes_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.delenv("FORGE_STRUCTURAL_PROBES_AUTO", raising=False)

    body, sidecar, payload = sp.inject_structural_probes_section(
        "body",
        skill_name="code-review",
        step=3,
        repo_root=tmp_path,
        state_dir=state_dir,
    )
    assert "agent selects tools" in body
    assert sidecar is None
    assert payload is None
    assert (state_dir / sp.PLAN_NAME).is_file()
    assert (state_dir / sp.INVENTORY_NAME).is_file()


def test_inject_auto_mode_runs_probes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setenv("FORGE_STRUCTURAL_PROBES_AUTO", "1")
    monkeypatch.setattr("forge_next.structural_tools.resolve_knip_command", lambda: None)
    monkeypatch.setattr("forge_next.structural_tools.resolve_madge_command", lambda: None)
    monkeypatch.setattr("forge_next.structural_tools.resolve_pyscn_command", lambda: None)

    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    body, sidecar, payload = sp.inject_structural_probes_section(
        "body",
        skill_name="code-review",
        step=3,
        repo_root=tmp_path,
        state_dir=state_dir,
    )
    assert "results" in body.lower()
    assert sidecar is not None
    assert payload is not None


def test_run_probes_respects_plan_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    sp.write_probe_plan(
        state_dir,
        {
            "tools": ["knip"],
            "node_root": ".",
            "reasoning": "Only knip for this test",
        },
    )
    monkeypatch.setattr("forge_next.structural_tools.resolve_knip_command", lambda: None)
    monkeypatch.setattr("forge_next.structural_tools.resolve_madge_command", lambda: None)
    monkeypatch.setattr("forge_next.structural_tools.resolve_pyscn_command", lambda: None)

    payload = sp.run_probes(tmp_path, state_dir=state_dir, plan=sp.load_probe_plan(state_dir))
    by_tool = {p["tool"]: p for p in payload["probes"]}
    assert by_tool["knip"]["status"] == "skip"
    assert "not selected" in by_tool["madge"]["summary"]
    assert "not selected" in by_tool["pyscn"]["summary"]


def test_code_review_step3_mentions_sidecar(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke: step 3 output includes structural-probes when injection runs."""
    import subprocess
    import sys

    from scripts.shared.orchestrator import SkillState, save_state

    repo = Path(__file__).resolve().parents[1]
    state = repo / ".codex" / "forge" / "state" / "code-review-structural-smoke.json"
    st = SkillState(skill_name="code-review", max_step=6, current_step=2)
    st.custom = {"mode": "pr", "target": ".", "target_tokens": ["."]}
    save_state(st, state)
    env = os.environ.copy()
    env.pop("FORGE_STRUCTURAL_PROBES_AUTO", None)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "code_review" / "code_review.py"),
            "--step",
            "3",
            "--state",
            str(state),
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    try:
        state.unlink(missing_ok=True)
    except OSError:
        pass
    assert proc.returncode == 0, proc.stderr
    assert "structural-probes" in proc.stdout.lower() or "STRUCTURAL PROBES" in proc.stdout
    assert "eight parallel subagents" in proc.stdout.lower()
    assert "8 subagents" in proc.stdout
