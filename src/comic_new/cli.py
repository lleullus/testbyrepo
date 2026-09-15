"""comic-new CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from comic_new.generation import GenerationRunner, GenerationService
from comic_new.server import ServerPreflightError, serve
from comic_new.store import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    RunnerAlreadyActiveError,
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


    # comic-new generate <project_dir> [--cut {1,2,3,4,5}]
    gen_parser = subparsers.add_parser(
        "generate",
        help="Enqueue and run image generation for all cuts or a single cut",
    )
    gen_parser.add_argument("project_dir", type=str, help="Path to the project directory")
    gen_parser.add_argument(
        "--cut",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help="Single cut_id to generate (defaults to all 1..5)",
    )

    # comic-new run-generation <project_dir>
    run_parser = subparsers.add_parser(
        "run-generation",
        help="Drain existing queued generation jobs using single runner with startup recovery",
    )
    run_parser.add_argument("project_dir", type=str, help="Path to the project directory")

    # comic-new cancel-generation <project_dir> <job_id>
    cancel_parser = subparsers.add_parser(
        "cancel-generation",
        help="Cancel a queued or running generation job",
    )
    cancel_parser.add_argument("project_dir", type=str, help="Path to the project directory")
    cancel_parser.add_argument("job_id", type=str, help="Job ID to cancel")

    # comic-new stop-generation <project_dir>
    stop_parser = subparsers.add_parser(
        "stop-generation",
        help="Stop all active generation jobs and cancel queued ones (global stop)",
    )
    stop_parser.add_argument("project_dir", type=str, help="Path to the project directory")

    # comic-new serve <project_dir> --font <absolute-font-file>
    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve the generated production Studio and same-origin API from one Python process",
    )
    serve_parser.add_argument("project_dir", type=str, help="Path to the project directory")
    serve_parser.add_argument(
        "--font",
        required=True,
        type=str,
        help="Absolute path to the canonical TrueType/OpenType font file",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Listen host")
    serve_parser.add_argument("--port", type=int, default=8000, help="Listen port")
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
        elif args.command == "generate":
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            snap = store.snapshot()
            service = GenerationService(store)
            enq_receipt = service.enqueue(
                cut_id=args.cut,
                expected_authority_revision=snap["authority_revision"],
            )
            runner = GenerationRunner(store)
            run_receipt = runner.run_until_idle()
            result = {
                "enqueue": enq_receipt.to_dict(),
                "run": run_receipt.to_dict(),
            }
            print(json.dumps(result, indent=2))
            # Nonzero exit if any job was failed/cancelled/interrupted/superseded
            bad_counts = sum(
                count
                for st, count in run_receipt.terminal_counts.items()
                if st in ("failed", "cancelled", "interrupted", "superseded")
            )
            return 1 if bad_counts > 0 else 0
        elif args.command == "run-generation":
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            runner = GenerationRunner(store)
            run_receipt = runner.run_until_idle()
            print(json.dumps(run_receipt.to_dict(), indent=2))
            bad_counts = sum(
                count
                for st, count in run_receipt.terminal_counts.items()
                if st in ("failed", "cancelled", "interrupted", "superseded")
            )
            return 1 if bad_counts > 0 else 0
        elif args.command == "cancel-generation":
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            service = GenerationService(store)
            receipt = service.cancel(args.job_id)
            print(json.dumps(receipt.to_dict(), indent=2))
            return 0
        elif args.command == "stop-generation":
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            service = GenerationService(store)
            receipt = service.stop_all()
            print(json.dumps(receipt.to_dict(), indent=2))
            return 0
        elif args.command == "serve":
            if not 1 <= args.port <= 65535:
                raise ValidationError("port must be between 1 and 65535")
            serve(
                project_dir=Path(args.project_dir),
                font_path=Path(args.font),
                host=args.host,
                port=args.port,
            )
            return 0
        else:
            parser.print_help(sys.stderr)
            return 2
    except (
        ProjectAlreadyExistsError,
        ProjectNotFoundError,
        StoreCorruptionError,
        RunnerAlreadyActiveError,
        ValidationError,
        TransactionalStoreError,
        ServerPreflightError,
    ) as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
