"""Tests for logtrim.similarity similarity functions."""

import unittest
from unittest.mock import patch

from logtrim.similarity import compute_similarity, token_similarity


class TestComputeSimilarity(unittest.TestCase):
    """Test compute_similarity function."""

    def test_compute_similarity_identical(self):
        """동일한 문자열은 유사도 1.0을 반환해야 함."""
        result = compute_similarity("hello world", "hello world")
        self.assertAlmostEqual(result, 1.0, places=1)

    def test_compute_similarity_different(self):
        """완전히 다른 문자열은 유사도 0.0에 가까워야 함."""
        result = compute_similarity("abc", "xyz")
        self.assertLess(result, 0.3)

    def test_compute_similarity_partial(self):
        """부분 일치 문자열은 0.5~0.9 사이 유사도를 반환해야 함."""
        result = compute_similarity("hello world", "hello python")
        self.assertGreaterEqual(result, 0.5)
        self.assertLessEqual(result, 0.9)

    def test_compute_similarity_case_sensitive(self):
        """대소문자는 구분되어야 함 (유사도 1.0이 아님)."""
        result = compute_similarity("Hello", "hello")
        self.assertNotAlmostEqual(result, 1.0, places=1)

    def test_compute_similarity_empty_strings(self):
        """빈 문자열 처리 테스트."""
        result = compute_similarity("", "")
        self.assertAlmostEqual(result, 1.0, places=1)

        result = compute_similarity("abc", "")
        self.assertLess(result, 0.5)

    def test_compute_similarity_fallback(self):
        """rapidfuzz 미설치 시 difflib fallback이 작동해야 함."""
        import logtrim.similarity as similarity

        # Mock _rapidfuzz_available to test difflib fallback path
        with patch.object(similarity, '_rapidfuzz_available', False):
            result = compute_similarity("test string", "test string")
            self.assertAlmostEqual(result, 1.0, places=1)

            result = compute_similarity("abc", "xyz")
            self.assertLess(result, 0.3)


class TestTokenSimilarity(unittest.TestCase):
    """Test token_similarity function."""

    def test_token_similarity_identical(self):
        """동일한 토큰 시퀀스는 유사도 1.0을 반환해야 함."""
        result = token_similarity("hello world", "hello world")
        self.assertAlmostEqual(result, 1.0, places=1)

    def test_token_similarity_partial(self):
        """부분 일치 토큰 시퀀스는 0.5~0.9 사이 유사도를 반환해야 함."""
        result = token_similarity("hello world foo", "hello world bar")
        self.assertGreaterEqual(result, 0.5)
        self.assertLessEqual(result, 0.9)

    def test_token_similarity_different_order(self):
        """토큰 순서가 다르면 유사도가 낮아져야 함."""
        result1 = token_similarity("a b c", "a b c")
        result2 = token_similarity("a b c", "c b a")
        self.assertGreater(result1, result2)

    def test_token_similarity_empty(self):
        """빈 문자열 처리 테스트."""
        result = token_similarity("", "")
        self.assertAlmostEqual(result, 1.0, places=1)

        result = token_similarity("hello", "")
        self.assertLess(result, 0.5)
