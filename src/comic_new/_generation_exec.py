#!/usr/bin/env python3
"""Launcher for generation subprocesses with parent-death safety and attach gate."""

from __future__ import annotations

import ctypes
import os
import signal
import sys


def set_pdeathsig() -> None:
    """Set PR_SET_PDEATHSIG to SIGTERM so child dies if parent terminates unexpectedly."""
    pr_set_pdeathsig = 1
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.prctl(pr_set_pdeathsig, signal.SIGTERM)
    except Exception:
        pass


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: _generation_exec.py <gate_fd> <cmd> [args...]", file=sys.stderr)
        sys.exit(1)

    try:
        gate_fd = int(sys.argv[1])
    except ValueError:
        print(f"Invalid gate_fd: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[2]
    cmd_args = sys.argv[2:]

    # Ensure parent-death signal is registered
    set_pdeathsig()

    # Block on the start gate until parent confirms DB attachment
    try:
        gate_byte = os.read(gate_fd, 1)
        if gate_byte != b"\x01":
            # Parent aborted or pipe closed without gate byte
            sys.exit(101)
    except Exception:
        sys.exit(102)
    finally:
        try:
            os.close(gate_fd)
        except OSError:
            pass

    # Gate passed: exec the target provider command
    os.execvp(cmd, cmd_args)


if __name__ == "__main__":
    main()
