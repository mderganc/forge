"""Prompt template loading and variable substitution.

Templates are markdown files in the prompts/ directory. Variables use
{{VARIABLE_NAME}} syntax and are replaced by render_template().
"""

from __future__ import annotations

import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_template(name: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Load a prompt template by relative name (without .md extension).

    Args:
        name: Relative path like "shared/plan_parsing" or "pre/feasibility"
        prompts_dir: Root prompts directory (default: ../prompts relative to scripts/)

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If template file doesn't exist.
    """
    path = prompts_dir / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace {{VARIABLE_NAME}} placeholders with values.

    Variables not present in the dict are left as-is (not an error).
    """
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)
