"""Run with python -m unittest discover -s tests -v."""
from __future__ import annotations

import bz2
import gzip
import io
import json
import lzma
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

from logtrim.cli import load_rules, main
from logtrim.grouping import Analyzer, group_logs
from logtrim.io_utils import assemble, ensure_distinct, iter_lines, write_output
from logtrim.models import Config, ResourceLimit
from logtrim.patterns import Normalizer, extract_pattern, parse_timestamp
from logtrim.report import diff_rows, render
from logtrim.similarity import compute_similarity

ROOT = Path(__file__).resolve().parents[1]


class NormalizationTests(unittest.TestCase):
    def test_java_and_long_exception_names(self):
        line = ("java.lang.NullPointerException at "
                "com.example.Service.run(Service.java:42) ConnectionRefusedError")
        out = extract_pattern(line)
        self.assertIn("java.lang.NullPointerException", out)
        self.assertIn("com.example.Service.run", out)
        self.assertIn("ConnectionRefusedError", out)
        self.assertIn("Service.java:<LINE>", out)

    def test_cpp_and_invalid_ip(self):
        line = "foo::bar C++Namespace::method :: 999.999.999.999"
        self.assertEqual(extract_pattern(line), line)

    def test_ipv4_ipv6_and_mac(self):
        for value, expected in [("10.0.0.1", "<IPV4>"), ("::1", "<IPV6>"),
                                ("2001:db8::1", "<IPV6>"), ("::ffff:192.0.2.1", "<IPV6>"),
                                ("aa:bb:cc:dd:ee:ff", "<MAC>")]:
            with self.subTest(value=value):
                self.assertEqual(extract_pattern("peer " + value), "peer " + expected)
        self.assertIn("[<IPV6>]:443", extract_pattern("peer [::1]:443"))

    def test_json_path_does_not_consume_fields(self):
        obj = {"level": "error", "path": "/var/lib/postgresql/data", "status": 507}
        out = json.loads(extract_pattern(json.dumps(obj)))
        self.assertEqual(out, {"level": "error", "path": "<PATH>", "status": 507})

    def test_paths_versions_domains_and_codes(self):
        self.assertEqual(extract_pattern("nginx/1.25.4 ORA-00600 HTTP/1.1 404"),
                         "nginx/1.25.4 ORA-00600 HTTP/1.1 404")
        self.assertEqual(extract_pattern("com.example.Worker.run"), "com.example.Worker.run")
        self.assertIn("<PATH>", extract_pattern(r"file C:\\logs\\app.txt"))

    def test_idempotence(self):
        inputs = ["peer ::1 after 12ms", "error ORA-00600 pid=12", "https://example.com/a",
                  '{"path":"/a/b","request_id":"abc","latency_ms":21}',
                  'level=error msg="failed after 2ms" retries=3']
        for line in inputs:
            with self.subTest(line=line):
                first = extract_pattern(line)
                self.assertEqual(extract_pattern(first), first)

    def test_json_canonical_order_and_types(self):
        self.assertEqual(extract_pattern('{"b":2,"a":1}'),
                         extract_pattern('{"a":1,"b":2}'))
        self.assertNotEqual(extract_pattern('{"status":500}'),
                            extract_pattern('{"status":"500"}'))
        self.assertTrue(json.loads(extract_pattern('{"ready":true}'))["ready"])

    def test_json_duplicate_and_malformed_fallback(self):
        n = Normalizer()
        for line in ['{"a":1,"a":2}', '{"message":', '{"x":NaN}', '{"x":1e999}']:
            self.assertEqual(n.normalize(line).parser, "text")
        self.assertEqual(n.stats["parser.json_failure"], 4)

    def test_logfmt(self):
        out = Normalizer().normalize('level=error msg="connection refused" retries=3')
        self.assertEqual(out.parser, "logfmt")
        self.assertEqual(json.loads(out.pattern)["retries"], "<RETRY_COUNT>")
        self.assertEqual(Normalizer().normalize('msg="unclosed').parser, "text")
        self.assertEqual(Normalizer().normalize('a=1 a=2').parser, "text")

    def test_redaction(self):
        out = extract_pattern('{"password":"s3cret","access_token":"abcdef","token_count":3}')
        self.assertNotIn("s3cret", out)
        self.assertNotIn("abcdef", out)
        self.assertIn('"token_count":3', out)
        self.assertNotIn("s3cret", extract_pattern('failed password="s3cret" now'))

    def test_captures_and_preserved_fields(self):
        n = Normalizer().normalize('{"service":"postgres","error":{"type":"TimeoutError"},"latency_ms":812}')
        self.assertIn('service="postgres"', n.anchors)
        self.assertIn(("latency_ms", 812.0), n.captures)
        self.assertIn("TimeoutError", n.pattern)

    def test_timestamp_offsets_and_unknown_year(self):
        stamp = parse_timestamp("2026-09-18T10:20:30+09:00")
        self.assertEqual(stamp.hour, 1)
        self.assertEqual(stamp.tzinfo, timezone.utc)
        self.assertIsNone(parse_timestamp("Apr 5 10:30:45"))
        self.assertEqual(parse_timestamp("Apr 5 10:30:45", 2025).year, 2025)
        self.assertIsNone(parse_timestamp("Feb 30 10:30:45", 2025))
        self.assertIsNone(parse_timestamp("2026-99-99T10:20:30Z"))
        self.assertEqual(parse_timestamp("2026-09-18T10:20:30", offset_minutes=540).hour, 1)

    def test_custom_rules(self):
        n = Normalizer(rules=[{"id": "order", "pattern": r"\bord_[A-Z0-9]{6}\b",
                               "placeholder": "ORDER_ID"}])
        self.assertEqual(n.normalize("order ord_ABC123 failed").pattern,
                         "order <ORDER_ID> failed")
        for rule in [{"id": "empty", "pattern": ".*"}, {"id": "bad", "pattern": "["},
                     {"id": "bad", "pattern": "x", "placeholder": "BAD>CODE"}]:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                Normalizer(rules=[rule])

    def test_event_and_depth_limits(self):
        with self.assertRaises(ResourceLimit):
            Normalizer(Config(max_event_bytes=8)).normalize("a" * 9)
        with self.assertRaises(ResourceLimit):
            Normalizer(Config(max_tokens=2)).normalize("a b c")
        with self.assertRaises(ResourceLimit):
            Normalizer().normalize('{"x":' * 34 + "0" + "}" * 34)

    def test_routes_remain_distinct(self):
        self.assertEqual(extract_pattern("GET /health HTTP/1.1 200"), "GET /health HTTP/1.1 200")
        self.assertNotEqual(extract_pattern("GET /health 200"), extract_pattern("GET /payments 200"))

    def test_compact_timezone(self):
        self.assertEqual(parse_timestamp("2026-09-18T10:20:30+0900").hour, 1)

    def test_klog(self):
        n = Normalizer(Config(syslog_year=2025))
        event = n.normalize("E0918 10:20:30.123456 1234 server.go:42] connection refused")
        self.assertEqual(event.parser, "klog")
        self.assertEqual(event.timestamp.year, 2025)
        self.assertEqual(json.loads(event.pattern)["line"], "<LINE>")
        self.assertIn('level="ERROR"', event.anchors)


