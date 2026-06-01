"""Smoke tests for split forge_next CLI modules."""

from __future__ import annotations

from pathlib import Path

from forge_next import cli_install, cli_inspect, cli_runtime
from forge_next.cli import build_parser, resolve_repo_root


def test_cli_modules_import() -> None:
    assert callable(cli_install.run_install)
    assert callable(cli_inspect.run_doctor)
    assert callable(cli_runtime.run_module_main)


def test_resolve_repo_root_finds_forge_repo() -> None:
    root = Path(__file__).resolve().parents[1]
    assert resolve_repo_root(root) == root


def test_build_parser_includes_ship() -> None:
    parser = build_parser()
    args = parser.parse_args(["ship", "--step", "1", "--repo", str(Path(__file__).parents[1])])
    assert args.command == "ship"
    assert args.step == 1
