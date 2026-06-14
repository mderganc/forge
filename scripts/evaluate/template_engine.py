"""Backward-compatible re-export of scripts.shared.template_engine."""

from scripts.shared.template_engine import (  # noqa: F401
    PROMPTS_DIR,
    WORKFLOW_PROMPT_TEMPLATES,
    default_prompts_root,
    load_template,
    packaged_prompts_root,
    read_prompt_file,
    render_template,
    validate_workflow_prompts,
)

__all__ = [
    "PROMPTS_DIR",
    "WORKFLOW_PROMPT_TEMPLATES",
    "default_prompts_root",
    "load_template",
    "packaged_prompts_root",
    "read_prompt_file",
    "render_template",
    "validate_workflow_prompts",
]