class GroupingTests(unittest.TestCase):
    def test_count_time_and_template(self):
        lines = ["peer 10.0.0.1", "2026-09-18T12:00:00+09:00 peer 10.0.0.1",
                 "2026-09-18T10:00:00+09:00 peer 2001:db8::1", "\n"]
        with Analyzer() as a:
            a.ingest(iter(lines))
            rows = list(a.rows())
            self.assertEqual(sum(r["count"] for r in rows), 3)
            merged = next(r for r in rows if r["count"] == 2)
            self.assertEqual(merged["pattern"], "<TIMESTAMP> peer <IP>")
            self.assertIn("01:00:00", merged["first_seen"])
            self.assertIn("03:00:00", merged["last_seen"])
            self.assertIsNone(merged["sample"])
            self.assertEqual(a.summary()["original_count"], 4)
            self.assertEqual(a.summary()["logical_events"], 3)

    def test_no_static_semantic_overmerge(self):
        lines = ["HTTP 404 failed", "HTTP 500 failed", "connection refused", "connection timeout",
                 "ORA-00600 failed", "ORA-00001 failed", "TimeoutError", "ConnectionRefusedError"]
        self.assertEqual(len(list(group_logs(lines))), len(lines))

    def test_leader_blocks_transitive_chain(self):
        a, b, c = "x <IPV4> <UUID>", "x <IPV6> <UUID>", "x <IPV6> <HEX>"
        self.assertGreaterEqual(compute_similarity(a, b), 0.96)
        self.assertGreaterEqual(compute_similarity(b, c), 0.96)
        self.assertLess(compute_similarity(a, c), 0.96)
        with Analyzer(Config(threshold=0.96)) as model:
            model.ingest([a, b, c])
            self.assertEqual([r["count"] for r in model.rows()], [2, 1])

    def test_ambiguity_margin(self):
        with Analyzer(Config(threshold=0.95)) as a:
            a.ingest(["x <IPV4> <UUID>", "x <IPV6> <HEX>", "x <IPV4> <HEX>"])
            self.assertEqual(a.stats["clusters"], 3)
            self.assertEqual(a.stats["ambiguous_events"], 1)

    def test_bounded_cache_candidates_and_single_pass(self):
        class Once:
            def __init__(self):
                self.used = False
            def __iter__(self):
                if self.used:
                    raise AssertionError("input iterated twice")
                self.used = True
                yield from (f"INFO event unique{i}" for i in range(300))
        with Analyzer(Config(cache_size=8, max_candidates=7)) as a:
            a.ingest(Once())
            self.assertLessEqual(len(a.cache), 8)
            self.assertLessEqual(a.stats["comparisons"], 300 * 7)
            self.assertEqual(a.stats["clusters"], 300)
            self.assertEqual(a.stats["exact_patterns"], 300)
            self.assertEqual(sum(r["count"] for r in a.rows()), 300)

    def test_cluster_limit_and_cleanup(self):
        with Analyzer(Config(max_clusters=1)) as a:
            directory = a._tmp.name
            with self.assertRaises(ResourceLimit):
                a.ingest(["one", "two"])
        self.assertFalse(Path(directory).exists())

    def test_frozen_baseline_diff(self):
        with Analyzer() as a:
            a.ingest(["peer 10.0.0.1", "old failure"], "baseline")
            a.ingest(["peer 2001:db8::1", "new failure"], "current")
            rows = list(diff_rows(a))
            self.assertEqual({r["change"] for r in rows}, {"NEW", "RESOLVED", "STABLE"})
            matched = next(r for r in rows if r["baseline"] and r["current"])
            self.assertIn("<IPV4>", matched["pattern"])
            with self.assertRaises(ValueError):
                a.ingest(["late baseline"], "baseline")

    def test_numeric_slot_statistics(self):
        with Analyzer() as a:
            a.ingest(['{"latency_ms":10}', '{"latency_ms":30}'])
            row = next(a.rows())
            self.assertEqual(row["slots"]["latency_ms"],
                             {"count": 2, "min": 10.0, "max": 30.0, "mean": 20.0})

    def test_multiline_python_and_java(self):
        lines = ["Traceback (most recent call last):\n", '  File "a.py", line 2\n',
                 "    fail()\n", "ValueError: bad\n", "next event\n",
                 "java.lang.RuntimeException: failed\n", "    at app.Run(Run.java:8)\n",
                 "Caused by: java.io.IOException: broken\n"]
        with Analyzer() as a:
            a.ingest(lines)
            self.assertEqual(a.stats["events"], 3)
            self.assertEqual(a.stats["event_physical_lines"], 8)

    def test_empty_and_unknown_times(self):
        with Analyzer() as a:
            a.ingest(["\n", " \n"])
            self.assertEqual(a.summary()["compression_ratio"], 0.0)
            self.assertEqual(list(a.rows()), [])
        self.assertIsNone(next(group_logs(["no timestamp"])).first_seen)

    def test_generic_python_exception_and_next_event(self):
        with Analyzer() as a:
            a.ingest(["Traceback (most recent call last):", '  File "a.py", line 2',
                      "Exception: failed", "TimeoutError: unrelated"])
            self.assertEqual(a.stats["events"], 2)

    def test_independent_sources_flush_multiline(self):
        with Analyzer() as a:
            a.ingest(["first"])
            a.ingest(["  second source"])
            self.assertEqual(a.stats["events"], 2)

    def test_repeatability(self):
        lines = ["x <IPV4>", "x <IPV6>", "other"]
        with Analyzer() as a, Analyzer() as b:
            a.ingest(lines)
            b.ingest(lines)
            self.assertEqual(list(a.rows()), list(b.rows()))


