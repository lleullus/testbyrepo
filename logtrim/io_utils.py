"""I/O utilities for log trimmer.

Provides memory-efficient line iteration and output writing
for both file paths and stdin/stdout.
"""

from __future__ import annotations

import sys
from typing import Iterator


def iter_lines(path_or_stdin: str) -> Iterator[str]:
    """Yield lines from a file or stdin.

    Args:
        path_or_stdin: File path to read, or ``"-"`` for stdin.

    Yields:
        Lines including their trailing newline characters.
    """
    if path_or_stdin == "-":
        for line in sys.stdin:
            yield line
    else:
        with open(path_or_stdin, encoding="utf-8") as fh:
            for line in fh:
                yield line


def write_output(lines: Iterator[str], path: str) -> None:
    """Write lines to a file or stdout.

    Args:
        lines: Iterator yielding strings.
        path: File path to write to, or ``"-"`` for stdout.
    """
    if path == "-":
        for line in lines:
            sys.stdout.write(line)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line)
