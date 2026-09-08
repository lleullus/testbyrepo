#!/usr/bin/env python3
"""Snapshot one complete candidate payload into a private, uninstalled OMP arena."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil


def prepare(source: Path, arena: Path, models: Path, origins: list[Path] | None = None) -> dict:
    source = source.resolve(strict=True)
    models = models.resolve(strict=True)
    arena = arena.resolve()
    if arena.exists() or arena.is_relative_to(source):
        raise ValueError("arena must be a new directory outside the source checkout")
    installer_path = source / "scripts/sync_installed_iis.py"
    spec = importlib.util.spec_from_file_location("iis_candidate_bundle", installer_path)
    if spec is None or spec.loader is None:
        raise ValueError("candidate bundle installer is unavailable")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    arena.mkdir(parents=True, mode=0o700)
    store = arena / "bundles"
    manifest = installer.prepare(source, store, origins)
    payload = store / "releases" / manifest["bundle_id"]
    host = arena / "host"
    host.mkdir(mode=0o700)
    shutil.copyfile(models, host / "models.yml")
    os.chmod(host / "models.yml", 0o600)
    config = {"skills": {"enabled": True, "enableSkillCommands": True,
              "enableCodexUser": False, "enableClaudeUser": False, "enableClaudeProject": False,
              "enablePiUser": False, "enablePiProject": False, "enableAgentsUser": False, "enableAgentsProject": False,
              "customDirectories": [str(payload), str(payload / "matt/skills"), str(payload / "companion-skills")]},
              "tools": {"xdev": True}, "advisor": {"enabled": False}, "autoResume": False,
              "providers": {"fallbackChains": {}}, "extensions": []}
    (host / "config.yml").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.chmod(host / "config.yml", 0o600)
    result = {"schema": "iis-calibration-environment/v2", "source": str(source),
              "arena": str(arena), "payload": str(payload), "agent_dir": str(host),
              "bundle_id": manifest["bundle_id"], "bundle_manifest": str(payload / "bundle.json"),
              "runtime_data": str(arena / "runtime-data"), "workflow": str(payload / "iis-workflow/SKILL.md"),
              "validator": str(payload / "matt/skills/to-tickets/validate_ticket.py"),
              "extension": str(payload / "delivery-runtime/ready-ticket-implement/index.js"),
              "tool_exposure": "Ready native tools and host-native device transport; tools.xdev=true",
              "models_sha256": hashlib.sha256((host / "models.yml").read_bytes()).hexdigest(),
              "config_sha256": hashlib.sha256((host / "config.yml").read_bytes()).hexdigest(),
              "runtime_admission": "NOT YET EXERCISED", "loaded_identity": "NOT_CHECKED"}
    (arena / "environment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--arena", required=True, type=Path)
    parser.add_argument("--models", required=True, type=Path)
    parser.add_argument("--origin", action="append", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.arena, args.models, args.origin), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
