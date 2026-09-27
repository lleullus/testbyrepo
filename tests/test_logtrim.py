"""Run with python -m unittest discover -s tests -v."""
from __future__ import annotations

import bz2
import gzip
import io
import json
import lzma
import tarfile
import zipfile
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
import build_dist


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
        for value, semantic in [("10.0.0.1", "<IPV4>"), ("::1", "<IPV6>"),
                                ("2001:db8::1", "<IPV6>"), ("::ffff:192.0.2.1", "<IPV6>")]:
            with self.subTest(value=value):
                event = Normalizer().normalize("peer " + value)
                self.assertEqual(event.pattern, "peer <IP>")
                self.assertEqual(event.semantic_pattern, "peer " + semantic)
        self.assertEqual(extract_pattern("peer aa:bb:cc:dd:ee:ff"), "peer <MAC>")
        event = Normalizer().normalize("peer [::1]:443")
        self.assertIn("[<IP>]:<PORT>", event.pattern)
        self.assertIn("[<IPV6>]:443", event.semantic_pattern)

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

    def test_coarse_route_keeps_semantic_variant(self):
        raw = "GET /users/123/orders/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1 200"
        event = Normalizer().normalize(raw)
        self.assertIn("/users/<NUM>/orders/<UUID>", event.pattern)
        self.assertIn("/users/123/orders/550e8400-e29b-41d4-a716-446655440000",
                      event.semantic_pattern)

    def test_legacy_entropy_classes_feed_coarse_identity(self):
        event = Normalizer().normalize(
            "api-7c9d8f6b7c-abc12 tid=4455 job 123456 hash abcdef12 app[991]"
        )
        self.assertIn("api-<POD>", event.pattern)
        self.assertIn("tid=<TID>", event.pattern)
        self.assertIn("<NUM>", event.pattern)
        self.assertIn("<HASH>", event.pattern)
        self.assertIn("<PID>", event.pattern)
        self.assertNotIn("app[", event.pattern)
        self.assertNotEqual(event.pattern, event.semantic_pattern)

    def test_structured_coarse_pattern_stays_valid_json(self):
        event = Normalizer().normalize('{"order":123456,"status":500}')
        coarse = json.loads(event.pattern)
        semantic = json.loads(event.semantic_pattern)
        self.assertEqual(coarse["order"], "<NUM>")
        self.assertEqual(coarse["status"], 500)
        self.assertEqual(semantic["order"], 123456)

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

    def test_coarse_identity_groups_dynamic_routes_without_splitting(self):
        lines = [
            "GET /users/123 HTTP/1.1 200",
            "GET /users/456 HTTP/1.1 200",
        ]
        with Analyzer() as a:
            a.ingest(lines)
            rows = list(a.rows())
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["count"], 2)
            self.assertIn("/users/<NUM>", row["pattern"])
            self.assertEqual(len(row["variants"]), 2)
            self.assertEqual(sum(v["count"] for v in row["variants"].values()), 2)

    def test_legacy_compression_floor_reference_cases(self):
        lines = [
            "api-7c9d8f6b7c-abc12 app[101]: peer 10.0.0.1:8080 job 123456",
            "api-7c9d8f6b7c-def34 db[202]: peer 10.0.0.2:9090 job 654321",
        ]
        with Analyzer() as a:
            a.ingest(lines)
            rows = list(a.rows())
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["count"], 2)
            self.assertEqual(len(rows[0]["variants"]), 2)

    def test_legacy_json_unstable_fields_do_not_split_coarse_groups(self):
        with Analyzer() as a:
            a.ingest([
                '{"level":"info","message":"ok","request_id":"abc","ts":"2026-01-01T00:00:00Z"}',
                '{"level":"info","message":"ok"}',
            ])
            rows = list(a.rows())
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["count"], 2)
            self.assertEqual(len(rows[0]["variants"]), 1)

    def test_compression_stage_accounting(self):
        with Analyzer() as a:
            a.ingest([
                "GET /users/123 HTTP/1.1 200",
                "GET /users/456 HTTP/1.1 200",
                "other event",
            ])
            summary = a.summary()
            self.assertEqual(summary["compression_stages"], {
                "physical_lines": 3,
                "logical_events": 3,
                "coarse_patterns": 2,
                "final_patterns": 2,
            })
            self.assertAlmostEqual(summary["coarse_compression_ratio"], 100 / 3)
            self.assertAlmostEqual(summary["physical_compression_ratio"], 100 / 3)

    def test_process_names_do_not_break_coarse_pid_floor(self):
        with Analyzer() as a:
            a.ingest([
                "app[101]: worker failed",
                "db[202]: worker failed",
            ])
            row = next(a.rows())
            self.assertEqual(row["count"], 2)
            self.assertEqual(len(row["variants"]), 2)
            self.assertIn("<PID>: worker failed", row["pattern"])

    def test_semantic_variants_are_bounded(self):
        with Analyzer(Config(max_variants=1)) as a:
            a.ingest([
                "GET /users/123 HTTP/1.1 200",
                "GET /users/456 HTTP/1.1 200",
            ])
            row = next(a.rows())
            self.assertEqual(len(row["variants"]), 1)
            self.assertEqual(row["variant_other_count"], 1)
            self.assertEqual(row["count"], 2)

    def test_snapshot_pods_group_by_workload_and_preserve_states(self):
        lines = [
            "NAME READY STATUS RESTARTS AGE\n",
            "api-7c9d8f6b7c-abc12  1/1  Running  0  2d\n",
            "api-7c9d8f6b7c-def34  0/1  CrashLoopBackOff  4  2d\n",
            "api-7c9d8f6b7c-ghi56  1/1  Running  0  3d\n",
        ]
        with Analyzer() as analyzer:
            analyzer.ingest(lines)
            rows = list(analyzer.rows())
            self.assertEqual(analyzer.summary()["compression_stages"], {
                "physical_lines": 4, "logical_events": 3,
                "coarse_patterns": 1, "final_patterns": 1,
            })
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["count"], 3)
            self.assertIn('workload="api"', row["pattern"])
            self.assertEqual(row["family_states"], {
                "CrashLoopBackOff": {"count": 1, "baseline": 0, "current": 0},
                "Running": {"count": 2, "baseline": 0, "current": 0},
            })
            self.assertEqual(sorted(stats["count"] for stats in row["variants"].values()), [1, 1, 1])
            self.assertEqual(sum(stats["count"] for stats in row["variants"].values()), 3)
            report = "".join(render(analyzer.summary(), rows, "text"))
            self.assertIn("states: CrashLoopBackOff=1, Running=2", report)
            self.assertTrue(any('status="CrashLoopBackOff"' in variant
                                for variant in row["variants"]))

    def test_snapshot_nodes_group_by_state_and_other_tables_are_detected(self):
        with Analyzer() as analyzer:
            analyzer.ingest([
                "NAME STATUS ROLES AGE VERSION\n",
                "node-01 Ready control-plane 3d v1.32.1\n",
                "node-02 NotReady <none> 1d v1.32.1\n",
                "node-03 Ready control-plane 5d v1.32.1\n",
            ])
            rows = list(analyzer.rows())
            self.assertEqual({row["count"] for row in rows}, {1, 2})
            self.assertEqual(sum(row["count"] for row in rows), 3)
            self.assertTrue(all(row["parser"] == "k8s_snapshot_nodes" for row in rows))
            self.assertEqual(analyzer.stats["family.snapshot_rows"], 3)
        with Analyzer() as analyzer:
            analyzer.ingest(["NAME  STATUS  CAPACITY\n", "vol-a  Bound  20Gi\n",
                             "vol-b  Pending  10Gi\n"])
            self.assertEqual(analyzer.stats["family.snapshot_rows"], 2)
            self.assertEqual(sum(row["count"] for row in analyzer.rows()), 2)

    def test_describe_reducer_preserves_fields_and_aggregates_events(self):
        block = [
            "Name: api-7c9d8f6b7c-abc12", "Namespace: default", "Labels:",
            "  app=api", "  pod-template-hash=abc12", "Annotations:",
            "  checksum/config=111", "Node: node-01/10.0.0.1", "Status: Running",
            "Restart Count: 0", "Conditions:", "  Type Status", "  Ready True",
            "Events:", "  Type Reason Age From Message",
            "  Normal Pulled 2m kubelet image pulled", "  Warning BackOff 1m kubelet backoff",
        ]
        changed = [line.replace("abc12", "def34").replace("111", "222")
                   for line in block]
        with Analyzer() as analyzer:
            analyzer.ingest([line + "\n" for line in block + [""] + changed])
            rows = list(analyzer.rows())
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["parser"], "k8s_describe_pod")
            self.assertEqual(row["count"], 2)
            self.assertIn('conditions="Ready=True"', row["pattern"])
            self.assertIn('events="Normal:Pulled=1,Warning:BackOff=1"', row["pattern"])
            self.assertEqual(row["variant_unique_count"], 2)
            self.assertTrue(any('checksum/config=111' in signature for signature in row["variants"]))
            self.assertTrue(any('checksum/config=222' in signature for signature in row["variants"]))
            self.assertEqual(analyzer.stats["family.describe_records"], 2)

    def test_variants_use_frequency_ranked_top_n_and_phase_counts(self):
        with Analyzer(Config(max_variants=1)) as analyzer:
            analyzer.ingest(["GET /users/987 HTTP/1.1 200"], "baseline")
            analyzer.ingest(["GET /users/123 HTTP/1.1 200"] * 5, "baseline")
            analyzer.ingest(["GET /users/123 HTTP/1.1 200"] * 2 +
                            ["GET /users/456 HTTP/1.1 200"] * 2, "current")
            row = next(analyzer.rows())
            self.assertEqual(row["variants"], {
                "GET /users/123 HTTP/1.1 200": {"count": 7, "baseline": 5, "current": 2},
            })
            self.assertEqual(row["variant_other_count"], 3)
            self.assertEqual(row["variant_unique_count"], 3)
            self.assertEqual((row["baseline"], row["current"]), (6, 4))

    def test_variants_are_visible_in_reports_and_json_is_versioned(self):
        with Analyzer() as analyzer:
            analyzer.ingest(["GET /users/123 HTTP/1.1 200",
                             "GET /users/456 HTTP/1.1 200"])
            summary, rows = analyzer.summary(), list(analyzer.rows())
            text = "".join(render(summary, rows, "text"))
            markdown = "".join(render(summary, rows, "markdown"))
            html_report = "".join(render(summary, rows, "html"))
            self.assertIn("+123", text)
            self.assertIn("+456", text)
            self.assertNotIn("GET /users/123 HTTP/1.1 200", text)
            self.assertIn("+123", markdown)
            self.assertIn("+456", html_report)
            encoded = json.loads("".join(render(summary, rows, "json")))
            self.assertEqual(encoded["summary"]["schema_version"], "4.0")
            self.assertEqual(len(encoded["patterns"][0]["variants"]), 2)
            jsonl = [json.loads(line) for line in "".join(render(summary, rows, "jsonl")).splitlines()]
            self.assertEqual(jsonl[0]["schema_version"], "4.0")
            self.assertEqual(jsonl[1]["type"], "pattern")

    def test_adaptive_variability_merges_high_cardinality_text_and_keeps_variants(self):
        lines = [f"tenant={value} job failed" for value in
                 ("abc17", "hfg32", "zzk91", "qwe48", "abc17")]
        with Analyzer(Config(max_variants=2)) as analyzer:
            analyzer.ingest(lines)
            rows = list(analyzer.rows())
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["pattern"], "tenant=<ID> job failed")
            self.assertEqual(row["representative"], "tenant=abc17 job failed")
            self.assertEqual(row["count"], 5)
            self.assertEqual(row["variant_unique_count"], 4)
            self.assertEqual(row["variant_other_count"], 2)
            self.assertEqual(sum(item["count"] for item in row["variants"].values()), 3)
            self.assertEqual(analyzer.stats["adaptive.promoted_positions"], 1)

    def test_adaptive_host_word_merge_preserves_outcomes_and_status_codes(self):
        lines = ["connection to node-a failed", "connection to node-b failed",
                 "connection to node-c failed", "connection established",
                 "connection established", "connection failed"]
        with Analyzer() as analyzer:
            analyzer.ingest(lines)
            rows = list(analyzer.rows())
            by_pattern = {row["pattern"]: row["count"] for row in rows}
            self.assertEqual(by_pattern["connection to <ID> failed"], 3)
            self.assertEqual(by_pattern["connection established"], 2)
            self.assertEqual(by_pattern["connection failed"], 1)
        with Analyzer() as analyzer:
            analyzer.ingest(["HTTP/1.1 200 ok", "HTTP/1.1 404 not-found",
                             "HTTP/1.1 500 failed"] * 2)
            rows = list(analyzer.rows())
            patterns = {row["pattern"]: row["count"] for row in rows}
            self.assertEqual(patterns, {
                "HTTP/1.1 200 ok": 2,
                "HTTP/1.1 404 not-found": 2,
                "HTTP/1.1 500 failed": 2,
            })

    def test_adaptive_json_values_preserve_status_service_and_component(self):
        lines = [
            '{"tenant":"abc17","status":"failed","service":"api","component":"worker"}',
            '{"tenant":"hfg32","status":"failed","service":"api","component":"worker"}',
            '{"tenant":"zzk91","status":"failed","service":"api","component":"worker"}',
            '{"tenant":"qwe48","status":"succeeded","service":"api","component":"worker"}',
            '{"tenant":"abc17","status":"failed","service":"billing","component":"worker"}',
            '{"tenant":"hfg32","status":"failed","service":"billing","component":"worker"}',
            '{"tenant":"zzk91","status":"failed","service":"billing","component":"worker"}',
        ]
        with Analyzer() as analyzer:
            analyzer.ingest(lines)
            rows = list(analyzer.rows())
            self.assertEqual(len(rows), 3)
            self.assertEqual(sorted(row["count"] for row in rows), [1, 3, 3])
            self.assertEqual({(json.loads(row["pattern"])["status"],
                               json.loads(row["pattern"])["service"]): row["count"]
                              for row in rows}, {
                ("failed", "api"): 3, ("failed", "billing"): 3,
                ("succeeded", "api"): 1,
            })
            self.assertTrue(all('"tenant":"<ID>"' in row["pattern"]
                                for row in rows if row["count"] == 3))
            self.assertTrue(any('"tenant":"qwe48"' in row["pattern"]
                                for row in rows if row["count"] == 1))


    def test_adaptive_inference_keeps_namespace_boundaries(self):
        with Analyzer() as analyzer:
            analyzer.ingest([
                '{"namespace":"dev","tenant":"abc17","message":"failed"}',
                '{"namespace":"stage","tenant":"hfg32","message":"failed"}',
                '{"namespace":"prod","tenant":"zzk91","message":"failed"}',
            ])
            rows = list(analyzer.rows())
            self.assertEqual(len(rows), 3)
            self.assertEqual({json.loads(row["pattern"])["namespace"] for row in rows},
                             {"dev", "stage", "prod"})
    def test_timestamped_python_traceback_is_one_logical_event(self):
        lines = [
            "2026-09-27T10:00:00Z ERROR Traceback (most recent call last):\n",
            '  File "/srv/api.py", line 41, in handle\n',
            '    raise ValueError("bad input")\n',
            "ValueError: bad input\n",
        ]
        with Analyzer() as analyzer:
            analyzer.ingest(lines)
            self.assertEqual(analyzer.stats["events"], 1)
            self.assertEqual(analyzer.stats["event_physical_lines"], 4)

    def test_no_static_semantic_overmerge(self):
        lines = ["HTTP 404 failed", "HTTP 500 failed", "connection refused", "connection timeout",
                 "ORA-00600 failed", "ORA-00001 failed", "TimeoutError", "ConnectionRefusedError"]
        self.assertEqual(len(list(group_logs(lines))), len(lines))

    def test_coarse_floor_precedes_residual_leader_constraints(self):
        a, b, c = "x <IPV4> <UUID>", "x <IPV6> <UUID>", "x <IPV6> <HEX>"
        self.assertGreaterEqual(compute_similarity(a, b), 0.96)
        self.assertGreaterEqual(compute_similarity(b, c), 0.96)
        self.assertLess(compute_similarity(a, c), 0.96)
        with Analyzer(Config(threshold=0.96)) as model:
            model.ingest([a, b, c])
            row = next(model.rows())
            self.assertEqual(row["count"], 3)
            self.assertEqual(len(row["variants"]), 3)

    def test_coarse_floor_avoids_semantic_ambiguity_splits(self):
        with Analyzer(Config(threshold=0.95)) as a:
            a.ingest(["x <IPV4> <UUID>", "x <IPV6> <HEX>", "x <IPV4> <HEX>"])
            self.assertEqual(a.stats["clusters"], 1)
            self.assertEqual(a.stats["ambiguous_events"], 0)
            self.assertEqual(len(next(a.rows())["variants"]), 3)

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
            self.assertLessEqual(a.stats["cache_peak"], 8)
            self.assertLessEqual(a.stats["adaptive_cache_peak"], 8)
            self.assertLessEqual(a.stats["comparisons"], 300 * 7)
            self.assertEqual(a.stats["clusters"], 1)
            self.assertEqual(a.stats["adaptive.promoted_positions"], 1)
            self.assertEqual(a.stats["exact_patterns"], 300)
            rows = list(a.rows())
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["count"], 300)
            self.assertEqual(rows[0]["variant_unique_count"], 300)
            self.assertEqual(rows[0]["variant_other_count"], 284)
            self.assertLessEqual(len(rows[0]["variants"]), a.config.max_variants)
            self.assertEqual(a.db.execute("SELECT COUNT(*) FROM adaptive_values").fetchone()[0], 300)
            self.assertEqual(a.db.execute("SELECT COUNT(*) FROM variants").fetchone()[0], 300)
            self.assertGreater(a.db.execute("PRAGMA page_count").fetchone()[0], 0)

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
            self.assertIn("<IP>", matched["pattern"])
            self.assertTrue(any("<IPV4>" in variant and stats["baseline"] == 1
                                for variant, stats in matched["variants"].items()))
            self.assertTrue(any("<IPV6>" in variant and stats["current"] == 1
                                for variant, stats in matched["variants"].items()))
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
                       {"depth": 17}, {"cache_size": 0}, {"max_variants": 0},
                       {"max_clusters": -1}]:
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
            event = json.loads(output.getvalue())
            self.assertIn("<IP>", event["pattern"])
            self.assertIn("<IPV6>", event["semantic_pattern"])

    def test_failure_does_not_replace_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            source, target = Path(d) / "in", Path(d) / "out"
            source.write_text("a line longer than eight bytes\n")
            target.write_text("previous report")
            with patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(main([str(source), str(target), "--max-event-bytes", "8"]), 3)
            self.assertEqual(target.read_text(), "previous report")


