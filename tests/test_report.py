"""Tests for logtrim.report module."""

import json
import re
import unittest

from logtrim.report import format_text, format_json, format_output


class TestFormatTextHeader(unittest.TestCase):
    """test_format_text_header — 헤더 메타데이터 포함 확인"""

    def test_header_metadata(self):
        summary = {
            "original_count": 12000,
            "trimmed_count": 520,
            "compression_ratio": 99.23,
            "threshold": 0.85,
        }
        patterns = []
        result = format_text(summary, patterns)

        self.assertIn("Log Trimmer Output", result)
        self.assertIn("# input_lines=12000", result)
        self.assertIn("# exact_patterns=12000", result)
        self.assertIn("# grouped_patterns=520", result)
        self.assertIn("# compression_ratio=99.23%", result)
        self.assertIn("# threshold=0.85", result)


class TestFormatTextPatterns(unittest.TestCase):
    """test_format_text_patterns — 패턴 목록 출력 확인"""

    def test_patterns_output(self):
        summary = {
            "original_count": 12000,
            "trimmed_count": 520,
            "compression_ratio": 99.23,
            "threshold": 0.85,
        }
        patterns = [
            {
                "pattern": "<TIMESTAMP> kubelet[<NUMBER>]: Started container <UUID>",
                "count": 812,
                "sample": "2026-04-24 10:00:01 kubelet[1234]: Started container abc-def-123",
                "first_seen": "2026-04-24T10:00:01",
                "last_seen": "2026-04-24T10:59:59",
            },
            {
                "pattern": "pod/<DOMAIN> failed pulling image <PATH>: timeout after <NUMBER>s",
                "count": 433,
                "sample": "pod/myapp failed pulling image /registry/img: timeout after 30s",
                "first_seen": "2026-04-24T11:00:00",
                "last_seen": "2026-04-24T11:30:00",
            },
        ]
        result = format_text(summary, patterns)

        self.assertIn("812", result)
        self.assertIn("433", result)
        self.assertIn("<TIMESTAMP> kubelet[<NUMBER>]: Started container <UUID>", result)
        self.assertIn("pod/<DOMAIN> failed pulling image <PATH>: timeout after <NUMBER>s", result)


class TestFormatTextCountAlignment(unittest.TestCase):
    """test_format_text_count_alignment — COUNT 열 정렬 확인"""

    def test_count_column_right_aligned(self):
        summary = {
            "original_count": 10000,
            "trimmed_count": 3,
            "compression_ratio": 99.97,
            "threshold": 0.85,
        }
        patterns = [
            {"pattern": "pattern A", "count": 1, "sample": "s1", "first_seen": None, "last_seen": None},
            {"pattern": "pattern B", "count": 99, "sample": "s2", "first_seen": None, "last_seen": None},
            {"pattern": "pattern C", "count": 9999, "sample": "s3", "first_seen": None, "last_seen": None},
        ]
        result = format_text(summary, patterns)

        # Extract the padded count portion (leading spaces + digits) from pattern lines
        padded_count_re = re.compile(r"^(\s*\d+)\s{4,}")
        padded_counts = []
        for line in result.split("\n"):
            m = padded_count_re.match(line)
            if m:
                padded_counts.append(m.group(1))

        self.assertEqual(len(padded_counts), len(patterns))
        # All padded count strings should have the same length (right-aligned)
        self.assertEqual(len(set(len(c) for c in padded_counts)), 1)


class TestFormatJsonHeader(unittest.TestCase):
    """test_format_json_header — JSON 헤더 확인"""

    def test_json_structure(self):
        summary = {
            "original_count": 1000,
            "trimmed_count": 120,
            "compression_ratio": 88.0,
            "threshold": 0.85,
        }
        patterns = []
        result = format_json(summary, patterns)
        data = json.loads(result)

        self.assertEqual(data["original_count"], 1000)
        self.assertEqual(data["trimmed_count"], 120)
        self.assertEqual(data["compression_ratio"], 88.0)
        self.assertIn("patterns", data)
        self.assertIsInstance(data["patterns"], list)


