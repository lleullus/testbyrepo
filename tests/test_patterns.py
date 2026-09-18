import unittest
from logtrim.patterns import extract_pattern


class TestExtractPattern(unittest.TestCase):
    """patterns.py - extract_pattern 테스트"""

    # ------------------------------------------------------------------
    # 1. URL
    # ------------------------------------------------------------------
    def test_extract_pattern_url(self):
        """URL → <URL>"""
        self.assertEqual(
            extract_pattern("GET https://example.com/path HTTP"),
            "GET <URL> HTTP",
        )

    def test_extract_pattern_url_https(self):
        """HTTPS URL → <URL>"""
        self.assertEqual(
            extract_pattern("redirect https://secure.example.com/login"),
            "redirect <URL>",
        )

    # ------------------------------------------------------------------
    # 2. TIMESTAMP (ISO)
    # ------------------------------------------------------------------
    def test_extract_pattern_timestamp_iso(self):
        """ISO timestamp → <TIMESTAMP>"""
        self.assertEqual(
            extract_pattern("2024-01-15T10:30:45.123Z message"),
            "<TIMESTAMP> message",
        )

    def test_extract_pattern_timestamp_iso_space(self):
        """ISO timestamp with space separator → <TIMESTAMP>"""
        self.assertEqual(
            extract_pattern("2024-01-15 10:30:45 message"),
            "<TIMESTAMP> message",
        )

    # ------------------------------------------------------------------
    # 3. TIMESTAMP (syslog)
    # ------------------------------------------------------------------
    def test_extract_pattern_timestamp_syslog(self):
        """Syslog timestamp → <TIMESTAMP>"""
        self.assertEqual(
            extract_pattern("Jan 15 10:30:45 hostname process"),
            "<TIMESTAMP> hostname process",
        )

    def test_extract_pattern_timestamp_syslog_single_digit_day(self):
        """Syslog timestamp with single-digit day → <TIMESTAMP>"""
        self.assertEqual(
            extract_pattern("Dec  5 08:01:03 server app"),
            "<TIMESTAMP> server app",
        )

    # ------------------------------------------------------------------
    # 4. UUID
    # ------------------------------------------------------------------
    def test_extract_pattern_uuid(self):
        """UUID → <UUID>"""
        self.assertEqual(
            extract_pattern("id=550e8400-e29b-41d4-a716-446655440000"),
            "id=<UUID>",
        )

    def test_extract_pattern_uuid_uppercase(self):
        """대문자 UUID → <UUID>"""
        self.assertEqual(
            extract_pattern("id=550E8400-E29B-41D4-A716-446655440000"),
            "id=<UUID>",
        )

    # ------------------------------------------------------------------
    # 5. MAC
    # ------------------------------------------------------------------
    def test_extract_pattern_mac(self):
        """MAC 주소 (콜론 구분) → <MAC>"""
        self.assertEqual(
            extract_pattern("src=00:1A:2B:3C:4D:5E"),
            "src=<MAC>",
        )

    def test_extract_pattern_mac_dash(self):
        """MAC 주소 (대시 구분) → <MAC>"""
        self.assertEqual(
            extract_pattern("dst=00-1A-2B-3C-4D-5E"),
            "dst=<MAC>",
        )

    # ------------------------------------------------------------------
    # 6. IPv4
    # ------------------------------------------------------------------
    def test_extract_pattern_ipv4(self):
        """IPv4 주소 → <IPV4>"""
        self.assertEqual(
            extract_pattern("src=192.168.1.1 dst=10.0.0.1"),
            "src=<IPV4> dst=<IPV4>",
        )

    # ------------------------------------------------------------------
    # 7. IPv6
    # ------------------------------------------------------------------
    def test_extract_pattern_ipv6_expanded(self):
        """확장된 IPv6 주소 → <IPV6>"""
        self.assertEqual(
            extract_pattern("src=2001:0db8:85a3:0000:0000:8a2e:0370:7334"),
            "src=<IPV6>",
        )

    def test_extract_pattern_ipv6_compressed(self):
        """축약된 IPv6 주소 → <IPV6>"""
        self.assertEqual(
            extract_pattern("src=2001:db8::1"),
            "src=<IPV6>",
        )

    # ------------------------------------------------------------------
    # 8. PATH
    # ------------------------------------------------------------------
    def test_extract_pattern_path(self):
        """파일 경로 → <PATH>"""
        self.assertEqual(
            extract_pattern("open /var/log/syslog done"),
            "open <PATH> done",
        )

    def test_extract_pattern_path_relative(self):
        """상대 경로 → <PATH>"""
        self.assertEqual(
            extract_pattern("cd /src/main.py ok"),
            "cd <PATH> ok",
        )

    # ------------------------------------------------------------------
    # 9. DOMAIN
    # ------------------------------------------------------------------
    def test_extract_pattern_domain(self):
        """도메인 이름 → <DOMAIN>"""
        self.assertEqual(
            extract_pattern("host=example.com"),
            "host=<DOMAIN>",
        )

    def test_extract_pattern_domain_subdomain(self):
        """서브도메인 포함 → <DOMAIN>"""
        self.assertEqual(
            extract_pattern("host=api.internal.example.com"),
            "host=<DOMAIN>",
        )

    # ------------------------------------------------------------------
    # 10. HEX
    # ------------------------------------------------------------------
    def test_extract_pattern_hex(self):
        """HEX 문자열 (8자 이상) → <HEX>"""
        self.assertEqual(
            extract_pattern("crc=abcdef0123456789"),
            "crc=<HEX>",
        )

    # ------------------------------------------------------------------
    # 11. NUMBER
    # ------------------------------------------------------------------
    def test_extract_pattern_number(self):
        """숫자 → <NUMBER>"""
        self.assertEqual(
            extract_pattern("count=42 remaining=0"),
            "count=<NUMBER> remaining=<NUMBER>",
        )

    # ------------------------------------------------------------------
    # 12. WHITESPACE CLEANUP
    # ------------------------------------------------------------------
    def test_extract_pattern_whitespace(self):
        """여러 공백 → 단일 공백"""
        self.assertEqual(
            extract_pattern("a    b   c"),
            "a b c",
        )

    def test_extract_pattern_whitespace_mixed(self):
        """변수 교체 후 공백 정리"""
        result = extract_pattern("src=192.168.1.1    dst=10.0.0.1")
        self.assertEqual(result, "src=<IPV4> dst=<IPV4>")

    # ------------------------------------------------------------------
    # 13. ORDER — URL이 NUMBER 전에 먼저 교체되어야 함
    # ------------------------------------------------------------------
    def test_extract_pattern_order_url_before_number(self):
        """URL 안에 숫자가 있어도 <URL>로 먼저 교체되어야 함"""
        result = extract_pattern("url=https://192.168.1.1:8080/path end")
        self.assertEqual(result, "url=<URL> end")

    def test_extract_pattern_order_ipv4_before_number(self):
        """IPv4 가 NUMBER 전에 먼저 교체되어야 함"""
        result = extract_pattern("ip=192.168.1.1 count=5")
        self.assertEqual(result, "ip=<IPV4> count=<NUMBER>")

    # ------------------------------------------------------------------
    # 14. K8s 로그 샘플
    # ------------------------------------------------------------------
    def test_extract_pattern_k8s_log(self):
        """실제 K8s 로그 샘플 테스트"""
        log_line = (
            '2024-01-15T10:30:45.123Z logger     '
            'src=10.0.0.1 dst=192.168.1.100 '
            'uuid=550e8400-e29b-41d4-a716-446655440000 '
            'url=https://api.example.com/v1/resource '
            'path=/var/log/app.log '
            'mac=00:1A:2B:3C:4D:5E '
            'hex=abcdef0123456789 '
            'port=8080'
        )
        result = extract_pattern(log_line)
        # 각 요소가 올바르게 교체되었는지 확인
        self.assertIn("<TIMESTAMP>", result)
        self.assertIn("<IPV4>", result)
        self.assertIn("<UUID>", result)
        self.assertIn("<URL>", result)
        self.assertIn("<PATH>", result)
        self.assertIn("<MAC>", result)
        self.assertIn("<HEX>", result)
        self.assertIn("<NUMBER>", result)
        # 중복 공백 없음
        self.assertNotIn("  ", result)


