"""Tests for logtrim.models dataclasses."""

import unittest
from datetime import datetime

from logtrim.models import LogLine, LogPattern, TrimmedLog


class TestLogLine(unittest.TestCase):
    """Test LogLine dataclass instantiation."""

    def test_instantiation_with_all_fields(self):
        """LogLine 인스턴스화 테스트 (raw, pattern, timestamp)."""
        ts = datetime(2024, 1, 15, 10, 30, 0)
        line = LogLine(
            raw="2024-01-15 10:30:00 INFO Application started",
            pattern="INFO_*",
            timestamp=ts,
        )
        self.assertEqual(line.raw, "2024-01-15 10:30:00 INFO Application started")
        self.assertEqual(line.pattern, "INFO_*")
        self.assertEqual(line.timestamp, ts)

    def test_instantiation_with_empty_raw(self):
        """빈 raw 문자열로도 인스턴스화 가능해야 함."""
        ts = datetime(2024, 1, 15, 10, 30, 0)
        line = LogLine(raw="", pattern="EMPTY", timestamp=ts)
        self.assertEqual(line.raw, "")
        self.assertEqual(line.pattern, "EMPTY")


class TestLogPattern(unittest.TestCase):
    """Test LogPattern dataclass instantiation."""

    def test_instantiation_with_all_fields(self):
        """LogPattern 인스턴스화 테스트 (pattern, count, sample, first_seen, last_seen)."""
        first = datetime(2024, 1, 15, 10, 0, 0)
        last = datetime(2024, 1, 15, 12, 0, 0)
        pattern = LogPattern(
            pattern="INFO_*",
            count=42,
            sample="2024-01-15 10:30:00 INFO Application started",
            first_seen=first,
            last_seen=last,
        )
        self.assertEqual(pattern.pattern, "INFO_*")
        self.assertEqual(pattern.count, 42)
        self.assertEqual(
            pattern.sample, "2024-01-15 10:30:00 INFO Application started"
        )
        self.assertEqual(pattern.first_seen, first)
        self.assertEqual(pattern.last_seen, last)

    def test_count_must_be_positive(self):
        """count는 양의 정수여야 함."""
        ts = datetime(2024, 1, 15, 10, 0, 0)
        pattern = LogPattern(
            pattern="DEBUG_*",
            count=1,
            sample="sample",
            first_seen=ts,
            last_seen=ts,
        )
        self.assertGreaterEqual(pattern.count, 1)


class TestTrimmedLog(unittest.TestCase):
    """Test TrimmedLog dataclass instantiation."""

    def test_instantiation_with_all_fields(self):
        """TrimmedLog 인스턴스화 테스트 (patterns, original_count, trimmed_count, compression_ratio)."""
        ts = datetime(2024, 1, 15, 10, 0, 0)
        patterns = [
            LogPattern(
                pattern="INFO_*",
                count=10,
                sample="sample1",
                first_seen=ts,
                last_seen=ts,
            ),
            LogPattern(
                pattern="ERROR_*",
                count=3,
                sample="sample2",
                first_seen=ts,
                last_seen=ts,
            ),
        ]
        trimmed = TrimmedLog(
            original_count=100,
            trimmed_count=2,
            compression_ratio=0.02,
            patterns=patterns,
        )
        self.assertEqual(trimmed.original_count, 100)
        self.assertEqual(trimmed.trimmed_count, 2)
        self.assertEqual(trimmed.compression_ratio, 0.02)
        self.assertEqual(len(trimmed.patterns), 2)

    def test_compression_ratio_calculation(self):
        """compression_ratio = (1 - trimmed_count / original_count) * 100 계산 테스트."""
        ts = datetime(2024, 1, 15, 10, 0, 0)
        patterns = [
            LogPattern(
                pattern="INFO_*",
                count=50,
                sample="s",
                first_seen=ts,
                last_seen=ts,
            )
        ]
        trimmed = TrimmedLog.create(
            original_count=100,
            trimmed_count=1,
            patterns=patterns,
        )
        self.assertEqual(trimmed.original_count, 100)
        self.assertEqual(trimmed.trimmed_count, 1)
        self.assertAlmostEqual(trimmed.compression_ratio, 99.0)

    def test_compression_ratio_zero_original(self):
        """original_count가 0일 때 compression_ratio는 0.0."""
        trimmed = TrimmedLog.create(
            original_count=0,
            trimmed_count=0,
            patterns=[],
        )
        self.assertEqual(trimmed.compression_ratio, 0.0)

    def test_patterns_default_empty(self):
        """patterns 필드는 기본값으로 빈 리스트."""
        trimmed = TrimmedLog(
            original_count=10,
            trimmed_count=1,
            compression_ratio=0.1,
        )
        self.assertEqual(trimmed.patterns, [])


if __name__ == "__main__":
    unittest.main()
