#!/usr/bin/env python3
"""Export a pinned IIS payload and a private OMP configuration, without installing it."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def prepare(source: Path, revision: str, arena: Path, models: Path, method: Path, runtime_source: Path | None = None,
            verify_skill_source: Path | None = None) -> dict:
    source = source.resolve(strict=True)
    models = models.resolve(strict=True)
    method = method.resolve(strict=True)
    arena = arena.resolve()
    if arena.exists() or arena.is_relative_to(source):
        raise ValueError("arena must be a new directory outside the source checkout")
    sha = subprocess.run(["git", "rev-parse", f"{revision}^{{commit}}"], cwd=source, check=True, capture_output=True, text=True).stdout.strip()
    archive_bytes = subprocess.run(["git", "archive", "--format=tar", sha], cwd=source, check=True, capture_output=True).stdout
    arena.mkdir(parents=True, mode=0o700)
    payload = arena / "baseline-payload"
    payload.mkdir()
    rebased = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        archive.extractall(payload, filter="data")
        for member in archive.getmembers():
            if not member.isfile() or Path(member.name).suffix not in {".md", ".py", ".js", ".json", ".yaml", ".yml"}:
                continue
            destination = payload / member.name
            before = destination.read_bytes()
            after = before.replace(str(source).encode() + b"/", str(payload).encode() + b"/")
            if before != after:
                destination.write_bytes(after)
                rebased.append(member.name)
    runtime_overlays = {}
    if runtime_source is not None:
        runtime_source = runtime_source.resolve(strict=True)
        runtime_files = [runtime_source / "index.js", runtime_source / "package.json", *sorted((runtime_source / "src").glob("*.js"))]
        for source_file in runtime_files:
            if not source_file.is_file() or source_file.is_symlink():
                raise ValueError(f"invalid runtime source file: {source_file}")
            relative = source_file.relative_to(runtime_source)
            content = source_file.read_bytes().replace(str(source).encode() + b"/", str(payload).encode() + b"/")
            (payload / "delivery-runtime/ready-ticket-implement" / relative).write_bytes(content)
            runtime_overlays[str(relative)] = hashlib.sha256(content).hexdigest()
    verify_skill_overlays = {}
    if verify_skill_source is not None:
        verify_skill_source = verify_skill_source.resolve(strict=True)
        for relative in (Path("SKILL.md"), Path("references/verify.md")):
            source_file = verify_skill_source / relative
            if not source_file.is_file() or source_file.is_symlink():
                raise ValueError(f"invalid verifier skill source file: {source_file}")
            content = source_file.read_bytes().replace(str(source).encode() + b"/", str(payload).encode() + b"/")
            (payload / "companion-skills/ready-ticket-verify" / relative).write_bytes(content)
            verify_skill_overlays[str(relative)] = hashlib.sha256(content).hexdigest()
    method_target = payload / "evaluation-methods/production-heuristic-probing"
    method_target.mkdir(parents=True)
    shutil.copy2(method, method_target / "SKILL.md")
    host = arena / "host"
    host.mkdir(mode=0o700)
    shutil.copyfile(models, host / "models.yml")
    os.chmod(host / "models.yml", 0o600)
    config = {"skills": {"enabled": True, "enableSkillCommands": True,
              "enableCodexUser": False, "enableClaudeUser": False, "enableClaudeProject": False,
              "enablePiUser": False, "enablePiProject": False, "enableAgentsUser": False, "enableAgentsProject": False,
              "customDirectories": [str(payload), str(payload / "matt/skills"), str(payload / "companion-skills"), str(payload / "evaluation-methods")]},
              "tools": {"xdev": True}, "advisor": {"enabled": False}, "autoResume": False,
              "providers": {"fallbackChains": {}}, "extensions": []}
    (host / "config.yml").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.chmod(host / "config.yml", 0o600)
    result = {"schema": "iis-calibration-environment/v1", "source": str(source), "revision": sha,
              "arena": str(arena), "payload": str(payload), "agent_dir": str(host),
              "runtime_data": str(arena / "runtime-data"), "workflow": str(payload / "iis-workflow/SKILL.md"),
              "extension": str(payload / "delivery-runtime/ready-ticket-implement/index.js"),
              "rebased_files": rebased, "tool_exposure": "Ready essential native plus exact Ready device transport; tools.xdev=true",
              "runtime_source": str(runtime_source) if runtime_source is not None else None, "runtime_overlays": runtime_overlays,
              "verify_skill_source": str(verify_skill_source) if verify_skill_source is not None else None,
              "verify_skill_overlays": verify_skill_overlays,
              "models_sha256": hashlib.sha256((host / "models.yml").read_bytes()).hexdigest(),
              "config_sha256": hashlib.sha256((host / "config.yml").read_bytes()).hexdigest(),
              "runtime_admission": "NOT YET EXERCISED"}
    (arena / "environment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--arena", required=True, type=Path)
    parser.add_argument("--models", required=True, type=Path)
    parser.add_argument("--probe-method", required=True, type=Path)
    parser.add_argument("--runtime-source", type=Path, help="Explicit local runtime package snapshot; records every overlaid file hash")
    parser.add_argument("--verify-skill-source", type=Path, help="Explicit local verifier SKILL.md and references/verify.md snapshot; records both file hashes")
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.revision, args.arena, args.models, args.probe_method,
                             args.runtime_source, args.verify_skill_source), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
