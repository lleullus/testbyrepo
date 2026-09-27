#!/usr/bin/env python3
"""Compare logtrim 0.1 output complexity with the current analyzer by corpus family."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FAMILIES = (
    "generic-text", "json", "logfmt", "http", "kubernetes-event",
    "kubectl-pods", "kubectl-nodes", "kubectl-describe", "python-traceback",
    "java-stacktrace", "high-cardinality-id", "mixed-production",
)
TITLES = {
    "Event Logs": "event", "JSON Logs": "json", "Snapshot Output": "snapshot",
    "Describe Output": "describe", "Generic Text": "generic",
}
GROUP = re.compile(r"^\[(\d+)\] ")


def _fixtures() -> dict[str, list[str]]:
    pods = [
        "NAMESPACE NAME READY STATUS RESTARTS AGE",
        "default  api-7c9d8f6b7c-abc12 1/1 Running 0 2d",
        "default  api-7c9d8f6b7c-def34 0/1 CrashLoopBackOff 4 2d",
        "default  api-7c9d8f6b7c-ghi56 1/1 Running 0 3d",
        "monitoring  worker-59d7648d6f-abc12 1/1 Running 1 1d",
    ]
    nodes = [
        "NAME STATUS ROLES AGE VERSION",
        "node-01 Ready control-plane 3d v1.32.1",
        "node-02 NotReady <none> 1d v1.32.1",
        "node-03 Ready control-plane 5d v1.32.1",
    ]
    describe = [
        "Name: api-7c9d8f6b7c-abc12", "Namespace: default", "Labels:",
        "  app=api", "  pod-template-hash=abc12", "Annotations:",
        "  checksum/config=111", "Node: node-01/10.0.0.1", "Status: Running",
        "IP: 10.0.0.2", "Restart Count: 0", "Conditions:", "  Type Status",
        "  Ready True", "  ContainersReady True", "Events:",
        "  Type Reason Age From Message", "  Normal Pulled 2m kubelet image pulled",
        "  Warning BackOff 1m kubelet backoff", "",
        "Name: api-7c9d8f6b7c-def34", "Namespace: default", "Labels:",
        "  app=api", "  pod-template-hash=def34", "Annotations:",
        "  checksum/config=222", "Node: node-02/10.0.0.3", "Status: Running",
        "IP: 10.0.0.4", "Restart Count: 1", "Conditions:", "  Type Status",
        "  Ready True", "  ContainersReady True", "Events:",
        "  Type Reason Age From Message", "  Normal Pulled 3m kubelet image pulled",
        "  Warning BackOff 1m kubelet backoff",
    ]
    fixtures = {
        "generic-text": ["worker started", "worker started", "cache warmed", "worker stopped"],
        "json": [
            '{"ts":"2026-09-27T10:00:00Z","level":"INFO","message":"ok","request_id":"abc123"}',
            '{"ts":"2026-09-27T10:00:01Z","level":"INFO","message":"ok","request_id":"def456"}',
            '{"ts":"2026-09-27T10:00:02Z","level":"ERROR","message":"failed","status_code":503}',
        ],
        "logfmt": ["2026-09-27T10:00:00Z INFO level=info event=connected peer=10.0.0.1",
                   "2026-09-27T10:00:01Z INFO level=info event=connected peer=10.0.0.2",
                   "2026-09-27T10:00:02Z ERROR level=error event=failed code=E503"],
        "http": ["2026-09-27T10:00:00Z INFO GET /users/123 HTTP/1.1 200",
                 "2026-09-27T10:00:01Z INFO GET /users/456 HTTP/1.1 200",
                 "2026-09-27T10:00:02Z INFO GET /users/789 HTTP/1.1 404",
                 "2026-09-27T10:00:03Z INFO POST /orders/123 HTTP/1.1 201"],
        "kubernetes-event": [
            "2026-09-27T10:00:00Z INFO Normal Pulled pod/api-abc12 Container image pulled",
            "2026-09-27T10:00:01Z INFO Normal Pulled pod/api-def34 Container image pulled",
            "2026-09-27T10:00:02Z WARN Warning BackOff pod/api-ghi56 Back-off restarting failed container",
        ],
        "kubectl-pods": pods,
        "kubectl-nodes": nodes,
        "kubectl-describe": describe,
        "python-traceback": [
            "2026-09-27T10:00:00Z ERROR Traceback (most recent call last):",
            "  File \"/srv/api.py\", line 41, in handle",
            "    raise ValueError(\"bad input\")", "ValueError: bad input",
            "2026-09-27T10:00:01Z ERROR Traceback (most recent call last):",
            "  File \"/srv/api.py\", line 52, in handle",
            "    raise ValueError(\"bad input\")", "ValueError: bad input",
        ],
        "java-stacktrace": [
            "2026-09-27T10:00:00Z ERROR Exception in thread \"main\" java.lang.IllegalStateException: failed",
            "    at com.example.Api.run(Api.java:41)", "    at com.example.Main.main(Main.java:12)",
            "2026-09-27T10:00:01Z ERROR Exception in thread \"main\" java.lang.IllegalStateException: failed",
            "    at com.example.Api.run(Api.java:52)", "    at com.example.Main.main(Main.java:12)",
        ],
        "high-cardinality-id": [f"2026-09-27T10:00:0{index}Z INFO tenant={value} job failed"
                                for index, value in enumerate(
                                    ("abc17", "hfg32", "zzk91", "qwe48", "abc17"))],
    }
    fixtures["mixed-production"] = [line for name in FAMILIES[:-1]
                                    for line in fixtures[name]]
    return fixtures




def _legacy_family_output(text: str, requested: str) -> str:
    family = _legacy_family(text, requested)
    if family == "mixed":
        return text
    title = {"event": "Event Logs", "json": "JSON Logs", "snapshot": "Snapshot Output",
             "describe": "Describe Output", "generic": "Generic Text"}[family]
    chunks, active = [], False
    for line in text.splitlines():
        if line in TITLES:
            if line == title:
                active = True
            elif active:
                active = False
            continue
        if active:
            chunks.append(line)
    return "\n".join(chunks) if chunks else text




def _copy_legacy_source(archive_path: Path, target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != "logtrim" or not member.isfile() or not member.name.endswith(".py"):
                continue
            if ".." in parts or PurePosixPath(member.name).is_absolute():
                raise ValueError(f"unsafe legacy archive member: {member.name}")
            destination = target.joinpath(*parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"cannot read legacy archive member: {member.name}")
            destination.write_bytes(source.read())
    if not (target / "logtrim" / "__main__.py").is_file():
        raise ValueError("legacy source archive does not contain logtrim/__main__.py")
    return target


def _run_legacy(root: Path, source: Path, output: Path) -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    result = subprocess.run(
        [sys.executable, "-m", "logtrim", "--input", str(source), "--output", str(output)],
        cwd=root, env=env, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"logtrim 0.1 failed for {source.name}: {result.stderr.strip()}")
    return output.read_text(encoding="utf-8")


def _legacy_items(text: str, family: str) -> int:
    if family in {"event", "json"}:
        return sum(bool(GROUP.match(line)) for line in text.splitlines())
    if family == "snapshot":
        return sum(line.lstrip().startswith("- ") for line in text.splitlines())
    if family == "describe":
        return sum(line.startswith("Name:") for line in text.splitlines())
    return sum(bool(line.strip()) for line in text.splitlines())


def _legacy_metrics(path: Path, text: str, family: str, full_output: str,
                    event_counts: dict[str, int]) -> dict:
    items = _legacy_items(text, family)
    if family == "mixed":
        items = _mixed_items(full_output)
    physical = len(path.read_text(encoding="utf-8").splitlines())
    logical = (event_counts["total"] if family == "mixed"
               else event_counts["by_family"].get(family, 0))
    coarse = items if family in {"event", "json"} else None
    ratio = 100 * (1 - items / logical) if logical else 0.0
    return {
        "tool_version": "0.1.0", "physical_lines": physical, "logical_events": logical,
        "logical_event_counts": event_counts["by_family"],
        "coarse_patterns": coarse, "final_patterns": None, "summary_items": items,
        "compression_ratio": ratio,
        "physical_compression_ratio": 100 * (1 - items / physical) if physical else 0.0,
        "legacy_output_bytes": len(full_output.encode("utf-8")),
        "bounded_state": {"in_memory_groups": True, "configured_memory_limit": None,
                          "state_model": "in-memory ordered groups"},
    }

def _current_metrics(path: Path) -> dict:
    from logtrim.grouping import Analyzer

    with Analyzer() as analyzer, path.open(encoding="utf-8") as source:
        analyzer.ingest(source)
        summary = analyzer.summary()
        rows = list(analyzer.rows())
        unique_variants = sum(row["variant_unique_count"] for row in rows)
        overflow = sum(row["variant_other_count"] for row in rows)
        return {
            "tool_version": summary["tool_version"], "physical_lines": summary["original_count"],
            "logical_events": summary["logical_events"], "coarse_patterns": summary["coarse_patterns"],
            "final_patterns": summary["trimmed_count"], "summary_items": len(rows),
            "compression_ratio": summary["compression_ratio"],
            "physical_compression_ratio": summary["physical_compression_ratio"],
            "unique_semantic_variants": unique_variants, "variant_overflow": overflow,
            "processing_time_ns": summary["elapsed_ns"],
            "bounded_state": {
                "cache_peak": analyzer.stats["cache_peak"],
                "cache_limit": analyzer.config.cache_size,
                "adaptive_cache_peak": analyzer.stats["adaptive_cache_peak"],
                "adaptive_cache_limit": analyzer.config.cache_size,
                "candidate_comparisons": analyzer.stats["comparisons"],
                "candidate_limit_per_lookup": analyzer.config.max_candidates,
                "candidate_comparison_budget": analyzer.stats["exact_patterns"] * analyzer.config.max_candidates,
                "sqlite_state_bytes": analyzer.db.execute(
                    "PRAGMA page_count").fetchone()[0] * analyzer.db.execute(
                    "PRAGMA page_size").fetchone()[0],
                "adaptive_signature_rows": analyzer.db.execute("SELECT COUNT(*) FROM adaptive_values").fetchone()[0],
                "adaptive_promoted_positions": analyzer.stats["adaptive.promoted_positions"],
                "variant_rows": analyzer.db.execute("SELECT COUNT(*) FROM variants").fetchone()[0],
            },
            "summary": summary,
        }


def _v3_version(pyz: Path) -> str:
    result = subprocess.run([sys.executable, str(pyz), "--version"],
                            text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"existing v3 version command failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _v3_metrics(pyz: Path, path: Path, output: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(pyz), "analyze", str(path), str(output), "--format", "json"],
        text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"existing v3 failed for {path.name}: {result.stderr.strip()}")
    report = json.loads(output.read_text(encoding="utf-8"))
    summary = report["summary"]
    return {
        "tool_version": summary["tool_version"],
        "physical_lines": summary["original_count"],
        "logical_events": summary["logical_events"],
        "coarse_patterns": summary.get("exact_patterns"),
        "final_patterns": summary["trimmed_count"],
        "summary_items": len(report["patterns"]),
        "compression_ratio": summary["compression_ratio"],
        "physical_compression_ratio": summary.get("physical_compression_ratio"),
        "processing_time_ns": summary["elapsed_ns"],
        "legacy_output_bytes": output.stat().st_size,
        "summary": summary,
    }


def _legacy_logical_events(root: Path, input_path: Path) -> dict[str, int]:
    """Instrument the 0.1 pipeline's own family processors without changing output."""
    probe = r'''
import json, sys
from collections import Counter
import logtrim.pipeline as pipeline
from logtrim.eventize import eventize_lines

counts = Counter()
original = pipeline._render_section
def counted(family, lines):
    if family in {"event", "json"}:
        amount = sum(1 for _ in eventize_lines(lines))
    elif family == "snapshot":
        nonempty = [line for line in lines if line.strip()]
        amount = max(0, len(nonempty) - 1)
    elif family == "describe":
        amount = sum(line.startswith("Name:") for line in lines)
    else:
        amount = sum(bool(line.strip()) for line in lines)
    counts[family] += amount
    return original(family, lines)

pipeline._render_section = counted
with open(sys.argv[1], encoding="utf-8") as source:
    for _ in pipeline.process_stream(source):
        pass
print(json.dumps({"by_family": dict(counts), "total": sum(counts.values())}))
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    result = subprocess.run([sys.executable, "-c", probe, str(input_path)],
                            cwd=root, env=env, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"logtrim 0.1 event-count probe failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _legacy_family(text: str, requested: str) -> str:
    if requested == "mixed-production":
        return "mixed"
    return {
        "generic-text": "generic", "json": "json", "logfmt": "event",
        "http": "event", "kubernetes-event": "event",
        "kubectl-pods": "snapshot", "kubectl-nodes": "snapshot",
        "kubectl-describe": "describe", "python-traceback": "event",
        "java-stacktrace": "event", "high-cardinality-id": "event",
    }[requested]


def _mixed_items(text: str) -> int:
    count, section = 0, "generic"
    for line in text.splitlines():
        if line in TITLES:
            section = TITLES[line]
        elif section in {"event", "json"}:
            count += bool(GROUP.match(line))
        elif section == "snapshot":
            count += line.lstrip().startswith("- ")
        elif section == "describe":
            count += line.startswith("Name:")
        elif section == "generic":
            count += bool(line.strip())
    return count


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-source", required=True, type=Path,
                        help="logtrim 0.1 source tar.gz used as the reference")
    parser.add_argument("--v3-pyz", type=Path,
                        default=(ROOT.parent / "logtrim" / "logtrim.pyz"
                                 if (ROOT.parent / "logtrim" / "logtrim.pyz").is_file() else None),
                        help="optional existing v3 standalone archive for a third comparison")
    parser.add_argument("--corpus-dir", type=Path,
                        help="directory containing <family>.log overrides; mixed accepts k8s_realistic.log")
    parser.add_argument("--output", type=Path, help="write JSON results here; stdout by default")
    args = parser.parse_args(argv)
    if not args.legacy_source.is_file():
        parser.error(f"legacy source archive not found: {args.legacy_source}")
    if args.corpus_dir is not None and not args.corpus_dir.is_dir():
        parser.error(f"corpus directory not found: {args.corpus_dir}")

    if args.v3_pyz is not None and not args.v3_pyz.is_file():
        parser.error(f"existing v3 archive not found: {args.v3_pyz}")
    v3_version = _v3_version(args.v3_pyz) if args.v3_pyz else None
    results = {"benchmark_schema": "1.0", "baseline": "logtrim 0.1.0",
               "existing_v3": v3_version, "current": "logtrim 0.4", "families": {}}
    fixtures = _fixtures()
    with tempfile.TemporaryDirectory(prefix="logtrim-differential-") as tmp:
        work = Path(tmp)
        legacy_root = _copy_legacy_source(args.legacy_source, work / "legacy")
        inputs = work / "inputs"
        inputs.mkdir()
        for name in FAMILIES:
            supplied = next((args.corpus_dir / f"{name}{suffix}"
                             for suffix in (".log", ".txt")
                             if args.corpus_dir and (args.corpus_dir / f"{name}{suffix}").is_file()), None)
            if supplied is None and name == "mixed-production" and args.corpus_dir:
                realistic = args.corpus_dir / "k8s_realistic.log"
                supplied = realistic if realistic.is_file() else None
            source_label = f"supplied-corpus:{supplied.name}" if supplied else "synthetic-fixture"
            input_path = supplied or inputs / f"{name}.log"
            if supplied is None:
                input_path.write_text("\n".join(fixtures[name]) + "\n", encoding="utf-8")
            old_output = work / f"{name}.out"
            started = time.perf_counter_ns()
            old_text = _run_legacy(legacy_root, input_path, old_output)
            old_elapsed = time.perf_counter_ns() - started
            current = _current_metrics(input_path)
            legacy_events = _legacy_logical_events(legacy_root, input_path)
            family = _legacy_family(old_text, name)
            legacy_text = _legacy_family_output(old_text, name)
            legacy = _legacy_metrics(input_path, legacy_text, family, old_text, legacy_events)
            legacy["processing_time_ns"] = old_elapsed
            baseline_items = legacy["summary_items"]
            comparable = baseline_items is not None
            v3 = (_v3_metrics(args.v3_pyz, input_path, work / f"{name}.v3.json")
                  if args.v3_pyz else None)
            v3_comparison = None
            if v3 is not None:
                delta = current["final_patterns"] - v3["final_patterns"]
                v3_comparison = {
                    "basis": "0.4 final patterns minus existing v3 final patterns",
                    "final_patterns_delta": delta,
                    "status": "FEWER_OR_EQUAL" if delta <= 0 else "MORE_GROUPS",
                }
            results["families"][name] = {
                "corpus_source": source_label, "physical_input_lines": current["physical_lines"],
                "logtrim_0_1": legacy, "logtrim_v3": v3, "logtrim_0_4": current,
                "comparison": {
                    "basis": "0.1 rendered summary items vs 0.4 final patterns",
                    "status": ("PASS" if comparable and current["final_patterns"] <= baseline_items
                               else "PARITY_REGRESSION" if comparable else "NOT_COMPARABLE"),
                    "summary_items_delta": (current["final_patterns"] - baseline_items
                                            if comparable else None),
                    "existing_v3": v3_comparison,
                },
            }

    encoded = json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return int(any(row["comparison"]["status"] == "PARITY_REGRESSION"
                   for row in results["families"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
