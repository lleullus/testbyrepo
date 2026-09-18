"""유사도 계산 모듈.

두 문자열의 유사도를 0.0~1.0 범위로 계산합니다.
rapidfuzz가 설치되어 있으면 우선 사용하고, 아니면 difflib로 fallback합니다.
"""

import difflib

_rapidfuzz_available = False
try:
    import rapidfuzz  # noqa: F401

    _rapidfuzz_available = True
except ImportError:
    pass


def compute_similarity(a: str, b: str) -> float:
    """두 문자열의 유사도를 0.0~1.0 범위로 계산합니다.

    rapidfuzz가 설치되어 있으면 rapidfuzz.fuzz.ratio를 우선 사용하고,
    아니면 difflib.SequenceMatcher.ratio()로 fallback합니다.

    Args:
        a: 첫 번째 문자열
        b: 두 번째 문자열

    Returns:
        0.0 ~ 1.0 범위의 유사도 (1.0 = 완전 일치)
    """
    if _rapidfuzz_available:
        return rapidfuzz.fuzz.ratio(a, b) / 100.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def token_similarity(a: str, b: str) -> float:
    """공백 기준 tokenize 후 토큰 시퀀스 유사도를 계산합니다.

    Args:
        a: 첫 번째 문자열
        b: 두 번째 문자열

    Returns:
        0.0 ~ 1.0 범위의 토큰 유사도 (1.0 = 완전 일치)
    """
    tokens_a = a.split()
    tokens_b = b.split()

    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    return difflib.SequenceMatcher(None, tokens_a, tokens_b).ratio()
