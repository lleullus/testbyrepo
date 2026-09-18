"""Tests for logtrim.cli — CLI 오케스트레이션 모듈.

TDD 방식으로 작성: 테스트 먼저 → 구현 → 통과 확인.
"""

import io
import sys
import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

from logtrim.cli import parse_args, run, main


# ===================================================================
# parse_args 테스트
# ===================================================================

class TestParseArgs(unittest.TestCase):
    """parse_args — argparse 인자 파싱 검증."""

    def test_parse_args_defaults(self):
        """test_parse_args_defaults — 인자 없이 호출 시 디폴트값 확인."""
        args = parse_args([])
        self.assertEqual(args.input, "-")
        self.assertEqual(args.output, "-")
        self.assertEqual(args.threshold, 0.85)
        self.assertEqual(args.format, "text")

    def test_parse_args_custom(self):
        """test_parse_args_custom — 커스텀 인자 확인."""
        args = parse_args([
            "input.log",
            "output.txt",
            "--threshold", "0.90",
            "--format", "json",
        ])
        self.assertEqual(args.input, "input.log")
        self.assertEqual(args.output, "output.txt")
        self.assertEqual(args.threshold, 0.90)
        self.assertEqual(args.format, "json")

    def test_parse_args_invalid_threshold(self):
        """test_parse_args_invalid_threshold — invalid threshold → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parse_args(["--threshold", "0.50"])
        self.assertIn("threshold", str(ctx.exception).lower())


# ===================================================================
# run 테스트
# ===================================================================

class TestRun(unittest.TestCase):
    """run — 메인 로직 검증."""

    def test_run_basic(self):
        """test_run_basic — 기본 실행 (임시 파일 생성 → 실행 → 출력 확인)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("2024-01-15T10:30:45.123Z server started\n")
            f.write("2024-01-15T10:30:46.123Z server started\n")
            f.write("2024-01-15T10:30:47.123Z server started\n")
            input_path = f.name

        output_path = input_path + ".out"

        try:
            exit_code = run(input_path, output_path)
            self.assertEqual(exit_code, 0)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Log Trimmer Output", content)
            self.assertIn("# input_lines=3", content)
            self.assertIn("# grouped_patterns=1", content)
            self.assertIn("<TIMESTAMP>", content)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_run_with_threshold(self):
        """test_run_with_threshold — 커스텀 threshold 실행."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("event alpha\n")
            f.write("event alpha\n")
            f.write("event beta\n")
            input_path = f.name

        output_path = input_path + ".out"

        try:
            exit_code = run(input_path, output_path, threshold=0.90)
            self.assertEqual(exit_code, 0)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Log Trimmer Output", content)
            self.assertIn("threshold=0.9", content)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_run_json_output(self):
        """test_run_json_output — JSON 출력 확인."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("server started\n")
            f.write("server started\n")
            f.write("server stopped\n")
            input_path = f.name

        output_path = input_path + ".out"

        try:
            exit_code = run(input_path, output_path, fmt="json")
            self.assertEqual(exit_code, 0)

            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("original_count", data)
            self.assertIn("trimmed_count", data)
            self.assertIn("compression_ratio", data)
            self.assertIn("patterns", data)
            self.assertEqual(data["original_count"], 3)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_run_stdin(self):
        """test_run_stdin — stdin 입력 ('-')."""
        input_content = "stdin log line 1\nstdin log line 2\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".out", delete=False, encoding="utf-8"
        ) as f:
            output_path = f.name

        try:
            with patch("sys.stdin", io.StringIO(input_content)):
                exit_code = run("-", output_path)

            self.assertEqual(exit_code, 0)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Log Trimmer Output", content)
        finally:
            os.unlink(output_path)

    def test_run_stdout(self):
        """test_run_stdout — stdout 출력 ('-')."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("stdout test line 1\n")
            f.write("stdout test line 2\n")
            input_path = f.name

        try:
            mock_stdout = io.StringIO()
            with patch("sys.stdout", mock_stdout):
                exit_code = run(input_path, "-")

            self.assertEqual(exit_code, 0)

            output = mock_stdout.getvalue()
            self.assertIn("# Log Trimmer Output", output)
        finally:
            os.unlink(input_path)

    def test_run_file_not_found(self):
        """test_run_file_not_found — 파일 없음 → FileNotFoundError."""
        with self.assertRaises(FileNotFoundError) as ctx:
            run("/nonexistent/path/input.log", "/tmp/output.log")
        self.assertIn("No such file", str(ctx.exception))

    def test_run_permission_denied(self):
        """test_run_permission_denied — 권한 없음 → PermissionError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("test line\n")
            input_path = f.name

        try:
            os.chmod(input_path, stat.S_IWUSR)

            with self.assertRaises(PermissionError):
                run(input_path, "/tmp/output.log")
        finally:
            os.chmod(input_path, stat.S_IRUSR | stat.S_IWUSR)
            os.unlink(input_path)


