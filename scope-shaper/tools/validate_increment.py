#!/usr/bin/env python3
"""Validate one Scope-selected ready-for-matt construction Increment."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


VALIDATOR_PATH = Path(__file__).with_name("validate_scope_result.py")
spec = importlib.util.spec_from_file_location("scope_result_validator_for_increment", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
assert spec.loader is not None
spec.loader.exec_module(validator)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("increment", type=Path)
    args = parser.parse_args()
    try:
        validator.validate_selected_increment(args.increment)
    except (OSError, validator.ValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
