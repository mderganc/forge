"""Metric target comparison for iterate loops."""

from __future__ import annotations


def numeric_target_met(operator: str, current: float, target: float) -> bool:
    if operator == "gt":
        return current > target
    if operator == "gte":
        return current >= target
    if operator == "lt":
        return current < target
    if operator == "lte":
        return current <= target
    if operator == "eq":
        return abs(current - target) < 1e-9
    if operator == "neq":
        return abs(current - target) >= 1e-9
    return False
