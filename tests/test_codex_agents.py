from __future__ import annotations

from pathlib import Path

import pytest

from forge_next.codex_agents import (
    FORGE_DEVELOPER_INSTRUCTIONS_BODY,
    apply_codex_agents_config,
)


def test_codex_agents_writes_snippet(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    rc = apply_codex_agents_config(cfg)
    assert rc == 0
    text = cfg.read_text(encoding="utf-8")
    assert "developer_instructions" in text
    assert FORGE_DEVELOPER_INSTRUCTIONS_BODY in text


def test_codex_agents_idempotent(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    assert apply_codex_agents_config(cfg) == 0
    assert apply_codex_agents_config(cfg) == 0


def test_codex_agents_refuses_overwrite_without_force(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text('developer_instructions = "keep me"\n', encoding="utf-8")
    rc = apply_codex_agents_config(cfg, force=False)
    assert rc == 1
    assert cfg.read_text(encoding="utf-8") == 'developer_instructions = "keep me"\n'


def test_codex_agents_dry_run_skips_write(tmp_path: Path) -> None:
    cfg = tmp_path / "miss.toml"
    assert apply_codex_agents_config(cfg, dry_run=True) == 0
    assert not cfg.exists()


def test_codex_agents_force_overwrites(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text('developer_instructions = "keep me"\n', encoding="utf-8")
    rc = apply_codex_agents_config(cfg, force=True)
    assert rc == 0
    assert FORGE_DEVELOPER_INSTRUCTIONS_BODY in cfg.read_text(encoding="utf-8")


def test_codex_agents_preserves_other_keys(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text('model = "gpt-5.4"\n', encoding="utf-8")
    assert apply_codex_agents_config(cfg) == 0
    body = cfg.read_text(encoding="utf-8")
    assert 'model = "gpt-5.4"' in body
    assert FORGE_DEVELOPER_INSTRUCTIONS_BODY in body


def test_forge_cli_codex_agents(tmp_path: Path) -> None:
    from forge_next.cli import main

    cfg = tmp_path / "config.toml"
    with pytest.raises(SystemExit) as ei:
        main(["codex-agents", "--config", str(cfg)])
    assert ei.value.code == 0
    assert FORGE_DEVELOPER_INSTRUCTIONS_BODY in cfg.read_text(encoding="utf-8")
