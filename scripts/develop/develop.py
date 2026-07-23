#!/usr/bin/env python3
"""Legacy shim — ``scripts.develop.develop`` redirects to ``scripts.design.design``.

``forge design`` is canonical. Older imports/smoke maps keep working via this module.
"""

from __future__ import annotations

from scripts.design.design import *  # noqa: F403
from scripts.design.design import main

if __name__ == "__main__":
    main()
