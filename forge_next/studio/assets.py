"""Load bundled Studio static assets from forge_next.assets."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def asset_text(name: str) -> str:
    ref = resources.files("forge_next.assets").joinpath("studio").joinpath(name)
    return ref.read_text(encoding="utf-8")


def asset_bytes(name: str) -> bytes:
    ref = resources.files("forge_next.assets").joinpath("studio").joinpath(name)
    return ref.read_bytes()
