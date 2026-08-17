from __future__ import annotations

import argparse
from pathlib import Path
import json
import os
import sys
from typing import Sequence

from .discovery import discover_repositories, display_name, is_git_repository
from .history import HistoryError, collect_history, render_history
from .model import Health, __version__
from .render import render_doctor, render_overview, render_overview_markdown, render_state
from .scanner import ScanOptions, scan_repository

COMMANDS = {"overview", "scan", "doctor", "history", "version", "-h", "--help"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iis-observatory",
        description="Read-only overview of IIS planning artifacts across repositories.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    overview = subparsers.add_parser("overview", help="Scan repositories and print the project overview.")
    overview.add_argument("root", nargs="?", default="~/project")
    overview.add_argument("--max-depth", type=int, default=4)
    overview.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    overview.add_argument("--lang", choices=("ko", "en"), default="ko")
    overview.add_argument("--no-color", action="store_true")
    overview.add_argument("--output", type=Path)
    overview.add_argument("--fail-on-inconsistent", action="store_true")
    overview.add_argument("--no-link-check", action="store_true")
    overview.add_argument(
        "--include-worktrees",
        action="store_true",
        help="Include linked Git worktrees in multi-repository discovery.",
    )

    scan = subparsers.add_parser("scan", help="Inspect one repository.")
    scan.add_argument("repository", nargs="?", default=".")
    scan.add_argument("--format", choices=("text", "json"), default="text")
    scan.add_argument("--lang", choices=("ko", "en"), default="ko")
    scan.add_argument("--no-color", action="store_true")
    scan.add_argument("--output", type=Path)
    scan.add_argument("--fail-on-inconsistent", action="store_true")
    scan.add_argument("--no-link-check", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Report planning-artifact inconsistencies.")
    doctor.add_argument("root", nargs="?", default="~/project")
    doctor.add_argument("--max-depth", type=int, default=4)
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--no-link-check", action="store_true")
    doctor.add_argument(
        "--include-worktrees",
        action="store_true",
        help="Include linked Git worktrees in multi-repository discovery.",
    )

    history = subparsers.add_parser("history", help="Show Git history for docs/planning.")
    history.add_argument("repository", nargs="?", default=".")
    history.add_argument("--limit", type=int, default=20)
    history.add_argument("--json", action="store_true")

    subparsers.add_parser("version", help="Print the installed version.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    if not raw:
        raw = ["overview"]
    elif raw[0] not in COMMANDS and not raw[0].startswith("-"):
        raw = ["overview", *raw]

    parser = build_parser()
    args = parser.parse_args(raw)
    command = args.command or "overview"
    try:
        if command == "overview":
            return _overview(args)
        if command == "scan":
            return _scan(args)
        if command == "doctor":
            return _doctor(args)
        if command == "history":
            return _history(args)
        if command == "version":
            print(__version__)
            return 0
    except (FileNotFoundError, NotADirectoryError, PermissionError) as exc:
        print(f"iis-observatory: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


def _overview(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    repos = discover_repositories(
        root,
        max_depth=args.max_depth,
        include_worktrees=args.include_worktrees,
    )
    options = ScanOptions(check_links=not args.no_link_check)
    states = [
        scan_repository(repo, repository_name=display_name(repo, root), options=options)
        for repo in repos
    ]
    states.sort(key=lambda state: (_health_rank(state.health), state.repository.lower()))
    if args.format == "json":
        output = json.dumps(
            {
                "schema_version": "1.0",
                "root": str(root),
                "projects": [state.to_dict() for state in states],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    elif args.format == "markdown":
        output = render_overview_markdown(states, lang=args.lang)
    else:
        color = sys.stdout.isatty() and not args.no_color and args.output is None
        output = render_overview(states, lang=args.lang, color=color)
    _emit(output, args.output)
    if args.fail_on_inconsistent and any(state.health == Health.INCONSISTENT for state in states):
        return 3
    return 0


def _scan(args: argparse.Namespace) -> int:
    repo = Path(args.repository).expanduser().resolve()
    state = scan_repository(repo, options=ScanOptions(check_links=not args.no_link_check))
    if args.format == "json":
        output = json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n"
    else:
        color = sys.stdout.isatty() and not args.no_color and args.output is None
        output = render_state(state, lang=args.lang, color=color)
    _emit(output, args.output)
    if args.fail_on_inconsistent and state.health == Health.INCONSISTENT:
        return 3
    return 0 if state.planning_root else 4


def _doctor(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if (root / "docs" / "planning").is_dir() and is_git_repository(root):
        repos = [root]
    else:
        repos = discover_repositories(
            root,
            max_depth=args.max_depth,
            include_worktrees=args.include_worktrees,
        )
    states = [
        scan_repository(
            repo,
            repository_name=display_name(repo, root),
            options=ScanOptions(check_links=not args.no_link_check),
        )
        for repo in repos
    ]
    if args.json:
        output = json.dumps(
            {
                "projects": [
                    {
                        "repository": state.repository,
                        "health": state.health.value,
                        "issues": [issue.to_dict() for issue in state.issues],
                    }
                    for state in states
                ]
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    else:
        output = render_doctor(states)
    print(output, end="")
    return 3 if any(state.has_errors for state in states) else 0


def _history(args: argparse.Namespace) -> int:
    try:
        events = collect_history(Path(args.repository), limit=max(1, args.limit))
    except HistoryError as exc:
        print(f"iis-observatory history: {exc}", file=sys.stderr)
        return 5
    if args.json:
        print(json.dumps([event.to_dict() for event in events], ensure_ascii=False, indent=2))
    else:
        print(render_history(events), end="")
    return 0


def _health_rank(health: Health) -> int:
    order = {
        Health.INCONSISTENT: 0,
        Health.BLOCKED: 1,
        Health.READY: 2,
        Health.PLANNING: 3,
        Health.NEEDS_SCOPE: 4,
        Health.STALE: 5,
        Health.COMPLETE: 6,
        Health.NO_IIS: 7,
    }
    return order[health]


def _emit(output: str, destination: Path | None) -> None:
    if destination is None:
        print(output, end="")
        return
    destination = destination.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
