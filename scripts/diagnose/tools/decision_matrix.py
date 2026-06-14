#!/usr/bin/env python3
"""
Weighted Decision Matrix for Solution Comparison

Reads candidate solutions from JSON, applies weighted scoring,
and outputs a ranked Markdown comparison table.

Input JSON format:
[
  {
    "solution": "Add mutex around payment handler",
    "type": "proper_fix",
    "root_cause": "Race condition in payment handler",
    "scores": {
      "effectiveness": 8,
      "effort": 4,
      "risk": 3,
      "reversibility": 9,
      "maintainability": 7
    },
    "description": "Wrap critical section with sync.Mutex",
    "side_effects": "Slight latency increase under contention",
    "rollback_plan": "git revert commit"
  },
  ...
]

Scoring (1-10, higher is better for all EXCEPT effort and risk which are inverted):
  Effectiveness:   How well does it fix the root cause? 10 = complete fix
  Effort:          How much work? 1 = trivial, 10 = massive (inverted in scoring)
  Risk:            Risk of introducing new issues? 1 = safe, 10 = dangerous (inverted)
  Reversibility:   How easy to roll back? 10 = instant rollback
  Maintainability: Long-term maintenance burden? 10 = zero burden

Default weights: effectiveness=3, effort=2, risk=2, reversibility=1, maintainability=1
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_WEIGHTS = {
    "effectiveness": 3,
    "effort": 2,
    "risk": 2,
    "reversibility": 1,
    "maintainability": 1,
}

INVERTED_DIMENSIONS = {"effort", "risk"}


def score_solution(solution: dict, weights: dict) -> dict:
    scores = solution.get("scores", {})
    weighted_scores = {}
    total = 0

    for dim, weight in weights.items():
        raw = int(scores.get(dim, 5))
        adjusted = (11 - raw) if dim in INVERTED_DIMENSIONS else raw
        weighted = adjusted * weight
        weighted_scores[dim] = {
            "raw": raw,
            "adjusted": adjusted,
            "weight": weight,
            "weighted": weighted,
        }
        total += weighted

    max_possible = sum(10 * w for w in weights.values())

    return {
        **solution,
        "weighted_scores": weighted_scores,
        "total_score": total,
        "max_score": max_possible,
        "percentage": round(total / max_possible * 100) if max_possible > 0 else 0,
    }


def render_markdown(results: list[dict], weights: dict) -> str:
    dims = list(weights.keys())
    dim_headers = []
    for d in dims:
        w = weights[d]
        inv = " (inv)" if d in INVERTED_DIMENSIONS else ""
        dim_headers.append(f"{d.title()}{inv} ({w}x)")

    lines = [
        "## Solution Decision Matrix",
        "",
        f"| Rank | Solution | Type | {' | '.join(dim_headers)} | **Total** | **%** |",
        f"|------|----------|------|{'|'.join(['---'] * len(dims))}|-------|-----|",
    ]

    for i, r in enumerate(results, 1):
        dim_cells = []
        for d in dims:
            ws = r["weighted_scores"][d]
            raw = ws["raw"]
            weighted = ws["weighted"]
            dim_cells.append(f"{raw}→{weighted}")

        sol_type = r.get("type", "unknown")
        lines.append(
            f"| {i} | {r['solution']} | {sol_type} | "
            f"{' | '.join(dim_cells)} | "
            f"**{r['total_score']}** | {r['percentage']}% |"
        )

    lines.extend(["", "### Solution Details", ""])
    for i, r in enumerate(results, 1):
        lines.append(f"**{i}. {r['solution']}** (Score: {r['total_score']}/{r['max_score']}, {r['percentage']}%)")
        if r.get("description"):
            lines.append(f"   - Description: {r['description']}")
        if r.get("root_cause"):
            lines.append(f"   - Addresses: {r['root_cause']}")
        if r.get("side_effects"):
            lines.append(f"   - Side effects: {r['side_effects']}")
        if r.get("rollback_plan"):
            lines.append(f"   - Rollback: {r['rollback_plan']}")
        lines.append("")

    # Recommendation
    if results:
        best = results[0]
        lines.extend([
            "### Recommendation",
            "",
            f"**{best['solution']}** scores highest at {best['percentage']}% "
            f"({best['total_score']}/{best['max_score']}). ",
        ])
        if len(results) > 1:
            gap = results[0]["total_score"] - results[1]["total_score"]
            if gap <= 5:
                lines.append(
                    f"Note: Only {gap} points ahead of #{2} — consider discussing trade-offs."
                )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Weighted Decision Matrix")
    parser.add_argument("--input", required=True, help="JSON file with solutions")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--weights", help="JSON string of custom weights")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        solutions = json.load(f)

    weights = DEFAULT_WEIGHTS
    if args.weights:
        weights = {**DEFAULT_WEIGHTS, **json.loads(args.weights)}

    results = [score_solution(s, weights) for s in solutions]
    results.sort(key=lambda x: x["total_score"], reverse=True)

    if args.format == "json":
        output = json.dumps(results, indent=2)
    else:
        output = render_markdown(results, weights)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
