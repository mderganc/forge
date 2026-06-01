"""Human and JSON output for forge install."""

from __future__ import annotations

import json
import os
from typing import Any

from forge_next.graphify import graphify_availability, graphify_install_notice_lines
from forge_next.structural_tools import (
    install_structural_tools as run_structural_tools_install,
    skip_structural_tools as env_skip_structural_tools,
    structural_tools_install_notice_lines,
    structural_tools_missing_warnings,
)


def run_structural_install(
    *,
    skip_structural_tools: bool,
) -> tuple[Any | None, bool, list[str]]:
    """Return (structural_result, skipped, extra_warnings)."""
    warnings: list[str] = []
    structural_skipped = skip_structural_tools or env_skip_structural_tools()
    structural_result = None
    if not structural_skipped:
        structural_result = run_structural_tools_install()
        if structural_result.warnings:
            warnings.extend(structural_result.warnings)
    elif skip_structural_tools:
        warnings.append(
            "Structural quality tools install skipped (--skip-structural-tools)."
        )
    warnings.extend(structural_tools_missing_warnings())
    return structural_result, structural_skipped, warnings


def build_install_payload(
    *,
    repo_url: str,
    ref: str,
    installed: dict[str, str],
    warnings: list[str],
    structural_result: Any | None,
) -> dict[str, Any]:
    graphify_available, graphify_status = graphify_availability()
    return {
        "command": "install",
        "repo_url": repo_url,
        "ref": ref,
        "installed": installed,
        "warnings": warnings,
        "graphify_available": graphify_available,
        "graphify_status": graphify_status,
        "graphify_onboarding": graphify_install_notice_lines(),
        "structural_tools": structural_result.to_dict() if structural_result else None,
        "structural_tools_onboarding": structural_tools_install_notice_lines(
            structural_result
        ),
        "error": None,
    }


def print_install_human(
    *,
    installed: dict[str, str],
    warnings: list[str],
    structural_result: Any | None,
    structural_skipped: bool,
    install_claude: bool,
    install_codex: bool,
) -> None:
    title = (
        "forge - install" if os.environ.get("FORGE_ASCII") == "1" else "forge — install"
    )
    print(title)
    print("=" * 60)
    for k, v in installed.items():
        print(f"{k}: {v}")
    if warnings:
        print("")
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")
    for line in graphify_install_notice_lines():
        print(line.rstrip())
    for line in structural_tools_install_notice_lines(structural_result):
        print(line.rstrip())
    print("")
    print("Next steps:")
    print("- Restart your editor/agent environment(s) so new commands are picked up.")
    print("- Run: forge doctor")
    if install_claude:
        print(
            "- Claude: Graphify hooks merged into ~/.claude/settings.json "
            "(re-run: forge claude-graphify)"
        )
    if install_codex:
        print(
            "- Codex: run `forge codex-agents --force` if developer_instructions "
            "were not updated"
        )
    if structural_skipped:
        print(
            "- Structural tools were skipped; re-run `forge install` without "
            "--skip-structural-tools or use `forge structural-tools install`"
        )


def emit_install_result(
    payload: dict[str, Any],
    *,
    json_output: bool,
    install_claude: bool,
    install_codex: bool,
    structural_result: Any | None,
    structural_skipped: bool,
) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=True))
        return
    print_install_human(
        installed=payload["installed"],
        warnings=payload["warnings"],
        structural_result=structural_result,
        structural_skipped=structural_skipped,
        install_claude=install_claude,
        install_codex=install_codex,
    )
