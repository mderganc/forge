#!/usr/bin/env python3
"""
Diagnostic Report Generator

Creates a structured diagnostic report template with YAML frontmatter.
Used by the diagnose skill to initialize the report file that gets
populated throughout the diagnostic phases.

Usage:
  python diagnostic_report.py --title "Memory leak in API handler" --severity high
  python diagnostic_report.py --title "Flaky test in CI" --severity medium --output ./diagnostics/report.md
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path


TEMPLATE = """---
title: "Diagnostic Report: {title}"
date_created: "{date}"
severity: "{severity}"
status: "investigating"
root_cause_category: "pending"
methodologies_used: []
autonomy_mode: "{mode}"
---

# Diagnostic Report: {title}

## Phase 1: Problem Definition

### IS / IS-NOT Matrix

| Dimension | IS (observed) | IS NOT (not observed) | Distinction |
|-----------|---------------|----------------------|-------------|
| **WHAT** | | | |
| **WHERE** | | | |
| **WHEN** | | | |
| **EXTENT** | | | |

### Complexity Classification (Cynefin)

- **Domain**: _pending_
- **Rationale**: _pending_
- **Strategy**: _pending_

### Change Analysis

- **Last known good state**: _pending_
- **Recent changes**: _pending_
- **Key diff**: _pending_

---

## Phase 2: Evidence Summary

### Evidence Collected

- [ ] Error messages & stack traces
- [ ] Reproduction steps
- [ ] Timeline
- [ ] Metrics (before/after)
- [ ] Affected scope
- [ ] Source code review
- [ ] Dependencies
- [ ] Configuration
- [ ] Tests
- [ ] Git history

### Causal Factor Timeline

```
[T-?] Last known good → ... → [T-0] Issue reported → [T+0] Current state
```

### Barrier Analysis

| Defense Layer | Status | Notes |
|--------------|--------|-------|
| Type system / linter | | |
| Unit tests | | |
| Integration tests | | |
| Monitoring / alerting | | |
| Code review | | |

---

## Phase 3: MECE Cause Tree

### Software Fishbone Decomposition

```
                          ┌─ CODE ────────────
                          ├─ CONFIG ───────────
PROBLEM ──────────────────┤─ DATA ─────────────
                          ├─ INFRASTRUCTURE ────
                          ├─ DEPENDENCIES ──────
                          └─ ENVIRONMENT ───────
```

### Logic Tree

_To be populated during analysis_

### 5 Whys

_To be populated during analysis_

---

## Phase 4: Cause Ranking

### FMEA Scoring

| Cause | S | O | D | RPN | Priority |
|-------|---|---|---|-----|----------|
| _pending_ | | | | | |

### Bayesian Assessment

| Hypothesis | Prior | Evidence Fit | Posterior | Status |
|-----------|-------|-------------|-----------|--------|
| _pending_ | | | | |

### Confirmed Root Cause(s)

_pending_

---

## Phase 5: Solutions Evaluated

### Decision Matrix

| Solution | Effectiveness (3x) | Effort (2x) | Risk (2x) | Reversibility (1x) | Maintainability (1x) | Total |
|----------|-------------------|-------------|-----------|--------------------|--------------------|-------|
| _pending_ | | | | | | |

### Selected Solution

_pending_

### Rejected Alternatives

_pending_

---

## Phase 6: Validation Results

### Validation Ladder

| Level | Method | Result | Notes |
|-------|--------|--------|-------|
| Unit tests | | | |
| Integration tests | | | |
| Regression suite | | | |
| Reproduction case | | | |
| Static analysis | | | |
| Performance benchmark | | | |

### Swiss Cheese Verification

```
Layer 1: Code correctness ────── [  ]
Layer 2: Type system / linter ── [  ]
Layer 3: Unit tests ──────────── [  ]
Layer 4: Integration tests ───── [  ]
Layer 5: Monitoring / alerting ─ [  ]
Layer 6: Code review checks ──── [  ]
```

### Rollback Plan

_pending_

---

## Phase 7: Preventive Measures

### Systemic Recommendations

_pending_

### Lessons Learned

_pending_
"""


def generate_report(title: str, severity: str = "medium", mode: str = "guided", date: str | None = None) -> str:
    """Generate the diagnostic report content string.

    Args:
        title: Short problem description.
        severity: One of critical/high/medium/low.
        mode: One of guided/autonomous/interactive.
        date: ISO date string (YYYY-MM-DD). Defaults to today (UTC).

    Returns:
        Rendered report as a string.
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return TEMPLATE.format(title=title, date=date, severity=severity, mode=mode)


def main():
    parser = argparse.ArgumentParser(description="Diagnostic Report Generator")
    parser.add_argument("--title", required=True, help="Short problem description")
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        default="medium",
        help="Issue severity",
    )
    parser.add_argument(
        "--mode",
        choices=["guided", "autonomous", "interactive"],
        default="guided",
        help="Autonomy mode",
    )
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    content = generate_report(title=args.title, severity=args.severity, mode=args.mode)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        print(f"Report template written to: {out_path}")
    else:
        print(content)


if __name__ == "__main__":
    main()
