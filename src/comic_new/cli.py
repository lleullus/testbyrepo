"""comic-new CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from comic_new.store import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    StoreCorruptionError,
    TransactionalStore,
    TransactionalStoreError,
    ValidationError,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="comic-new",
        description="Web Comic Studio - Single Transactional Authority CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # comic-new init <project_dir>
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new comic-new project directory with exact five-cut transactional store",
    )
    init_parser.add_argument("project_dir", type=str, help="Path to the empty project directory")

    # comic-new snapshot <project_dir>
    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Read authoritative snapshot from a comic-new project database as JSON",
    )
    snapshot_parser.add_argument("project_dir", type=str, help="Path to the project directory")

    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            p = Path(args.project_dir)
            store = TransactionalStore.create_project(p)
            print(f"Initialized comic-new project at {store.db_path.parent}")
            return 0
        elif args.command == "snapshot":
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            snap = store.snapshot()
            print(json.dumps(snap, indent=2))
            return 0
        else:
            parser.print_help(sys.stderr)
            return 2
    except (
        ProjectAlreadyExistsError,
        ProjectNotFoundError,
        StoreCorruptionError,
        ValidationError,
        TransactionalStoreError,
    ) as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
