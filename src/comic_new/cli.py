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

    # comic-new init <project_dir> [--cut-count N]
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new comic-new project directory with N dynamic cuts",
    )
    init_parser.add_argument("project_dir", type=str, help="Path to the empty project directory")
    init_parser.add_argument("--cut-count", type=int, default=5, help="Initial active cut count (positive integer)")
    # comic-new snapshot <project_dir>
    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Read authoritative snapshot from a comic-new project database as JSON",
    )
    snapshot_parser.add_argument("project_dir", type=str, help="Path to the project directory")


    # comic-new generate <project_dir> [--cut N]
    gen_parser = subparsers.add_parser(
        "generate",
        help="Enqueue and run image generation for all active cuts or a single cut",
    )
    gen_parser.add_argument("project_dir", type=str, help="Path to the project directory")
    gen_parser.add_argument(
        "--cut",
        type=int,
        default=None,
        help="Single positive cut_id to generate (defaults to all active cuts)",
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


    # comic-new export-png <project_dir> <output_file>
    export_parser = subparsers.add_parser(
        "export-png",
        help="Export approved canonical review artifact to a standalone PNG file without reflow",
    )
    export_parser.add_argument("project_dir", type=str, help="Path to the project directory")
    export_parser.add_argument("output_file", type=str, help="Target path for the exported PNG file")

    # comic-new release-blogger <project_dir> [--blog-id <id>] [--title <title>]
    blogger_parser = subparsers.add_parser(
        "release-blogger",
        help="Publish approved comic to Blogger with destination readback",
    )
    blogger_parser.add_argument("project_dir", type=str, help="Path to the project directory")
    blogger_parser.add_argument("--blog-id", type=str, default=None, help="Blogger blog ID")
    blogger_parser.add_argument("--title", type=str, default=None, help="Post title")
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
            store = TransactionalStore.create_project(p, cut_count=args.cut_count)
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
        elif args.command == "export-png":
            from comic_new.delivery import DeliveryService
            from comic_new.composition import CANONICAL_WIDTH
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            snap = store.snapshot()
            delivery_svc = DeliveryService(store)
            dest_file = Path(args.output_file).resolve()
            try:
                result = delivery_svc.export_png(snap["authority_revision"], output_path=dest_file)
                output = {
                    "status": "success",
                    "attempt_id": result.attempt_id,
                    "authorization_id": result.authorization_id,
                    "artifact_id": result.artifact_id,
                    "output_file": str(dest_file),
                    "content_hash": result.content_hash,
                    "bytes_written": result.bytes_written,
                    "dimensions": [result.evidence.get("width", CANONICAL_WIDTH), result.evidence.get("height")],
                }
                print(json.dumps(output, indent=2))
                return 0
            except Exception as exc:
                sys.stderr.write(f"export-png error: {exc}\n")
                return 1
        elif args.command == "release-blogger":
            from comic_new.delivery import DeliveryService
            p = Path(args.project_dir)
            store = TransactionalStore.open_project(p)
            snap = store.snapshot()
            delivery_svc = DeliveryService(store)
            try:
                result = delivery_svc.deliver_blogger(
                    snap["authority_revision"],
                    blog_id=args.blog_id,
                    title=args.title,
                )
                if result.outcome == "confirmed_success":
                    output = {
                        "status": "confirmed_success",
                        "attempt_id": result.attempt_id,
                        "authorization_id": result.authorization_id,
                        "post_id": result.destination_id,
                        "destination_url": result.destination_url,
                    }
                    print(json.dumps(output, indent=2))
                    return 0
                elif result.outcome == "unknown":
                    output = {
                        "status": "unknown",
                        "attempt_id": result.attempt_id,
                        "message": "발행 결과 미확인: 외부 서비스 응답 타임아웃",
                    }
                    print(json.dumps(output, indent=2))
                    return 1
                else:
                    output = {
                        "status": "confirmed_failure",
                        "attempt_id": result.attempt_id,
                        "evidence": result.evidence,
                    }
                    print(json.dumps(output, indent=2))
                    return 1
            except Exception as exc:
                sys.stderr.write(f"release-blogger error: {exc}\n")
                return 1
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
