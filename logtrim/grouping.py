"""로그 그룹화 모듈.

유사한 로그 라인들을 패턴 기반으로 그룹화합니다.
exact match 우선, 그 다음 유사도 비교를 통해 버킷을 최적화합니다.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Iterator

from logtrim.models import LogPattern
from logtrim.patterns import extract_pattern, parse_timestamp
from logtrim.similarity import compute_similarity


class _UnionFind:
    """소집합 병합을 위한 유니온파인드 구조."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


def _block_key(pattern: str, n_tokens: int = 2) -> str:
    """블록 키 생성: 패턴의 앞부분 토큰으로 유사한 패턴만 비교.

    Args:
        pattern: 패턴 문자열
        n_tokens: 블록 키에 사용할 토큰 수

    Returns:
        패턴의 앞 n_tokens 토큰을 공백으로 연결한 문자열
    """
    tokens = pattern.split()
    return " ".join(tokens[:n_tokens])


def _length_bucket(pattern: str, bucket_size: int = 20) -> int:
    """패턴 길이를 버킷으로 분류.

    Args:
        pattern: 패턴 문자열
        bucket_size: 버킷 크기

    Returns:
        길이 버킷 인덱스
    """
    return len(pattern) // bucket_size


def _group_patterns_internal(
    patterns: list[str],
    counts: dict[str, int],
    threshold: float,
) -> list[LogPattern]:
    """내부 헬퍼: 패턴 리스트와 카운터로부터 그룹을 생성합니다.

    Uses a blocking index to avoid O(n^2) pairwise comparisons.
    Only patterns sharing the same block key are compared.

    Args:
        patterns: 고유 패턴 리스트
        counts: 패턴별 카운터
        threshold: 유사도 임계값

    Returns:
        LogPattern 인스턴스 리스트 (count 내림차순 정렬)
    """
    if not patterns:
        return []

    uf = _UnionFind()

    # Build 2D blocking index: (prefix_block_key, length_bucket)
    # Similar patterns must share both prefix AND similar length
    blocks: dict[tuple[str, int], list[str]] = {}
    for p in patterns:
        key = _block_key(p)
        bucket = _length_bucket(p)
        blocks.setdefault((key, bucket), []).append(p)

    # Compare only within the same 2D block
    for (key, bucket), block_patterns in blocks.items():
        if len(block_patterns) == 1:
            continue
        for i in range(len(block_patterns)):
            for j in range(i + 1, len(block_patterns)):
                sim = compute_similarity(block_patterns[i], block_patterns[j])
                if sim >= threshold:
                    uf.union(block_patterns[i], block_patterns[j])

    # 그룹별로 모으기
    groups: dict[str, list[str]] = {}
    for p in patterns:
        root = uf.find(p)
        groups.setdefault(root, []).append(p)

    # 각 그룹에서 대표 패턴 선택 (가장 높은 count를 가진 패턴)
    result: list[LogPattern] = []
    for members in groups.values():
        rep = max(members, key=lambda p: counts.get(p, 0))
        total_count = sum(counts.get(p, 0) for p in members)
        result.append(
            LogPattern(
                pattern=rep,
                count=total_count,
                sample="",
                first_seen=datetime.min,
                last_seen=datetime.min,
            )
        )

    # count 내림차순 정렬
    result.sort(key=lambda p: p.count, reverse=True)
    return result


def group_logs(
    lines: Iterator[str],
    threshold: float = 0.85,
) -> Iterator[LogPattern]:
    """로그 라인들을 패턴 기반으로 그룹화합니다.

    Args:
        lines: 원본 로그 라인 이터레이터
        threshold: 유사도 임계값 (기본 0.85)

    Yields:
        LogPattern 인스턴스 (count 내림차순)
    """
    # 1. 패턴 추출 및 카운팅, 타임스탬프/샘플 추적
    pattern_counter: Counter = Counter()
    pattern_first_seen: dict[str, datetime] = {}
    pattern_last_seen: dict[str, datetime] = {}
    pattern_sample: dict[str, str] = {}
    unique_patterns: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        pattern = extract_pattern(line)
        ts = parse_timestamp(line)

        pattern_counter[pattern] += 1

        if pattern not in pattern_sample:
            pattern_sample[pattern] = line
            unique_patterns.append(pattern)
            if ts is not None:
                pattern_first_seen[pattern] = ts
            else:
                pattern_first_seen[pattern] = datetime.min

        # last_seen 업데이트
        if ts is not None:
            if pattern not in pattern_last_seen:
                pattern_last_seen[pattern] = ts
            else:
                if ts > pattern_last_seen[pattern]:
                    pattern_last_seen[pattern] = ts
        elif pattern not in pattern_last_seen:
            pattern_last_seen[pattern] = datetime.min

    # 2. 그룹화
    patterns_list = list(pattern_counter.keys())
    groups = _group_patterns_internal(patterns_list, dict(pattern_counter), threshold)

    # 3. 각 그룹에 sample, first_seen, last_seen 주입
    for group in groups:
        rep_pattern = group.pattern
        group.sample = pattern_sample.get(rep_pattern, rep_pattern)
        group.first_seen = pattern_first_seen.get(rep_pattern, datetime.min)
        group.last_seen = pattern_last_seen.get(rep_pattern, datetime.min)

    yield from groups


def group_patterns(
    pattern_counts: dict[str, int],
    threshold: float = 0.85,
) -> Iterator[LogPattern]:
    """정규화된 패턴들의 카운터로부터 그룹화합니다.

    Args:
        pattern_counts: 패턴별 카운터 딕셔너리
        threshold: 유사도 임계값 (기본 0.85)

    Yields:
        LogPattern 인스턴스 (count 내림차순)
    """
    patterns = list(pattern_counts.keys())
    groups = _group_patterns_internal(patterns, pattern_counts, threshold)

    for group in groups:
        # sample은 대표 패턴 자체, timestamp는 기본값
        group.sample = group.pattern
        yield group
