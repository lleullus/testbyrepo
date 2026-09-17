from __future__ import annotations

import argparse
import os
import tempfile
import sys
from pathlib import Path

from .pipeline import process_stream


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline log trimming utility.")
    parser.add_argument("--input", default="input.txt", help="Input file path.")
    parser.add_argument("--output", default="output.txt", help="Output file path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 2

    temp_path: Path | None = None
    try:
        with input_path.open("r", encoding="utf-8") as input_file:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=output_path.parent,
                prefix=f"{output_path.name}.",
                suffix=".tmp",
            ) as temp_file:
                temp_path = Path(temp_file.name)
                stream = iter(process_stream(input_file))
                first_chunk = next(stream, None)
                if first_chunk is None:
                    pass
                else:
                    second_chunk = next(stream, None)
                    if second_chunk is None and first_chunk.startswith("Generic Text\n"):
                        temp_file.write(first_chunk[len("Generic Text\n") :])
                    else:
                        temp_file.write(first_chunk)
                        if second_chunk is not None:
                            temp_file.write(second_chunk)
                        for chunk in stream:
                            temp_file.write(chunk)
        os.replace(temp_path, output_path)
    except Exception as exc:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        print(f"error: processing failed: {exc}", file=sys.stderr)
        return 1

    return 0
