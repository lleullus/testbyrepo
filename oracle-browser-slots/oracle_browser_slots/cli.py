"""Command-line entry point for independent Oracle Browser slots."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .allocator import AutoAllocator
from .followup import FollowupError, FollowupRunner, OracleSessionRepository
from .model import AVAILABLE, SLOT_IDS, Settings
from .runner import JobRunner
from .service import SlotService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oracle-browser-slots",
        description="Prepare and inspect the three fixed local Oracle Browser slots.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="prepare one explicitly selected slot")
    prepare.add_argument("--slot", type=int, choices=SLOT_IDS, required=True)

    status = commands.add_parser("status", help="show current state for one or all slots")
    status.add_argument("--slot", type=int, choices=SLOT_IDS)

    run = commands.add_parser("run", help="run one explicitly selected job in one slot")
    run.add_argument("--slot", type=int, choices=SLOT_IDS, required=True)
    run.add_argument("--job-id", required=True)
    run.add_argument("--opencode-conversation-id")
    run.add_argument("child_argv", nargs=argparse.REMAINDER)

    submit = commands.add_parser(
        "submit", help="submit one request to the first available slot or FIFO queue"
    )
    submit.add_argument("--request-id", required=True)
    submit.add_argument("--opencode-conversation-id")
    submit.add_argument("child_argv", nargs=argparse.REMAINDER)

    followup = commands.add_parser(
        "followup", help="continue one saved Oracle Browser conversation in its original slot"
    )
    followup.add_argument("--request-id", required=True)
    followup.add_argument("--opencode-conversation-id", required=True)
    followup.add_argument("--parent-session-id")
    followup.add_argument("child_argv", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    service = SlotService(settings)
    if args.command == "prepare":
        record = service.prepare(args.slot)
        print(
            json.dumps(
                {"operation": "prepare", "slot": record},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if record["status"] == AVAILABLE else 1

    if args.command == "status":
        if args.slot is None:
            payload = {"operation": "status", "slots": service.status_all()}
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        payload = {"operation": "status", "slot": service.status(args.slot)}
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    command = list(args.child_argv)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error(f"{args.command} requires a command after --")

    def emit(record: dict[str, object]) -> None:
        print(json.dumps(record, ensure_ascii=False, sort_keys=True), file=sys.stderr, flush=True)

    if args.command == "followup":
        result = FollowupRunner(service).run(
            args.request_id,
            args.opencode_conversation_id,
            command,
            parent_session_id=args.parent_session_id,
            emit=emit,
        )
        return int(result["exit_code"])

    context_id = args.opencode_conversation_id
    child_session_id: str | None = None
    repository: OracleSessionRepository | None = None
    if context_id is not None:
        repository = OracleSessionRepository(settings)
        try:
            context_id = repository.normalize_context_id(context_id)
            request_id = args.request_id if args.command == "submit" else args.job_id
            command, child_session_id = repository.prepare_new_run_command(command, request_id)
        except FollowupError as exc:
            emit(
                {
                    "operation": args.command,
                    "event": "rejected",
                    "outcome": "rejected",
                    "reason": exc.reason,
                    "operator_action": exc.operator_action,
                    "opencode_conversation_id": context_id,
                }
            )
            return 2

    if args.command == "submit":
        result = AutoAllocator(service).submit(args.request_id, command, emit=emit)
        request_id = args.request_id
        slot_id = result["record"].get("assigned_slot")
    else:
        result = JobRunner(service).run(args.slot, args.job_id, command, emit=emit)
        request_id = args.job_id
        slot_id = args.slot

    if (
        repository is not None
        and child_session_id is not None
        and result.get("accepted") is True
        and isinstance(slot_id, int)
    ):
        try:
            readback = repository.record_origin(
                child_session_id,
                context_id=context_id,
                slot_id=slot_id,
                request_id=request_id,
                operation=args.command,
                exit_code=int(result["exit_code"]),
            )
        except FollowupError as exc:
            emit(
                {
                    "operation": args.command,
                    "event": "session_registration_failed",
                    "outcome": "failed",
                    "request_id": request_id,
                    "child_session_id": child_session_id,
                    "opencode_conversation_id": context_id,
                    "reason": (
                        f"stock Oracle child 종료 후 OpenCode context 등록에 실패했습니다: "
                        f"{exc.reason} 프롬프트가 이미 제출되었을 수 있으므로 자동 재시도하지 않았습니다."
                    ),
                    "operator_action": exc.operator_action,
                    "prompt_submission_may_have_occurred": True,
                }
            )
            return int(result["exit_code"]) if int(result["exit_code"]) != 0 else 1
        emit(
            {
                "operation": args.command,
                "event": "session_registered",
                "outcome": "success",
                "request_id": request_id,
                "child_session_id": child_session_id,
                "opencode_conversation_id": context_id,
                "authoritative_readback": readback,
            }
        )
    return int(result["exit_code"])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
