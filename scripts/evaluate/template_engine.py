"""Prompt template loading and variable substitution.

Templates are markdown files in the prompts/ directory. Variables use
{{VARIABLE_NAME}} syntax and are replaced by render_template().
"""

from __future__ import annotations

import os
import re
from importlib import resources
from pathlib import Path
from typing import Protocol, runtime_checkable

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


@runtime_checkable
class _ResourceLike(Protocol):
    def joinpath(self, *descendants: str): ...
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def is_file(self) -> bool: ...


def default_prompts_root() -> Path | _ResourceLike:
    """Resolve the prompts root.

    Resolution order:
    1) FORGE_CODEX_PROMPTS_DIR env var (developer override)
    2) Repo-local `prompts/` relative to this file (editable checkout)
    3) Packaged assets at `forge_codex.assets/prompts` (pipx install)
    """
    override = os.environ.get("FORGE_CODEX_PROMPTS_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if PROMPTS_DIR.is_dir():
        return PROMPTS_DIR

    # Packaged fallback (installed distribution)
    return resources.files("forge_codex.assets").joinpath("prompts")


def _join(root: Path | _ResourceLike, rel: str) -> Path | _ResourceLike:
    if isinstance(root, Path):
        return root / rel
    return root.joinpath(rel)


def _exists(path: Path | _ResourceLike) -> bool:
    if isinstance(path, Path):
        return path.exists()
    return path.is_file()


def load_template(name: str, prompts_dir: Path | _ResourceLike | None = None) -> str:
    """Load a prompt template by relative name (without .md extension).

    Args:
        name: Relative path like "shared/plan_parsing" or "pre/feasibility"
        prompts_dir: Root prompts directory. If omitted, auto-resolves via
            default_prompts_root().

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If template file doesn't exist.
    """
    root = prompts_dir or default_prompts_root()
    path = _join(root, f"{name}.md")
    if not _exists(path):
        raise FileNotFoundError(f"Template not found: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Some working copies on Windows may contain legacy cp1252 bytes.
        # Fall back so workflows still run; packaged assets are UTF-8.
        return path.read_text(encoding="cp1252")


def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace {{VARIABLE_NAME}} placeholders with values.

    Variables not present in the dict are left as-is (not an error).
    """
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)
