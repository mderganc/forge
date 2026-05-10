"""Tests for plan resolution including native IDE plan directories."""

from __future__ import annotations

import pytest

from scripts.evaluate.plan_resolver import (
    AmbiguousPlanError,
    _find_md_files,
    format_native_plan_hints,
    native_plan_directories,
    resolve_plan,
    resolve_plan_file,
)


def test_native_plan_directories_includes_repo_cursor_plans(tmp_path):
    d = tmp_path / ".cursor" / "plans"
    d.mkdir(parents=True)
    assert d in native_plan_directories(tmp_path)


def test_find_md_includes_markdown_under_cursor_plans(tmp_path):
    p = tmp_path / ".cursor" / "plans" / "hello.plan.md"
    p.parent.mkdir(parents=True)
    p.write_text("---\ntitle: Hello\n---\n# x\n", encoding="utf-8")
    found = _find_md_files(tmp_path)
    assert p.resolve() in [x.resolve() for x in found]


def test_resolve_plan_keywords_finds_native_plan(tmp_path):
    f = tmp_path / ".cursor" / "plans" / "auth_workflow.md"
    f.parent.mkdir(parents=True)
    f.write_text("# Auth workflow\n", encoding="utf-8")
    got = resolve_plan("auth workflow", tmp_path, return_matches=False)
    assert got.resolve() == f.resolve()


def test_resolve_plan_file_ambiguous(tmp_path):
    a = tmp_path / "docs" / "auth_feature_alpha.md"
    b = tmp_path / "docs" / "auth_feature_beta.md"
    a.parent.mkdir(parents=True)
    a.write_text("# x\n", encoding="utf-8")
    b.write_text("# y\n", encoding="utf-8")
    with pytest.raises(AmbiguousPlanError) as exc:
        resolve_plan_file("auth feature", tmp_path)
    assert len(exc.value.matches) >= 2


def test_format_native_plan_hints_is_markdown(tmp_path):
    h = format_native_plan_hints(tmp_path)
    assert "native" in h.lower()
    assert "`" in h or "none found" in h.lower()


def test_resolve_plan_file_absolute_path(tmp_path):
    f = tmp_path / "p.md"
    f.write_text("x", encoding="utf-8")
    assert resolve_plan_file(str(f), tmp_path) == f.resolve()