class PackagingTests(unittest.TestCase):
    def test_archives_rebuild_identically_and_have_fixed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            prefix = "logtrim-4.0.0"
            clean = output / "clean.zip"
            standalone = output / "standalone.pyz"
            source = output / "source.tar.gz"
            for _ in range(2):
                build_dist.write_zip(clean, prefix, build_dist.distribution_files())
                build_dist.write_pyz(standalone)
                build_dist.write_tar(source, prefix, build_dist.source_files())
                hashes = tuple(build_dist.sha256(path) for path in (clean, standalone, source))
                if _ == 0:
                    first_hashes = hashes
                else:
                    self.assertEqual(hashes, first_hashes)

            with zipfile.ZipFile(clean) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertIn("logtrim-4.0.0/tests/test_logtrim.py", names)
                self.assertIn("logtrim-4.0.0/build_dist.py", names)
                self.assertIn("logtrim-4.0.0/benchmarks/differential.py", names)
                self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0)
                                    and info.external_attr >> 16 == 0o100644
                                    for info in archive.infolist()))
            with zipfile.ZipFile(standalone) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertIn("README.md", names)
                self.assertIn("USAGE_KO.md", names)
                self.assertIn("logtrim/variability.py", names)
                self.assertNotIn("tests/test_logtrim.py", names)
                self.assertNotIn("pyproject.toml", names)
                self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0)
                                    for info in archive.infolist()))
            with tarfile.open(source, "r:gz") as archive:
                members = archive.getmembers()
                self.assertTrue(all(member.mtime == 0 and member.uid == 0 and member.gid == 0
                                    and member.mode == 0o644 for member in members))
                self.assertIn("logtrim-4.0.0/logtrim/variability.py",
                              {member.name for member in members})

    def test_standalone_runs_version_analyze_and_explain(self):
        with tempfile.TemporaryDirectory() as tmp:
            standalone = Path(tmp) / "logtrim.pyz"
            build_dist.write_pyz(standalone)
            version = subprocess.run([sys.executable, str(standalone), "--version"],
                                     text=True, capture_output=True, check=True)
            self.assertEqual(version.stdout.strip(), "4.0.0")
            source = Path(tmp) / "input.log"
            source.write_text("\n".join(f"tenant={value} job failed" for value in
                                         ("abc17", "hfg32", "zzk91", "qwe48")) + "\n")
            analyzed = subprocess.run([sys.executable, str(standalone), str(source), "-",
                                       "--format", "json"], text=True, capture_output=True,
                                      check=True)
            report = json.loads(analyzed.stdout)
            self.assertEqual(report["summary"]["schema_version"], "4.0")
            self.assertEqual(report["patterns"][0]["pattern"], "tenant=<ID> job failed")
            explained = subprocess.run([sys.executable, str(standalone), "explain", "--line",
                                        "ORA-00600 peer ::1"], text=True, capture_output=True,
                                       check=True)
            self.assertIn("<IP>", json.loads(explained.stdout)["pattern"])

    def test_build_main_writes_sha256_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = [str(ROOT / "build_dist.py"), "--output-dir", tmp,
                    "--date", "2026-09-27"]
            with patch.object(sys, "argv", args):
                build_dist.main()
            manifest = Path(tmp) / "SHA256SUMS"
            first = manifest.read_bytes()
            with patch.object(sys, "argv", args):
                build_dist.main()
            self.assertEqual(manifest.read_bytes(), first)
            expected = {"logtrim-4.0.0-clean.zip", "logtrim-4.0.0-standalone.pyz",
                        "logtrim-4.0.0-source-2026-09-27.tar.gz"}
            lines = first.decode("ascii").splitlines()
            self.assertEqual({line.split("  ", 1)[1] for line in lines}, expected)
            for line in lines:
                digest, name = line.split("  ", 1)
                self.assertEqual(digest, build_dist.sha256(Path(tmp) / name))


if __name__ == "__main__":
    unittest.main()