if __name__ == "__main__":
    unittest.main()


class TestParseTimestamp(unittest.TestCase):
    """patterns.py - parse_timestamp 테스트"""

    def test_parse_timestamp_iso(self):
        """ISO timestamp 파싱 성공"""
        from logtrim.patterns import parse_timestamp
        result = parse_timestamp("2024-01-15T10:30:45.123Z message")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 30)
        self.assertEqual(result.second, 45)

    def test_parse_timestamp_iso_space_separator(self):
        """ISO timestamp with space separator"""
        from logtrim.patterns import parse_timestamp
        result = parse_timestamp("2024-01-15 10:30:45 message")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_parse_timestamp_syslog(self):
        """Syslog timestamp 파싱"""
        from logtrim.patterns import parse_timestamp
        result = parse_timestamp("Jan 15 10:30:45 hostname process")
        self.assertIsNotNone(result)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 10)
        self.assertEqual(result.minute, 30)
        self.assertEqual(result.second, 45)

    def test_parse_timestamp_invalid(self):
        """유효하지 않은 timestamp → None"""
        from logtrim.patterns import parse_timestamp
        result = parse_timestamp("not-a-timestamp at all")
        self.assertIsNone(result)

    def test_parse_timestamp_not_in_line(self):
        """timestamp 없는 라인 → None"""
        from logtrim.patterns import parse_timestamp
        result = parse_timestamp("just a plain line with no time")
        self.assertIsNone(result)