# ===================================================================
# main 테스트
# ===================================================================

class TestMain(unittest.TestCase):
    """main — CLI 진입점 검증."""

    def test_main_success(self):
        """test_main_success — main() 정상 실행 → exit code 0."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("main test line\n")
            input_path = f.name

        output_path = input_path + ".out"

        try:
            exit_code = main([input_path, output_path])
            self.assertEqual(exit_code, 0)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_main_error(self):
        """test_main_error — main() 에러 실행 → exit code 1."""
        exit_code = main(["/nonexistent/path/input.log", "/tmp/output.log"])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()


# ===================================================================
# 통합 테스트 — K8s 시스템 로그
# ===================================================================

K8S_KUBELET_SAMPLE = """\
2026-04-24T10:00:01Z kubelet[1234]: Started container 550e8400-e29b-41d4-a716-446655440000 in pod web-abcde on node ip-10-0-1-5
2026-04-24T10:00:02Z kubelet[1234]: Started container 550e8400-e29b-41d4-a716-446655440001 in pod web-fghij on node ip-10-0-1-6
2026-04-24T10:00:03Z kubelet[5678]: Failed pulling image registry.k8s.io/pause:3.9 for pod dns-xyz on node ip-10-0-1-7
2026-04-24T10:00:04Z kubelet[5678]: Failed pulling image registry.k8s.io/pause:3.8 for pod dns-abc on node ip-10-0-1-8
Apr 24 10:00:05 node kubelet[999]: Back-off restarting failed container myapp-7f9c8d in pod app-xyz_123
Apr 24 10:00:06 node kubelet[998]: Back-off restarting failed container myapp-7f9c8e in pod app-abc_456
2026-04-24T10:00:07Z containerd[111]: Pulling image 10.2.3.4:5000/app:v1 for pod web-def on node ip-10-0-1-9
2026-04-24T10:00:08Z containerd[111]: Pulling image 10.2.3.4:5000/app:v2 for pod web-ghi on node ip-10-0-1-10
"""


class TestIntegrationK8sLogs(unittest.TestCase):
    """통합 테스트 — K8s 시스템 로그 샘플 3종."""

    def test_integration_k8s_logs(self):
        """test_integration_k8s_logs — K8s 샘플 로그 → 압축률 검증."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write(K8S_KUBELET_SAMPLE)
            input_path = f.name

        output_path = input_path + ".out"

        try:
            exit_code = run(input_path, output_path)
            self.assertEqual(exit_code, 0)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Log Trimmer Output", content)
            self.assertIn("# input_lines=8", content)
            self.assertIn("# grouped_patterns=", content)
            self.assertIn("<TIMESTAMP>", content)
            self.assertIn("<UUID>", content)
            self.assertIn("<IPV4>", content)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_integration_compression_ratio(self):
        """test_integration_compression_ratio — 압축률 > 0 확인."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write(K8S_KUBELET_SAMPLE)
            input_path = f.name

        output_path = input_path + ".out"

        try:
            exit_code = run(input_path, output_path, fmt="json")
            self.assertEqual(exit_code, 0)

            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertGreater(data["compression_ratio"], 0.0)
            self.assertGreater(data["original_count"], 0)
            self.assertLessEqual(data["trimmed_count"], data["original_count"])
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_integration_cli_command(self):
        """test_integration_cli_command — python trim.py input.txt output.txt 실제 실행."""
        import subprocess

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write(K8S_KUBELET_SAMPLE)
            input_path = f.name

        output_path = input_path + ".out"

        try:
            result = subprocess.run(
                [sys.executable, "trim.py", input_path, output_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            )
            self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")

            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Log Trimmer Output", content)
            self.assertIn("# input_lines=8", content)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    unittest.main()
