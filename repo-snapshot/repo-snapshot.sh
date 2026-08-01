#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOKEN_FILE="${REPO_SNAPSHOT_TOKEN_FILE:-${XDG_CONFIG_HOME:-$HOME/.config}/repo-snapshot/token}"
REMOTE_HTTPS="${REPO_SNAPSHOT_REMOTE:-https://github.com/lleullus/testbyrepo.git}"
REMOTE_WEB="${REPO_SNAPSHOT_WEB:-https://github.com/lleullus/testbyrepo}"
BASE_DIR="${REPO_SNAPSHOT_BASE:-/tmp/oracle-snapshots}"

SOURCE=""
TASK=""
SLUG=""

usage() {
  cat <<'EOF'
Usage: repo-snapshot.sh [SOURCE_PATH] [--task TEXT] [--slug NAME]

Creates a full local copy of a git repo (including .git and working tree),
pushes it to snapshot/<slug> on the snapshot remote, and writes:
  /tmp/oracle-snapshots/<slug>/snapshot.json
  /tmp/oracle-snapshots/<slug>/oracle-prompt.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --task)
      TASK="${2:-}"
      shift 2
      ;;
    --slug)
      SLUG="${2:-}"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      exit 2
      ;;
    *)
      if [[ -z "$SOURCE" ]]; then
        SOURCE="$1"
        shift
      else
        echo "unexpected argument: $1" >&2
        exit 2
      fi
      ;;
  esac
done

SOURCE="${SOURCE:-.}"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "token file not found: $TOKEN_FILE" >&2
  exit 1
fi

TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
if [[ -z "$TOKEN" ]]; then
  echo "token file is empty: $TOKEN_FILE" >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi
if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

SOURCE="$(cd "$SOURCE" && pwd)"
if ! git -C "$SOURCE" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "not a git repository: $SOURCE" >&2
  exit 1
fi

SRC_ROOT="$(git -C "$SOURCE" rev-parse --show-toplevel)"
SOURCE_HEAD="$(git -C "$SRC_ROOT" rev-parse HEAD 2>/dev/null || true)"
SOURCE_BRANCH="$(git -C "$SRC_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)"

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

if [[ -z "$SLUG" ]]; then
  SLUG="$(slugify "$(basename "$SRC_ROOT")")"
fi
if [[ -z "$SLUG" ]]; then
  echo "could not derive slug" >&2
  exit 1
fi

BRANCH="snapshot/${SLUG}"
WORKDIR="${BASE_DIR}/${SLUG}"
REPO_DIR="${WORKDIR}/repo"
AUTH_REMOTE="https://x-access-token:${TOKEN}@github.com/lleullus/testbyrepo.git"

rm -rf "$WORKDIR"
mkdir -p "$REPO_DIR"
rsync -a "$SRC_ROOT"/ "$REPO_DIR"/

git -C "$REPO_DIR" remote | while read -r remote_name; do
  git -C "$REPO_DIR" remote remove "$remote_name" >/dev/null 2>&1 || true
done
git -C "$REPO_DIR" remote add origin "$REMOTE_HTTPS"

if [[ -z "$(git -C "$REPO_DIR" config --get user.name || true)" ]]; then
  git -C "$REPO_DIR" config user.name "repo-snapshot"
fi
if [[ -z "$(git -C "$REPO_DIR" config --get user.email || true)" ]]; then
  git -C "$REPO_DIR" config user.email "repo-snapshot@local"
fi

if [[ -n "$(git -C "$REPO_DIR" status --porcelain)" ]]; then
  git -C "$REPO_DIR" add -A
  git -C "$REPO_DIR" commit -m "repo-snapshot: include working tree $(date -u +%Y-%m-%dT%H:%M:%SZ)"
fi

COMMIT_SHA="$(git -C "$REPO_DIR" rev-parse HEAD)"
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

ensure_main_placeholder() {
  local refs
  refs="$(GIT_TERMINAL_PROMPT=0 git ls-remote --heads "$AUTH_REMOTE" 2>/dev/null || true)"
  if printf '%s\n' "$refs" | grep -E 'refs/heads/main$' >/dev/null 2>&1; then
    return 0
  fi
  if [[ -n "$refs" ]]; then
    return 0
  fi

  local tmp
  tmp="$(mktemp -d /tmp/repo-snapshot-main.XXXXXX)"
  git -C "$tmp" init -b main >/dev/null
  git -C "$tmp" config user.name "repo-snapshot"
  git -C "$tmp" config user.email "repo-snapshot@local"
  printf '%s\n' '# repo-snapshots' 'Placeholder main branch. Snapshot content lives on snapshot/<repo-slug> branches.' > "$tmp/README.md"
  git -C "$tmp" add README.md
  git -C "$tmp" commit -m "chore: initialize empty main placeholder" >/dev/null
  GIT_TERMINAL_PROMPT=0 git -C "$tmp" push "$AUTH_REMOTE" "HEAD:refs/heads/main"
  rm -rf "$tmp"
}

ensure_main_placeholder

GIT_TERMINAL_PROMPT=0 git -C "$REPO_DIR" push --force "$AUTH_REMOTE" "HEAD:refs/heads/${BRANCH}"

COMMIT_URL="${REMOTE_WEB}/commit/${COMMIT_SHA}"
BRANCH_URL="${REMOTE_WEB}/tree/${BRANCH}"

TASK_TEXT="$TASK"
if [[ -z "$TASK_TEXT" ]]; then
  TASK_TEXT="Review this repository snapshot."
fi

export SNAPSHOT_URL="$REMOTE_WEB"
export COMMIT_URL
export COMMIT_SHA
export BRANCH
export BRANCH_URL
export SOURCE_PATH="$SRC_ROOT"
export SOURCE_HEAD
export SOURCE_BRANCH
export CREATED_AT
export WORKDIR
export TASK_TEXT

python3 - <<'PY'
import json
import os
from pathlib import Path

workdir = Path(os.environ["WORKDIR"])
meta = {
    "snapshotUrl": os.environ["SNAPSHOT_URL"],
    "commitUrl": os.environ["COMMIT_URL"],
    "commitSha": os.environ["COMMIT_SHA"],
    "branch": os.environ["BRANCH"],
    "branchUrl": os.environ["BRANCH_URL"],
    "sourcePath": os.environ["SOURCE_PATH"],
    "sourceHead": os.environ["SOURCE_HEAD"] or None,
    "sourceBranch": os.environ["SOURCE_BRANCH"],
    "createdAt": os.environ["CREATED_AT"],
    "status": "published",
}
(workdir / "snapshot.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

prompt = f"""Read and review this repository snapshot:

{os.environ["COMMIT_URL"]}

Branch: {os.environ["BRANCH"]}
Commit: {os.environ["COMMIT_SHA"]}

Task:
{os.environ["TASK_TEXT"]}
"""
(workdir / "oracle-prompt.md").write_text(prompt, encoding="utf-8")
print(json.dumps(meta, indent=2))
print(f"oraclePrompt: {workdir / 'oracle-prompt.md'}")
PY
