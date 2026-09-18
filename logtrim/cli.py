"""CLI 오케스트레이션 모듈.

argparse 기반 CLI 진입점, 인자 파싱, 메인 로직 흐름 orchestration.

Flow: read → extract_pattern → group → format → write
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logtrim.grouping import group_logs
from logtrim.io_utils import iter_lines, write_output
from logtrim.report import format_output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 인자를 파싱합니다.

    Args:
        argv: 명령줄 인자 리스트. None이면 sys.argv[1:] 사용.

    Returns:
        파싱된 argparse.Namespace 객체.

    Raises:
        ValueError: threshold가 0.80~0.90 범위를 벗어나면.
    """
    parser = argparse.ArgumentParser(
        prog="logtrim",
        description="로그 줄을 패턴화하고 중복을 압축합니다.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="입력 파일 경로 또는 '-' (stdin, 기본값: '-')",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="-",
        help="출력 파일 경로 또는 '-' (stdout, 기본값: '-')",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="유사도 임계값 (0.80~0.90, 기본값: 0.85)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="출력 포맷 ('text' 또는 'json', 기본값: 'text')",
    )

    args = parser.parse_args(argv)

    if args.threshold < 0.80 or args.threshold > 0.90:
        raise ValueError(
            f"Invalid threshold: {args.threshold} (must be 0.80-0.90)"
        )

    return args


def run(
    input_path: str,
    output_path: str,
    threshold: float = 0.85,
    fmt: str = "text",
) -> int:
    """메인 로직: read → extract_pattern → group → format → write.

    Args:
        input_path: 입력 파일 경로 또는 "-" (stdin).
        output_path: 출력 파일 경로 또는 "-" (stdout).
        threshold: 유사도 임계값 (0.80~0.90).
        fmt: 출력 포맷 ("text" 또는 "json").

    Returns:
        종료 코드 (0=성공, 1=에러).

    Raises:
        FileNotFoundError: 입력 파일을 찾을 수 없으면.
        PermissionError: 파일에 접근 권한이 없으면.
        ValueError: threshold가 유효하지 않으면.
    """
    # threshold 검증
    if threshold < 0.80 or threshold > 0.90:
        raise ValueError(
            f"Invalid threshold: {threshold} (must be 0.80-0.90)"
        )

    # 1. 입력 라인 읽기
    raw_lines = list(iter_lines(input_path))
    original_count = len(raw_lines)

    # 2. 패턴 추출 및 그룹화 (group_logs 내부에서 extract_pattern 호출)
    groups = list(group_logs(iter(raw_lines), threshold=threshold))

    # 3. 요약 메타데이터 계산
    trimmed_count = len(groups)
    if original_count == 0:
        compression_ratio = 0.0
    else:
        compression_ratio = (1 - trimmed_count / original_count) * 100

    summary = {
        "original_count": original_count,
        "trimmed_count": trimmed_count,
        "compression_ratio": compression_ratio,
        "threshold": threshold,
    }

    # 4. LogPattern → dict 변환 (datetime → ISO string for JSON compatibility)
    patterns = []
    for g in groups:
        patterns.append({
            "pattern": g.pattern,
            "count": g.count,
            "sample": g.sample,
            "first_seen": g.first_seen.isoformat() if g.first_seen else None,
            "last_seen": g.last_seen.isoformat() if g.last_seen else None,
        })

    # 5. 출력 포맷팅
    output = format_output(summary, patterns, fmt=fmt)

    # 6. 출력 쓰기
    write_output(iter([output]), output_path)

    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점.

    인자 파싱 → run 실행 → 결과 반환. 모든 예외를 캐치하여
    exit code 1로 처리합니다.

    Args:
        argv: 명령줄 인자 리스트. None이면 sys.argv[1:] 사용.

    Returns:
        종료 코드 (0=성공, 1=에러).
    """
    try:
        args = parse_args(argv)
        return run(args.input, args.output, args.threshold, args.format)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
