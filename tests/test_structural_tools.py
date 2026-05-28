"""Tests for forge_next.structural_tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_next import structural_tools as st


def test_default_prefix_is_under_user_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(st.sys, "platform", "win32")
    assert st.default_prefix() == tmp_path / "forge" / "structural-tools"


def test_skip_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_SKIP_STRUCTURAL_TOOLS", "1")
    assert st.skip_structural_tools() is True
    result = st.install_structural_tools()
    assert any("skipped" in w.lower() for w in result.warnings)


def test_write_and_load_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(st, "default_prefix", lambda: tmp_path / "npm")
    monkeypatch.setattr(st, "manifest_path", lambda: tmp_path / "structural-tools.json")
    result = st.StructuralToolsInstallResult(
        ok=True,
        prefix=str(tmp_path / "npm"),
        manifest_path="",
        knip=str(tmp_path / "npm" / "node_modules" / ".bin" / "knip"),
        madge=str(tmp_path / "npm" / "node_modules" / ".bin" / "madge"),
        pyscn="/usr/bin/pyscn",
        pyscn_via="pipx",
    )
    st.write_manifest(tmp_path / "npm", result)
    loaded = st.load_manifest()
    assert loaded is not None
    assert loaded["knip"] == result.knip
    assert loaded["pyscn_via"] == "pipx"


def test_resolve_knip_uses_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_KNIP_COMMAND", "/custom/knip --foo")
    assert st.resolve_knip_command() == ["/custom/knip", "--foo"]


def test_install_npm_skips_without_node(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(st, "_node_available", lambda: (False, "missing"))
    result = st.StructuralToolsInstallResult(ok=True, prefix=str(tmp_path), manifest_path="")
    st._install_npm_tools(tmp_path, result)
    assert any("Node" in w for w in result.warnings)


def test_install_structural_tools_mocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(st, "default_prefix", lambda: tmp_path / "npm")
    monkeypatch.setattr(st, "manifest_path", lambda: tmp_path / "manifest.json")

    def fake_npm(prefix: Path, result: st.StructuralToolsInstallResult) -> None:
        result.knip = str(prefix / "knip")
        result.madge = str(prefix / "madge")
        result.steps.append("fake npm")

    def fake_pyscn(result: st.StructuralToolsInstallResult) -> None:
        result.pyscn = "/bin/pyscn"
        result.pyscn_via = "pipx"

    monkeypatch.setattr(st, "_install_npm_tools", fake_npm)
    monkeypatch.setattr(st, "_install_pyscn", fake_pyscn)

    result = st.install_structural_tools()
    assert result.ok
    assert result.knip and result.madge and result.pyscn
    assert tmp_path.joinpath("manifest.json").is_file()
    data = json.loads(tmp_path.joinpath("manifest.json").read_text(encoding="utf-8"))
    assert data["knip"] == result.knip


def test_doctor_checks_without_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(st, "load_manifest", lambda: None)
    monkeypatch.setattr(st, "_npx_executable", lambda: None)
    monkeypatch.setattr(st.shutil, "which", lambda name: None)
    checks = st.doctor_checks()
    assert checks["knip"] is None
    warnings = st.structural_tools_warnings_for_doctor()
    assert len(warnings) == 3
    assert any("knip" in w for w in warnings)
    assert any("madge" in w for w in warnings)
    assert any("pyscn" in w for w in warnings)


def test_missing_warnings_empty_when_skip_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_SKIP_STRUCTURAL_TOOLS", "1")
    assert st.structural_tools_missing_warnings() == []
