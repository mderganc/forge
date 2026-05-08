"""Shared report generation for evaluate and diagnose skills.

Produces structured markdown reports with YAML frontmatter,
findings grouped by severity, dismissed items audit trail,
and custom sections.
"""

from __future__ import annotations

from scripts.shared.findings import Finding


def write_report(
    title: str,
    metadata: dict,
    summary: str,
    sections: list[tuple[str, str]],
    findings: list[Finding],
    dismissed: list[Finding],
    conclusion: str,
) -> str:
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f'title: "{title}"')
    for key, value in metadata.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")

    lines.append(f"# {title}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    for heading, content in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(content)
        lines.append("")

    lines.append("## Findings")
    lines.append("")

    if not findings:
        lines.append("No findings.")
        lines.append("")
    else:
        severity_order = ["critical", "warning", "suggestion"]
        severity_labels = {"critical": "Critical", "warning": "Warnings", "suggestion": "Suggestions"}
        for sev in severity_order:
            matched = [f for f in findings if f.severity == sev]
            if matched:
                lines.append(f"### {severity_labels[sev]}")
                lines.append("")
                for f in matched:
                    lines.append(f"- **{f.id}**: {f.title}")
                    lines.append(f"  {f.detail}")
                    lines.append("")

    lines.append("## Dismissed Items")
    lines.append("")
    if not dismissed:
        lines.append("None.")
        lines.append("")
    else:
        for f in dismissed:
            reason = f.user_note or "(no reason given)"
            lines.append(f"- **{f.id}**: {f.title} — *{reason}*")
            lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    lines.append(conclusion)
    lines.append("")

    return "\n".join(lines)
