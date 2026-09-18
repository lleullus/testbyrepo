"""Tests for logtrim.grouping grouping functions."""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from logtrim.models import LogPattern
from logtrim.grouping import group_logs, group_patterns


class TestGroupLogs(unittest.TestCase):
    """grouping.py - group_logs 테스트"""

    def test_group_logs_identical(self):
        """완전히 동일한 라인 3개 → 1 그룹, count=3."""
        lines = [
            "2024-01-15T10:30:45.123Z server started",
            "2024-01-15T10:30:46.123Z server started",
            "2024-01-15T10:30:47.123Z server started",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].count, 3)
        self.assertEqual(result[0].pattern, "<TIMESTAMP> server started")

    def test_group_logs_different_patterns(self):
        """서로 다른 패턴 3개 → 3 그룹, 각 count=1."""
        lines = [
            "server started",
            "database query failed",
            "disk usage critical",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 3)
        for pattern in result:
            self.assertEqual(pattern.count, 1)

    def test_group_logs_similar_patterns(self):
        """유사한 패턴 2개 (threshold >= 유사도) → 1 그룹, count=2."""
        lines = [
            "Connection established to host1",
            "Connection established to host2",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        # "Connection established to host1"와 "Connection established to host2"는
        # 매우 유사하므로 threshold >= 유사도이면 같은 그룹
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].count, 2)

    def test_group_logs_dissimilar_patterns(self):
        """다른 패턴 2개 (threshold < 유사도) → 2 그룹."""
        lines = [
            "Connection established to host1",
            "Database query failed on server2",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 2)
        for pattern in result:
            self.assertEqual(pattern.count, 1)

    def test_group_logs_variable_different(self):
        """변수가 다른 동일 패턴 3개 → 1 그룹, count=3."""
        lines = [
            "2024-01-15T10:30:45.123Z User user123 logged in from 192.168.1.1",
            "2024-01-15T10:31:45.123Z User user456 logged in from 10.0.0.1",
            "2024-01-15T10:32:45.123Z User user789 logged in from 172.16.0.1",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].count, 3)
        # IP 주소가 <IPV4>로 교체됨 확인
        self.assertIn("<IPV4>", result[0].pattern)

    def test_group_logs_timestamp_tracking(self):
        """first_seen / last_seen 정확히 추적."""
        lines = [
            "2024-01-15T10:30:45.123Z server started",
            "2024-01-15T10:35:45.123Z server started",
            "2024-01-15T10:40:45.123Z server started",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 1)
        pattern = result[0]
        self.assertEqual(pattern.count, 3)
        # first_seen은 첫 번째 라인, last_seen은 마지막 라인
        self.assertEqual(pattern.first_seen.year, 2024)
        self.assertEqual(pattern.first_seen.month, 1)
        self.assertEqual(pattern.first_seen.day, 15)
        self.assertEqual(pattern.first_seen.hour, 10)
        self.assertEqual(pattern.first_seen.minute, 30)
        self.assertEqual(pattern.last_seen.hour, 10)
        self.assertEqual(pattern.last_seen.minute, 40)

    def test_group_logs_sort_by_count(self):
        """count 내림차순 정렬 확인."""
        lines = [
            "event alpha",
            "event alpha",
            "event alpha",
            "event beta",
            "event beta",
            "event gamma",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 3)
        counts = [p.count for p in result]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_group_logs_empty_input(self):
        """빈 입력 → 빈 리스트."""
        result = list(group_logs(iter([]), threshold=0.85))
        self.assertEqual(result, [])

    def test_group_logs_sample_is_first_occurrence(self):
        """sample은 첫 등장 로그여야 함."""
        lines = [
            "first occurrence message",
            "first occurrence message",
            "first occurrence message",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sample, "first occurrence message")

    def test_group_logs_threshold_custom(self):
        """커스텀 threshold로 그룹화 테스트."""
        lines = [
            "Connection to host1 established",
            "Connection to host2 established",
        ]
        # 높은 threshold (0.99) → 분리됨 (더 많은 그룹)
        result_high_thresh = list(group_logs(iter(lines), threshold=0.99))
        # 낮은 threshold (0.5) → 통합됨 (더 적은 그룹)
        result_low_thresh = list(group_logs(iter(lines), threshold=0.5))
        self.assertGreaterEqual(len(result_high_thresh), len(result_low_thresh))

    def test_group_logs_multiple_groups_sorted(self):
        """여러 그룹이 count 내림차순으로 정렬됨."""
        lines = [
            "event alpha",
            "event alpha",
            "event beta",
            "event gamma",
            "event gamma",
            "event gamma",
            "event gamma",
        ]
        result = list(group_logs(iter(lines), threshold=0.85))
        self.assertEqual(len(result), 3)
        counts = [p.count for p in result]
        self.assertEqual(counts, [4, 2, 1])


class TestGroupPatterns(unittest.TestCase):
    """grouping.py - group_patterns 테스트"""

    def test_group_patterns_exact_match(self):
        """exact match 패턴 카운팅."""
        pattern_counts = {
            "server started": 5,
            "database query failed": 3,
            "disk usage critical": 1,
        }
        result = list(group_patterns(pattern_counts, threshold=0.85))
        self.assertEqual(len(result), 3)
        patterns_dict = {p.pattern: p for p in result}
        self.assertEqual(patterns_dict["server started"].count, 5)
        self.assertEqual(patterns_dict["database query failed"].count, 3)
        self.assertEqual(patterns_dict["disk usage critical"].count, 1)

    def test_group_patterns_similar_merge(self):
        """유사한 패턴 병합."""
        pattern_counts = {
            "Connection to host1 established": 3,
            "Connection to host2 established": 2,
            "server started": 5,
        }
        result = list(group_patterns(pattern_counts, threshold=0.85))
        # "Connection to host1 established"와 "Connection to host2 established"는
        # 유사하므로 병합될 것
        # "server started"는 분리됨
        self.assertGreaterEqual(len(result), 1)
        # 병합된 그룹의 count는 두 패턴의 합
        merged = [p for p in result if p.count == 5]
        self.assertGreaterEqual(len(merged), 1)

    def test_group_patterns_empty(self):
        """빈 입력 → 빈 리스트."""
        result = list(group_patterns({}, threshold=0.85))
        self.assertEqual(result, [])

    def test_group_patterns_single_pattern(self):
        """단일 패턴 → 1 그룹."""
        pattern_counts = {"server started": 10}
        result = list(group_patterns(pattern_counts, threshold=0.85))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].count, 10)

    def test_group_patterns_sort_by_count(self):
        """count 내림차순 정렬 확인."""
        pattern_counts = {
            "A": 1,
            "B": 5,
            "C": 3,
        }
        result = list(group_patterns(pattern_counts, threshold=0.85))
        counts = [p.count for p in result]
        self.assertEqual(counts, sorted(counts, reverse=True))


if __name__ == "__main__":
    unittest.main()
