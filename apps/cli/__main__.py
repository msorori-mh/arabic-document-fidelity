"""CLI entry point: ``python -m apps.cli diagnose ...``."""

from __future__ import annotations

import sys

from apps.cli.diagnose import main

if __name__ == "__main__":
    sys.exit(main())
