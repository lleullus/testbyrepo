"""Tests for logtrim.io_utils."""

import io
import os
import tempfile
import unittest
from unittest.mock import patch

from logtrim.io_utils import iter_lines, write_output


class TestIterLinesFile(unittest.TestCase):
    """test_iter_lines_file — 임시 파일 생성 → iter_lines로 읽기 → 라인 수 확인."""

    def test_iter_lines_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            f.write("line1\nline2\nline3\n")
            tmp_path = f.name

        try:
            lines = list(iter_lines(tmp_path))
            self.assertEqual(lines, ["line1\n", "line2\n", "line3\n"])
        finally:
            os.unlink(tmp_path)

    def test_iter_lines_empty_file(self):
        """test_iter_lines_empty_file — 빈 파일 처리."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            tmp_path = f.name

        try:
            lines = list(iter_lines(tmp_path))
            self.assertEqual(lines, [])
        finally:
            os.unlink(tmp_path)

    def test_iter_lines_large_file(self):
        """test_iter_lines_large_file — 여러 라인 포함 파일."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            for i in range(1000):
                f.write(f"log entry {i}\n")
            tmp_path = f.name

        try:
            lines = list(iter_lines(tmp_path))
            self.assertEqual(len(lines), 1000)
            self.assertEqual(lines[0], "log entry 0\n")
            self.assertEqual(lines[999], "log entry 999\n")
        finally:
            os.unlink(tmp_path)


class TestIterLinesStdin(unittest.TestCase):
    """test_iter_lines_stdin — StringIO로 stdin 모킹 → iter_lines로 읽기."""

    def test_iter_lines_stdin(self):
        with patch("sys.stdin", io.StringIO("stdin line1\nstdin line2\n")):
            lines = list(iter_lines("-"))
            self.assertEqual(lines, ["stdin line1\n", "stdin line2\n"])

    def test_iter_lines_stdin_empty(self):
        with patch("sys.stdin", io.StringIO("")):
            lines = list(iter_lines("-"))
            self.assertEqual(lines, [])


class TestWriteOutputFile(unittest.TestCase):
    """test_write_output_file — write_output으로 파일에 쓰기 → 파일 내용 확인."""

    def test_write_output_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, encoding="utf-8"
        ) as f:
            tmp_path = f.name

        try:
            write_output(iter(["out1\n", "out2\n"]), tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "out1\nout2\n")
        finally:
            os.unlink(tmp_path)


class TestWriteOutputStdout(unittest.TestCase):
    """test_write_output_stdout — stdout 모킹 → write_output으로 쓰기."""

    def test_write_output_stdout(self):
        mock_stdout = io.StringIO()
        with patch("sys.stdout", mock_stdout):
            write_output(iter(["stdout1\n", "stdout2\n"]), "-")
            self.assertEqual(mock_stdout.getvalue(), "stdout1\nstdout2\n")


if __name__ == "__main__":
    unittest.main()
