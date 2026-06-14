"""Compat shim — implementation lives in scripts.diagnose.tools.diagnostic_report."""

from __future__ import annotations

from scripts.diagnose.tools.diagnostic_report import *  # noqa: F403
from scripts.diagnose.tools import diagnostic_report as _impl

if __name__ == "__main__":
    _impl.main()
