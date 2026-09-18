#!/usr/bin/env python3
"""Backward-compatible executable entry point."""
from logtrim.cli import main

if __name__ == "__main__":
    raise SystemExit(main())