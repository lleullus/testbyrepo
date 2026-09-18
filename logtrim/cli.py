"""Command-line entry points."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sqlite3
import sys
from dataclasses import asdict

from . import __version__
from .grouping import Analyzer
from .io_utils import ensure_distinct, iter_lines, write_output
from .models import Config, ResourceLimit
from .patterns import Normalizer
from .report import diff_rows, render


def load_rules(path):
    if not path:
        return []
    with open(path, "rb") as source:
        content = source.read(65537)
    if len(content) > 65536:
        raise ValueError("rules file exceeds 64 KiB")
    data = json.loads(content)
    if not isinstance(data, dict) or set(data) != {"version", "rules"} or data["version"] != 1:
        raise ValueError("rules file must contain version=1 and rules")
    if not isinstance(data["rules"], list):
        raise ValueError("rules must be a list")
    return data["rules"]


def parse_args(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in {"analyze", "diff", "explain", "-h", "--help", "--version"}:
        argv.insert(0, "analyze")
    parser = argparse.ArgumentParser(prog="logtrim")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--threshold", type=float, default=0.85)
    common.add_argument("--min-margin", type=float, default=0.02)
    common.add_argument("--max-candidates", type=int, default=64)
    common.add_argument("--max-event-bytes", type=int, default=65536)
    common.add_argument("--max-event-lines", type=int, default=256)
    common.add_argument("--max-tokens", type=int, default=2048)
    common.add_argument("--max-clusters", type=int, default=0)
    common.add_argument("--max-input-bytes", type=int, default=0)
    common.add_argument("--cache-size", type=int, default=256)
    common.add_argument("--sqlite-cache-kib", type=int, default=8192)
    common.add_argument("--depth", type=int, default=4)
    common.add_argument("--multiline", choices=["auto", "off"], default="auto")
    common.add_argument("--sample-mode", choices=["none", "redacted", "raw"], default="none")
    common.add_argument("--syslog-year", type=int)
    common.add_argument("--timezone-minutes", type=int, default=0)
    common.add_argument("--rules")
    common.add_argument("--work-dir", help="directory for private temporary SQLite state")
    common.add_argument("--encoding", default="utf-8")
    common.add_argument("--decode-errors", choices=["strict", "replace"], default="strict")
    common.add_argument("--format", choices=["text", "json", "jsonl", "markdown", "html"], default="text")
    common.add_argument("--top", type=int, default=0)
    common.add_argument("--debug", action="store_true")
    analyze = sub.add_parser("analyze", parents=[common])
    analyze.add_argument("input", nargs="?", default="-")
    analyze.add_argument("output", nargs="?", default="-")
    analyze.add_argument("--rare-max-count", type=int, default=0)
    diff = sub.add_parser("diff", parents=[common])
    diff.add_argument("baseline")
    diff.add_argument("current")
    diff.add_argument("-o", "--output", default="-")
    diff.add_argument("--min-ratio", type=float, default=2.0)
    diff.add_argument("--changes-only", action="store_true")
    explain = sub.add_parser("explain", parents=[common])
    explain.add_argument("--line", required=True)
    return parser.parse_args(argv)


def execute(args):
    names = ("threshold", "min_margin", "max_candidates", "max_event_bytes", "max_event_lines",
             "max_tokens", "max_clusters", "max_input_bytes", "cache_size", "sqlite_cache_kib",
             "depth", "sample_mode", "syslog_year", "timezone_minutes")
    config = Config(**{key: getattr(args, key) for key in names},
                    multiline=args.multiline == "auto")
    rules = load_rules(args.rules)
    if args.top < 0 or getattr(args, "rare_max_count", 0) < 0:
        raise ValueError("report limits must be nonnegative")
    if args.command == "explain":
        normalizer = Normalizer(config, rules)
        event = asdict(normalizer.normalize(args.line))
        if event["timestamp"] is not None:
            event["timestamp"] = event["timestamp"].isoformat()
        event["diagnostics"] = dict(normalizer.stats)
        write_output([json.dumps(event, ensure_ascii=True, allow_nan=False) + "\n"], "-")
        return 0
    inputs = [args.input] if args.command == "analyze" else [args.baseline, args.current]
    if inputs.count("-") > 1:
        raise ValueError("stdin can be used for only one diff input")
    if args.command == "diff" and (not math.isfinite(args.min_ratio) or args.min_ratio <= 1):
        raise ValueError("min_ratio must be finite and greater than one")
    ensure_distinct(inputs, args.output)
    with Analyzer(config, rules, args.work_dir) as analyzer:
        phases = ["main"] if args.command == "analyze" else ["baseline", "current"]
        for path, phase in zip(inputs, phases):
            lines = iter_lines(path, config, analyzer.stats, args.encoding, args.decode_errors)
            try:
                analyzer.ingest(lines, phase)
            finally:
                lines.close()
        rows = analyzer.rows() if args.command == "analyze" else diff_rows(analyzer, args.min_ratio)
        if args.command == "analyze" and args.rare_max_count:
            rows = (row for row in rows if row["count"] <= args.rare_max_count)
        if args.command == "diff" and args.changes_only:
            rows = (row for row in rows if row["change"] != "STABLE")
        if args.top:
            rows = itertools.islice(rows, args.top)
        summary = analyzer.summary()
        summary["report_filter"] = {"top": args.top,
                                    "rare_max_count": getattr(args, "rare_max_count", 0),
                                    "changes_only": getattr(args, "changes_only", False)}
        write_output(render(summary, rows, args.format), args.output)
    return 0


def run(input_path: str, output_path: str = "-", threshold: float = 0.85,
        fmt: str = "text") -> int:
    return execute(parse_args(["analyze", input_path, output_path,
                               "--threshold", str(threshold), "--format", fmt]))


def main(argv=None):
    args = parse_args(argv)
    try:
        return execute(args)
    except KeyboardInterrupt:
        print("logtrim: interrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        # Prevent a second BrokenPipeError during interpreter shutdown.
        try:
            with open(os.devnull, "w") as sink:
                os.dup2(sink.fileno(), sys.stdout.fileno())
        except (OSError, ValueError):
            pass
        return 0
    except (ResourceLimit, ValueError, OSError, UnicodeError, sqlite3.Error, LookupError) as exc:
        if args.debug:
            raise
        code = (3 if isinstance(exc, ResourceLimit) else 1 if isinstance(exc, UnicodeError)
                else 2 if isinstance(exc, ValueError) else 1)
        print(f"logtrim: {type(exc).__name__}: {exc}", file=sys.stderr)
        return code