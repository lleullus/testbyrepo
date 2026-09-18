"""변수 감지 및 패턴 추출 모듈.

로그 줄에서 다양한 변수 유형 (URL, 타임스탬프, IP 주소 등) 을
감지하고 <TYPE> 플레이스홀더로 교체하여 패턴화합니다.
"""

from datetime import datetime
import re


# ------------------------------------------------------------------
# Regex 정의 (중요: 호출 순서가 매칭 우선순위가 됨)
# ------------------------------------------------------------------

# 1. URL (http/https)
_RE_URL = re.compile(r'https?://[^\s]+')

# 2. TIMESTAMP — ISO 형식 (optional fractional seconds + TZ) + syslog 형식
_RE_TIMESTAMP = re.compile(
    r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?'
    r'|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'
)

# 3. UUID
_RE_UUID = re.compile(
    r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
)

# 4. MAC
_RE_MAC = re.compile(r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}')

# 5. IPv4
_RE_IPV4 = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

# 6. IPv6 — full, compressed in middle, compressed at end, compressed at start
_RE_IPV6 = re.compile(
    r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}'  # full 8 groups
    r'|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}'  # 1-6 groups + : + 1 group
    r'|(?:[0-9a-fA-F]{1,4}:)+::'  # 1+ groups + ::
    r'|(?:[0-9a-fA-F]{1,4}:){1,7}:'  # 1-7 groups + : (compressed at end)
    r'|::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}'  # starts with ::
    r'|::'  # just ::
)

# 7. PATH — 버전 번호 (/1.1 등) 제외
_RE_PATH = re.compile(r'/(?!1\.1\b|1\.0\b)[^\s]+')

# 8. DOMAIN
_RE_DOMAIN = re.compile(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+')

# 9. HEX (8 자 이상)
_RE_HEX = re.compile(r'\b[0-9a-fA-F]{8,}\b')

# 10. NUMBER
_RE_NUMBER = re.compile(r'\b\d+\b')

# 11. IDENT — 혼합 식별자 (예: web-7d9f8b6d9f-abcde)
_RE_IDENT = re.compile(
    r'[a-zA-Z][a-zA-Z0-9]*-[0-9a-fA-F]{4,}(?:-[0-9a-fA-F]{4,})*'
)

# 12. ID — 랜덤 문자열 (20 자리 이상 알파벳 + 숫자)
_RE_ID = re.compile(
    r'[a-zA-Z][a-zA-Z0-9]{19,}'
)


# ------------------------------------------------------------------
# 플레이스홀더 매핑 (순서 = 우선순위)
# ------------------------------------------------------------------
_PATTERNS = [
    (_RE_URL,        '<URL>'),
    (_RE_TIMESTAMP,  '<TIMESTAMP>'),
    (_RE_UUID,       '<UUID>'),
    (_RE_MAC,        '<MAC>'),
    (_RE_IPV4,       '<IPV4>'),
    (_RE_IPV6,       '<IPV6>'),
    (_RE_PATH,       '<PATH>'),
    (_RE_DOMAIN,     '<DOMAIN>'),
    (_RE_IDENT,      '<IDENT>'),
    (_RE_ID,         '<ID>'),
    (_RE_HEX,        '<HEX>'),
    (_RE_NUMBER,     '<NUMBER>'),
]


def extract_pattern(raw_line: str) -> str:
    """주어진 로그 줄에서 변수를 감지하고 <TYPE> 플레이스홀더로 교체합니다.

    교체 순서 (중요):
        URL → TIMESTAMP → UUID → MAC → IPV4 → IPV6 → PATH → DOMAIN →
        IDENT → ID → HEX → NUMBER

    공백 정리:
        여러 연속 공백을 단일 공백으로 줄입니다.

    Args:
        raw_line: 원본 로그 줄

    Returns:
        변수가 <TYPE> 플레이스홀더로 교체된 패턴화 된 줄
    """
    result = raw_line

    for regex, placeholder in _PATTERNS:
        result = regex.sub(placeholder, result)

    # 공백 정리: 여러 연속 공백 → 단일 공백
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def parse_timestamp(line: str) -> datetime | None:
    """라인에서 타임스탬프를 파싱합니다.

    ISO 8601 형식과 syslog 형식을 지원합니다.
    dateutil 없이 stdlib datetime만 사용합니다.
    실패 시 None 을 반환하며 에러는 발생시키지 않습니다.

    Args:
        line: 파싱할 로그 줄

    Returns:
        파싱된 datetime 객체, 또는 실패 시 None
    """
    # ISO 8601: extract timestamp from log line first
    m = re.search(
        r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)',
        line,
    )
    if m:
        ts_str = m.group(1)
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue

    # syslog: Apr  5 10:30:45
    _month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    m = re.search(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})',
        line,
    )
    if m:
        month = _month_map.get(m.group(1))
        if month:
            return datetime(
                2026, month, int(m.group(2)),
                int(m.group(3)), int(m.group(4)), int(m.group(5)),
            )

    return None
