#!/usr/bin/env python3
"""
FMEA Risk Priority Number (RPN) Calculator

Reads candidate causes from JSON, calculates RPN scores (Severity x Occurrence x Detection),
and outputs a ranked Markdown table.

Input JSON format:
[
  {
    "cause": "Race condition in payment handler",
    "severity": 8,
    "occurrence": 6,
    "detection": 7,
    "evidence": "Intermittent duplicate charges in logs",
    "category": "code"
  },
  ...
]

Scores (1-10 scale):
  Severity:   1=cosmetic, 3=minor UX, 5=feature broken, 7=data affected, 10=data loss/security
  Occurrence:  1=very unlikely cause, 3=unlikely, 5=plausible, 7=probable, 10=almost certain
  Detection:   1=easy to verify, 3=straightforward, 5=requires effort, 7=hard, 10=extremely hard
"""

import argparse
import json
import sys
from pathlib import Path


SEVERITY_LABELS = {
    (1, 2): "Cosmetic",
    (3, 4): "Minor",
    (5, 6): "Moderate",
    (7, 8): "Major",
    (9, 10): "Critical",
}

OCCURRENCE_LABELS = {
    (1, 2): "Very unlikely",
    (3, 4): "Unlikely",
    (5, 6): "Plausible",
    (7, 8): "Probable",
    (9, 10): "Near certain",
}

DETECTION_LABELS = {
    (1, 2): "Easy to verify",
    (3, 4): "Straightforward",
    (5, 6): "Moderate effort",
    (7, 8): "Difficult",
    (9, 10): "Very difficult",
}


def get_label(score: int, label_map: dict) -> str:
    for (lo, hi), label in label_map.items():
        if lo <= score <= hi:
            return label
    return "Unknown"


def calculate_rpn(causes: list[dict]) -> list[dict]:
    results = []
    for c in causes:
        s = int(c.get("severity", 5))
        o = int(c.get("occurrence", 5))
        d = int(c.get("detection", 5))
        rpn = s * o * d
        results.append({
            "cause": c["cause"],
            "category": c.get("category", "unknown"),
            "severity": s,
            "severity_label": get_label(s, SEVERITY_LABELS),
            "occurrence": o,
            "occurrence_label": get_label(o, OCCURRENCE_LABELS),
            "detection": d,
            "detection_label": get_label(d, DETECTION_LABELS),
            "rpn": rpn,
            "evidence": c.get("evidence", ""),
            "priority": "CRITICAL" if rpn >= 300 else "HIGH" if rpn >= 150 else "MEDIUM" if rpn >= 50 else "LOW",
        })
    results.sort(key=lambda x: x["rpn"], reverse=True)
    return results


def render_markdown(results: list[dict]) -> str:
    lines = [
        "## FMEA Cause Ranking",
        "",
        "| Rank | Cause | Category | S | O | D | RPN | Priority | Evidence |",
        "|------|-------|----------|---|---|---|-----|----------|----------|",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['cause']} | {r['category']} | "
            f"{r['severity']} ({r['severity_label']}) | "
            f"{r['occurrence']} ({r['occurrence_label']}) | "
            f"{r['detection']} ({r['detection_label']}) | "
            f"**{r['rpn']}** | {r['priority']} | {r['evidence']} |"
        )

    lines.extend([
        "",
        "### Priority Thresholds",
        "- **CRITICAL** (RPN >= 300): Investigate immediately",
        "- **HIGH** (RPN >= 150): Investigate in current cycle",
        "- **MEDIUM** (RPN >= 50): Schedule investigation",
        "- **LOW** (RPN < 50): Monitor only",
        "",
        f"**Total causes evaluated**: {len(results)}",
    ])

    critical = sum(1 for r in results if r["priority"] == "CRITICAL")
    high = sum(1 for r in results if r["priority"] == "HIGH")
    if critical:
        lines.append(f"**CRITICAL causes requiring immediate attention**: {critical}")
    if high:
        lines.append(f"**HIGH priority causes**: {high}")

    # Pareto: top 20% of causes by RPN
    top_n = max(1, len(results) // 5)
    top_rpn_sum = sum(r["rpn"] for r in results[:top_n])
    total_rpn_sum = sum(r["rpn"] for r in results)
    if total_rpn_sum > 0:
        pct = round(top_rpn_sum / total_rpn_sum * 100)
        lines.append(f"**Pareto**: Top {top_n} cause(s) account for {pct}% of total risk")

    return "\n".join(lines)


def render_json(results: list[dict]) -> str:
    return json.dumps(results, indent=2)


def main():
    parser = argparse.ArgumentParser(description="FMEA RPN Calculator")
    parser.add_argument("--input", required=True, help="JSON file with causes")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        causes = json.load(f)

    if not isinstance(causes, list):
        print("Error: Input must be a JSON array", file=sys.stderr)
        sys.exit(1)

    results = calculate_rpn(causes)

    if args.format == "json":
        output = render_json(results)
    else:
        output = render_markdown(results)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
