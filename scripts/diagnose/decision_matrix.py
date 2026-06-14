"""Compat shim — implementation lives in scripts.diagnose.tools.decision_matrix."""

from __future__ import annotations

from scripts.diagnose.tools import decision_matrix as _impl

if __name__ == "__main__":
    _impl.main()
