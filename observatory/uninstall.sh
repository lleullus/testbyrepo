#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BIN_DIR=${IIS_OBSERVATORY_BIN_DIR:-$HOME/.local/bin}
PURGE=0

if [[ "${1:-}" == "--purge-source" ]]; then
  PURGE=1
elif [[ -n "${1:-}" ]]; then
  echo "Usage: ./uninstall.sh [--purge-source]" >&2
  exit 2
fi

LINK="$BIN_DIR/iis-observatory"
if [[ -L "$LINK" ]]; then
  TARGET=$(readlink "$LINK")
  if [[ "$TARGET" == "$SOURCE_DIR/bin/iis-observatory" ]]; then
    rm -- "$LINK"
    echo "Removed command link: $LINK"
  else
    echo "Command link points elsewhere; left unchanged: $LINK -> $TARGET" >&2
  fi
fi

if [[ "$PURGE" -eq 1 ]]; then
  cd "$(dirname -- "$SOURCE_DIR")"
  rm -rf -- "$SOURCE_DIR"
  echo "Removed source directory: $SOURCE_DIR"
else
  echo "Source retained: $SOURCE_DIR"
fi
