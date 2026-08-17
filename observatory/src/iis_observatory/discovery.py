from __future__ import annotations

from pathlib import Path
import os

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
}


def has_iis_planning(repo: Path) -> bool:
    return (repo / "docs" / "planning").is_dir()


def is_git_repository(repo: Path) -> bool:
    """Return True when the path itself is a Git working tree or gitfile-backed repo."""
    dot_git = repo / ".git"
    return dot_git.is_dir() or dot_git.is_file()


def is_git_worktree(repo: Path) -> bool:
    """Return True when repo is a linked Git worktree, not a submodule."""
    dot_git = repo / ".git"
    if not dot_git.is_file():
        return False
    try:
        first_line = dot_git.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return False
    prefix = "gitdir:"
    if not first_line.lower().startswith(prefix):
        return False
    raw_target = first_line[len(prefix) :].strip()
    if not raw_target:
        return False
    target = Path(raw_target).expanduser()
    if not target.is_absolute():
        target = dot_git.parent / target
    # Linked worktrees use .../worktrees/<name>; submodules use .../modules/<name>.
    return target.resolve().parent.name == "worktrees"


def discover_repositories(
    root: Path,
    max_depth: int = 4,
    include_worktrees: bool = False,
) -> list[Path]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Discovery root does not exist: {root}")
    if root.is_file():
        raise NotADirectoryError(f"Discovery root is not a directory: {root}")

    found: set[Path] = set()
    if has_iis_planning(root) and is_git_repository(root):
        found.add(root)

    root_depth = len(root.parts)
    for current, dirs, _files in os.walk(root, followlinks=False):
        current_path = Path(current)
        depth = len(current_path.parts) - root_depth
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS and not name.startswith(".")]
        if current_path != root and not include_worktrees and is_git_worktree(current_path):
            # A linked worktree is a duplicate view of its parent project for portfolio purposes.
            dirs[:] = []
            continue
        if depth >= max_depth:
            dirs[:] = []
            continue
        planning = current_path / "docs" / "planning"
        if planning.is_dir():
            if current_path != root or is_git_repository(current_path):
                found.add(current_path.resolve())
            # Avoid traversing generated planning content while still allowing nested repos elsewhere.
            if "docs" in dirs:
                dirs.remove("docs")

    return sorted(found, key=lambda path: path.as_posix().lower())


def display_name(repo: Path, discovery_root: Path | None = None) -> str:
    if discovery_root is not None:
        try:
            relative = repo.resolve().relative_to(discovery_root.resolve())
            if relative.parts:
                return relative.as_posix()
        except ValueError:
            pass
    return repo.name
