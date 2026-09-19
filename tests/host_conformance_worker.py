#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

payload = json.load(sys.stdin)
store = Path(os.environ["IIS_TEST_STORE_PATH"])
blocked = False
try:
    list(store.iterdir())
except PermissionError:
    blocked = True
if not blocked:
    print(json.dumps({"error": "worker could read supervisor store"}))
    raise SystemExit(9)

inputs = payload.get("inputs", [])
if not inputs:
    print(json.dumps({"error": "no fixed handoff inputs"}))
    raise SystemExit(10)
for item in inputs:
    path = Path(item["path"])
    if not path.is_file():
        print(json.dumps({"error": f"missing handoff {path}"}))
        raise SystemExit(11)
    path.read_bytes()

if payload["kind"] == "product-thesis-review":
    print(json.dumps({
        "result": {
            "completion": "COMPLETE",
            "worker_uid": os.geteuid(),
            "store_access": "blocked",
        },
        "frontier": [],
        "findings": [],
    }))
elif payload["kind"] == "iis-role":
    print(json.dumps({
        "worker_uid": os.geteuid(),
        "store_access": "blocked",
        "role": payload["role"],
    }))
else:
    print(json.dumps({"error": "unknown payload kind"}))
    raise SystemExit(12)