class TestFormatJsonPatterns(unittest.TestCase):
    """test_format_json_patterns — JSON 패턴 목록 확인"""

    def test_json_patterns(self):
        summary = {
            "original_count": 1000,
            "trimmed_count": 120,
            "compression_ratio": 88.0,
            "threshold": 0.85,
        }
        patterns = [
            {
                "pattern": "<TIMESTAMP> Failed to connect to <IP>:<PORT>",
                "count": 120,
                "sample": "2026-04-24 10:00:01 Failed to connect to 10.0.0.1:6443",
                "first_seen": "2026-04-24T10:00:01",
                "last_seen": "2026-04-24T10:59:59",
            },
        ]
        result = format_json(summary, patterns)
        data = json.loads(result)

        self.assertEqual(len(data["patterns"]), 1)
        p = data["patterns"][0]
        self.assertEqual(p["pattern"], "<TIMESTAMP> Failed to connect to <IP>:<PORT>")
        self.assertEqual(p["count"], 120)
        self.assertEqual(p["sample"], "2026-04-24 10:00:01 Failed to connect to 10.0.0.1:6443")
        self.assertEqual(p["first_seen"], "2026-04-24T10:00:01")
        self.assertEqual(p["last_seen"], "2026-04-24T10:59:59")


class TestFormatOutputTextDefault(unittest.TestCase):
    """test_format_output_text_default — 디폴트 text 포맷"""

    def test_default_is_text(self):
        summary = {
            "original_count": 100,
            "trimmed_count": 10,
            "compression_ratio": 90.0,
            "threshold": 0.85,
        }
        patterns = []

        result_default = format_output(summary, patterns)
        result_explicit = format_output(summary, patterns, "text")

        self.assertEqual(result_default, result_explicit)
        self.assertIn("Log Trimmer Output", result_default)


class TestFormatOutputJson(unittest.TestCase):
    """test_format_output_json — JSON 포맷"""

    def test_json_format(self):
        summary = {
            "original_count": 100,
            "trimmed_count": 10,
            "compression_ratio": 90.0,
            "threshold": 0.85,
        }
        patterns = []

        result = format_output(summary, patterns, "json")
        data = json.loads(result)

        self.assertIn("original_count", data)
        self.assertIn("patterns", data)


class TestFormatOutputInvalid(unittest.TestCase):
    """test_format_output_invalid — 잘못된 포맷 → ValueError"""

    def test_invalid_format_raises_valueerror(self):
        summary = {
            "original_count": 100,
            "trimmed_count": 10,
            "compression_ratio": 90.0,
            "threshold": 0.85,
        }
        patterns = []

        with self.assertRaises(ValueError):
            format_output(summary, patterns, "xml")

        with self.assertRaises(ValueError):
            format_output(summary, patterns, "csv")


class TestFormatTextEmpty(unittest.TestCase):
    """test_format_text_empty — 빈 패턴 목록"""

    def test_empty_patterns(self):
        summary = {
            "original_count": 0,
            "trimmed_count": 0,
            "compression_ratio": 0.0,
            "threshold": 0.85,
        }
        result = format_text(summary, [])

        self.assertIn("Log Trimmer Output", result)
        self.assertIn("# input_lines=0", result)
        self.assertIn("# exact_patterns=0", result)
        self.assertIn("# grouped_patterns=0", result)


class TestCompressionRatioCalculation(unittest.TestCase):
    """test_compression_ratio_calculation — 압축률 계산 정확성"""

    def test_compression_ratio_in_text(self):
        summary = {
            "original_count": 10000,
            "trimmed_count": 100,
            "compression_ratio": 99.0,
            "threshold": 0.85,
        }
        result = format_text(summary, [])
        self.assertIn("# compression_ratio=99.0%", result)

    def test_compression_ratio_in_json(self):
        summary = {
            "original_count": 10000,
            "trimmed_count": 100,
            "compression_ratio": 99.0,
            "threshold": 0.85,
        }
        result = format_json(summary, [])
        data = json.loads(result)
        self.assertEqual(data["compression_ratio"], 99.0)

    def test_ratio_precision(self):
        summary = {
            "original_count": 12000,
            "trimmed_count": 92,
            "compression_ratio": 99.23,
            "threshold": 0.85,
        }
        result_text = format_text(summary, [])
        result_json = format_json(summary, [])

        self.assertIn("# compression_ratio=99.23%", result_text)
        data = json.loads(result_json)
        self.assertEqual(data["compression_ratio"], 99.23)


if __name__ == "__main__":
    unittest.main()
