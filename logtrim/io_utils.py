"""Bounded records, compression-aware input and atomic output."""
from __future__ import annotations

import bz2
import gzip
import lzma
import os
import re
import sys
import tempfile
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

from .models import Config, Event, ResourceLimit
from .patterns import EXCEPTION, ISO, KLOG, SYSLOG

CONTINUATION = re.compile(r"^(?:\s+|Caused by:|Suppressed:|During handling of|The above exception|\.\.\. \d+ more)")


def iter_lines(path_or_stdin: str, config: Config | None = None,
               stats: Counter | None = None, encoding: str = "utf-8",
               errors: str = "strict"):
    config = config or Config()
    stats = stats if stats is not None else Counter()
    if errors not in {"strict", "replace"}:
        raise ValueError("decode errors must be strict or replace")
    with ExitStack() as stack:
        if path_or_stdin == "-":
            stream = getattr(sys.stdin, "buffer", sys.stdin)
        else:
            raw = stack.enter_context(open(path_or_stdin, "rb"))
            magic = raw.read(6)
            raw.seek(0)
            opener = gzip.GzipFile if magic.startswith(b"\x1f\x8b") else (
                bz2.BZ2File if magic.startswith(b"BZh") else (
                    lzma.LZMAFile if magic.startswith(b"\xfd7zXZ\x00") else None))
            stream = stack.enter_context(gzip.GzipFile(fileobj=raw) if opener is gzip.GzipFile
                                         else opener(raw)) if opener else raw
        while True:
            chunk = stream.readline(config.max_event_bytes + 1)
            if not chunk:
                break
            size = len(chunk.encode("utf-8")) if isinstance(chunk, str) else len(chunk)
            stats["input_bytes"] += size
            if size > config.max_event_bytes:
                raise ResourceLimit("physical line exceeds max_event_bytes")
            if config.max_input_bytes and stats["input_bytes"] > config.max_input_bytes:
                raise ResourceLimit("decompressed input exceeds max_input_bytes")
            if isinstance(chunk, bytes):
                try:
                    chunk = chunk.decode(encoding, errors="strict")
                except UnicodeDecodeError:
                    stats["decode_error_lines"] += 1
                    if errors == "strict":
                        raise
                    chunk = chunk.decode(encoding, errors="replace")
            yield chunk


def assemble(lines, config: Config, stats: Counter):
    """Conservative, single-source multiline state machine; EOF always flushes."""
    pending, size, trace = [], 0, False
    for raw in lines:
        stats["physical_lines"] += 1
        line = raw.rstrip("\r\n")
        if not line.strip():
            stats["blank_lines"] += 1
            continue
        nbytes = len(line.encode("utf-8"))
        if nbytes > config.max_event_bytes:
            raise ResourceLimit("physical line exceeds max_event_bytes")
        header = bool(ISO.match(line.lstrip()) or SYSLOG.match(line.lstrip())
                      or KLOG.match(line.lstrip()) or line.lstrip().startswith("{"))
        traceback = line.startswith("Traceback (most recent call last):")
        continuation = bool(pending and config.multiline and not header and (
            CONTINUATION.match(line) or (trace and EXCEPTION.match(line)) or
            (traceback and (re.search(r"(?i)\b(error|exception|fatal)\b", pending[0]) or
                            pending[-1].startswith(("During handling of", "The above exception"))))))
        if pending and not continuation:
            yield Event("\n".join(pending), len(pending))
            pending, size, trace = [], 0, False
        extra = nbytes + bool(pending)
        if size + extra > config.max_event_bytes or len(pending) >= config.max_event_lines:
            raise ResourceLimit("multiline event exceeds configured limits")
        pending.append(line)
        size += extra
        if traceback:
            trace = True
        elif trace and EXCEPTION.match(line):
            trace = False
    if pending:
        yield Event("\n".join(pending), len(pending))


def ensure_distinct(inputs, output: str):
    if output == "-":
        return
    target = Path(output).resolve()
    for source in inputs:
        if source == "-":
            continue
        path = Path(source)
        if path.resolve() == target or (path.exists() and target.exists()
                                       and os.path.samefile(path, target)):
            raise ValueError("input and output must be different files")


def write_output(chunks, path: str):
    if path == "-":
        for chunk in chunks:
            sys.stdout.write(chunk)
        sys.stdout.flush()
        return
    target = Path(path).absolute()
    fd, temporary = tempfile.mkstemp(prefix=".logtrim-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            for chunk in chunks:
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)