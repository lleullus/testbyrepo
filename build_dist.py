#!/usr/bin/env python3
"""Build reproducible clean ZIP, runtime-only PYZ, and dated source archive."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import tarfile
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "logtrim"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
PYZ_MAIN = b"from logtrim.cli import main\nraise SystemExit(main())\n"


def version() -> str:
    namespace: dict[str, object] = {}
    exec((PACKAGE / "__init__.py").read_text(encoding="utf-8"), namespace)
    return str(namespace["__version__"])

def distribution_files() -> list[Path]:
    files = [
        ROOT / "README.md",
        ROOT / "USAGE_KO.md",
        ROOT / "pyproject.toml",
        ROOT / "trim.py",
        ROOT / "build_dist.py",
        ROOT / "benchmarks" / "differential.py",
        ROOT / "docs" / "architecture" / "ARCHITECTURE.md",
        ROOT / "tests" / "__init__.py",
        ROOT / "tests" / "test_logtrim.py",
    ]
    files.extend(PACKAGE.glob("*.py"))
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())

def source_files() -> list[Path]:
    return distribution_files()


def _zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ((0o100755 if executable else 0o100644) << 16)
    return info


def _write_zip_entries(target: Path, entries: list[tuple[str, bytes]], executable: set[str] = frozenset()) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, strict_timestamps=True) as archive:
        archive.comment = b""
        for name, content in sorted(entries, key=lambda entry: entry[0]):
            archive.writestr(_zip_info(name, name in executable), content,
                             compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_zip(target: Path, prefix: str, files: list[Path]) -> None:
    entries = [(f"{prefix}/{path.relative_to(ROOT).as_posix()}", path.read_bytes())
               for path in files]
    _write_zip_entries(target, entries)


def write_tar(target: Path, prefix: str, files: list[Path]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0,
                           compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
                    name = f"{prefix}/{path.relative_to(ROOT).as_posix()}"
                    info = tarfile.TarInfo(name)
                    info.size = path.stat().st_size
                    info.mode = 0o644
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    info.type = tarfile.REGTYPE
                    with path.open("rb") as source:
                        archive.addfile(info, source)


def write_pyz(target: Path) -> None:
    entries = [
        ("README.md", (ROOT / "README.md").read_bytes()),
        ("USAGE_KO.md", (ROOT / "USAGE_KO.md").read_bytes()),
        ("__main__.py", PYZ_MAIN),
    ]
    entries.extend((f"logtrim/{path.name}", path.read_bytes())
                   for path in sorted(PACKAGE.glob("*.py"), key=lambda item: item.name))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as output:
        output.write(b"#!/usr/bin/env python3\n")
        _write_zip_entries_to_stream(output, entries)
    os.chmod(target, 0o755)


def _write_zip_entries_to_stream(stream, entries: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, strict_timestamps=True) as archive:
        archive.comment = b""
        for name, content in sorted(entries, key=lambda entry: entry[0]):
            archive.writestr(_zip_info(name, name == "__main__.py"), content,
                             compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="..")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    try:
        archive_date = date.fromisoformat(args.date).isoformat()
    except ValueError:
        parser.error("--date must be an ISO-8601 calendar date (YYYY-MM-DD)")

    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"logtrim-{version()}"
    targets = [
        output_dir / f"{prefix}-clean.zip",
        output_dir / f"{prefix}-standalone.pyz",
        output_dir / f"{prefix}-source-{archive_date}.tar.gz",
    ]

    write_zip(targets[0], prefix, distribution_files())
    write_pyz(targets[1])
    write_tar(targets[2], prefix, source_files())
    manifest = output_dir / "SHA256SUMS"
    manifest.write_text("".join(f"{sha256(path)}  {path.name}\n"
                                 for path in sorted(targets, key=lambda item: item.name)),
                        encoding="ascii")
    for target in targets:
        print(f"{target.name}\t{target.stat().st_size}\t{sha256(target)}")
    print(f"{manifest.name}\t{manifest.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