class TestExtractPatternHeuristics(unittest.TestCase):
    """patterns.py - extract_pattern heuristic 확장 테스트"""

    def test_extract_pattern_ident_mixed(self):
        """혼합 식별자 (web-7d9f8b6d9f-abcde) → <IDENT>"""
        from logtrim.patterns import extract_pattern
        result = extract_pattern("server=web-7d9f8b6d9f-abcde running")
        self.assertIn("<IDENT>", result)
        self.assertNotIn("7d9f8b6d9f-abcde", result)

    def test_extract_pattern_id_random(self):
        """랜덤 문자열 (20자리 이상 알파벳+숫자) → <ID>"""
        from logtrim.patterns import extract_pattern
        result = extract_pattern("token=abcdefghij1234567890 done")
        self.assertIn("<ID>", result)
        self.assertNotIn("abcdefghij1234567890", result)

    def test_extract_pattern_k8s_pod(self):
        """K8s pod 식별자 → <IDENT>"""
        from logtrim.patterns import extract_pattern
        result = extract_pattern("pod=web-7d9f8b6d9f-abcde namespace=default")
        self.assertIn("<IDENT>", result)
        self.assertNotIn("web-7d9f8b6d9f-abcde", result)

    def test_extract_pattern_heuristics_combined(self):
        """여러 heuristic 복합 테스트"""
        from logtrim.patterns import extract_pattern
        log_line = (
            "2024-01-15T10:30:45.123Z app "
            "pod=web-7d9f8b6d9f-abcde "
            "token=abcdefghij1234567890 "
            "container=my-app "
            "count=42"
        )
        result = extract_pattern(log_line)
        self.assertIn("<TIMESTAMP>", result)
        self.assertIn("<IDENT>", result)
        self.assertIn("<ID>", result)
        self.assertIn("<NUMBER>", result)
        # 중복 공백 없음
        self.assertNotIn("  ", result)