class IOAndCLITests(unittest.TestCase):
    def test_compressed_magic_and_decoding(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "input.bin"
            for compress in (gzip.compress, bz2.compress, lzma.compress):
                path.write_bytes(compress(b"one\ntwo\n"))
                self.assertEqual(list(iter_lines(str(path))), ["one\n", "two\n"])
            path.write_bytes(b"bad\xff\n")
            with self.assertRaises(UnicodeDecodeError):
                list(iter_lines(str(path)))
            stats = Counter()
            self.assertIn("\ufffd", next(iter_lines(str(path), stats=stats, errors="replace")))
            self.assertEqual(stats["decode_error_lines"], 1)

    def test_input_limits(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "input"
            path.write_text("abc\ndef\n")
            with self.assertRaises(ResourceLimit):
                list(iter_lines(str(path), Config(max_input_bytes=5)))
            with self.assertRaises(ResourceLimit):
                list(iter_lines(str(path), Config(max_event_bytes=2)))
        with self.assertRaises(ResourceLimit):
            list(assemble(["x", "  y", "  z"], Config(max_event_lines=2), Counter()))

    def test_atomic_output_and_same_path(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out"
            path.write_text("old")
            def broken():
                yield "new"
                raise OSError("test failure")
            with self.assertRaises(OSError):
                write_output(broken(), str(path))
            self.assertEqual(path.read_text(), "old")
            with self.assertRaises(ValueError):
                ensure_distinct([str(path)], str(path))
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["out"])

    def test_all_report_formats_and_escaping(self):
        with Analyzer() as a:
            a.ingest(["<script>alert(1)</script>\x1b[31m | bad"])
            for fmt in ["text", "json", "jsonl", "markdown", "html"]:
                out = "".join(render(a.summary(), a.rows(), fmt))
                self.assertTrue(out)
                if fmt == "json":
                    self.assertEqual(json.loads(out)["summary"]["logical_events"], 1)
                if fmt == "jsonl":
                    self.assertEqual(len([json.loads(x) for x in out.splitlines()]), 2)
                if fmt == "html":
                    self.assertNotIn("<script>alert", out)
                    self.assertIn("Content-Security-Policy", out)
                if fmt == "text":
                    self.assertNotIn("\x1b", out)
        with self.assertRaises(ValueError):
            list(render({}, [], "invalid"))

    def test_config_validation(self):
        for kwargs in [{"threshold": float("nan")}, {"threshold": 0}, {"max_candidates": 0},
                       {"depth": 17}, {"cache_size": 0}, {"max_clusters": -1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Config(**kwargs)

    def test_cli_pipe_and_legacy_entrypoint(self):
        for command in [[sys.executable, "-m", "logtrim"], [sys.executable, "trim.py"]]:
            result = subprocess.run(command + ["-", "-", "--format", "json"],
                                    input="same\nsame\n", text=True, capture_output=True, cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["patterns"][0]["count"], 2)
            self.assertEqual(data["summary"]["exact_patterns"], 1)

    def test_cli_errors_and_rules(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rules.json"
            path.write_text('{"version":1,"rules":[]}', encoding="utf-8")
            self.assertEqual(load_rules(path), [])
            path.write_text('{"version":2,"rules":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_rules(path)
            with patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(main(["--threshold", "nan"]), 2)
                self.assertEqual(main([str(Path(d) / "missing")]), 1)
            with patch("sys.stdin", new=io.StringIO("abcde\n")), patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(main(["--max-event-bytes", "3"]), 3)

    def test_cli_diff_and_top(self):
        with tempfile.TemporaryDirectory() as d:
            before, after, output = (Path(d) / name for name in ("before", "after", "report"))
            before.write_text("old failure\n")
            after.write_text("new failure\nnew failure\n")
            self.assertEqual(main(["diff", str(before), str(after), "-o", str(output),
                                   "--format", "json", "--changes-only", "--top", "1"]), 0)
            result = json.loads(output.read_text())
            self.assertEqual(len(result["patterns"]), 1)
            self.assertEqual(result["patterns"][0]["change"], "NEW")

    def test_cli_explain(self):
        with patch("sys.stdout", new=io.StringIO()) as output:
            self.assertEqual(main(["explain", "--line", "ORA-00600 peer ::1"]), 0)
            self.assertIn("<IPV6>", json.loads(output.getvalue())["pattern"])

    def test_failure_does_not_replace_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            source, target = Path(d) / "in", Path(d) / "out"
            source.write_text("a line longer than eight bytes\n")
            target.write_text("previous report")
            with patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(main([str(source), str(target), "--max-event-bytes", "8"]), 3)
            self.assertEqual(target.read_text(), "previous report")


if __name__ == "__main__":
    unittest.main()