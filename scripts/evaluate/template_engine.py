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


def packaged_prompts_root() -> _ResourceLike:
    """Packaged prompts shipped inside the forge-next wheel."""
    return resources.files("forge_next.assets").joinpath("prompts")


def default_prompts_root() -> Path | _ResourceLike:
    """Resolve the preferred prompts root (first candidate for load_template).

    Resolution order:
    1) FORGE_CODEX_PROMPTS_DIR env var (developer override)
    2) Repo-local `prompts/` relative to this file (editable checkout)
    3) Packaged assets at `forge_next.assets/prompts` (pipx install)

    load_template() also tries packaged assets when a template is missing from
    an earlier candidate (e.g. checkout prompts/ without plan/context.md).
    """
    override = os.environ.get("FORGE_CODEX_PROMPTS_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if PROMPTS_DIR.is_dir():
        return PROMPTS_DIR

    return packaged_prompts_root()


def _prompt_roots(prompts_dir: Path | _ResourceLike | None) -> list[Path | _ResourceLike]:
    """Ordered roots to search when loading a template."""
    if prompts_dir is not None:
        return [prompts_dir]

    roots: list[Path | _ResourceLike] = []
    override = os.environ.get("FORGE_CODEX_PROMPTS_DIR")
    if override:
        roots.append(Path(override).expanduser().resolve())
    if PROMPTS_DIR.is_dir():
        roots.append(PROMPTS_DIR)
    packaged = packaged_prompts_root()
    if not any(r is packaged for r in roots):
        roots.append(packaged)
    return roots


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
    rel = f"{name}.md"
    tried: list[str] = []
    for root in _prompt_roots(prompts_dir):
        path = _join(root, rel)
        tried.append(str(path))
        if not _exists(path):
            continue
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Some working copies on Windows may contain legacy cp1252 bytes.
            # Fall back so workflows still run; packaged assets are UTF-8.
            return path.read_text(encoding="cp1252")

    raise FileNotFoundError(
        f"Template not found: {rel} (searched: {', '.join(tried)})"
    )


def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace {{VARIABLE_NAME}} placeholders with values.

    Variables not present in the dict are left as-is (not an error).
    """
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)
