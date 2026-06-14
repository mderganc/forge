"""Compat shim — implementation lives in scripts.diagnose.tools.fmea_score."""

from __future__ import annotations

from scripts.diagnose.tools import fmea_score as _impl

if __name__ == "__main__":
    _impl.main()
