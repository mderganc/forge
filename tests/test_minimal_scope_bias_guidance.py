"""Phrase / path checks for minimal-scope bias guidance."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_scope_size_model_exists():
    text = (REPO / "templates" / "scope-size-model.md").read_text(encoding="utf-8")
    assert "Scope expansion" in text
    assert "trivial" in text


def test_design_scope_keeps_opportunities_as_expansion():
    text = (REPO / "prompts" / "design" / "scope.md").read_text(encoding="utf-8")
    assert "Scope expansion" in text
    assert "not recommended" in text.lower()
    assert "Opportunity" in text or "opportunities" in text.lower()


def test_prototype_stub_not_invokable():
    text = (REPO / "docs" / "forge" / "prototype-skill-stub.md").read_text(encoding="utf-8")
    assert "NOT YET INVOKABLE" in text or "not yet invokable" in text.lower()


def test_design_prompts_canonical_path():
    assert (REPO / "prompts" / "design" / "startup.md").is_file()
    assert (REPO / "scripts" / "design" / "design.py").is_file()


def test_load_template_develop_alias():
    from scripts.shared.template_engine import load_template

    a = load_template("design/scope")
    b = load_template("develop/scope")
    assert a == b
