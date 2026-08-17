#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TARGET=${IIS_OBSERVATORY_TARGET:-/home/user01/project/iis-skills/observatory}
BIN_DIR=${IIS_OBSERVATORY_BIN_DIR:-$HOME/.local/bin}
FORCE=0
CREATE_LINK=1

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --target PATH    Source installation path
                   (default: /home/user01/project/iis-skills/observatory)
  --bin-dir PATH   CLI symlink directory (default: ~/.local/bin)
  --force          Back up and replace an existing target
  --no-link        Do not create the ~/.local/bin/iis-observatory symlink
  -h, --help       Show this help
EOF
}

while (($#)); do
  case "$1" in
    --target)
      TARGET=${2:?--target requires a path}
      shift 2
      ;;
    --bin-dir)
      BIN_DIR=${2:?--bin-dir requires a path}
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --no-link)
      CREATE_LINK=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

TARGET=$(python3 - "$TARGET" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).expanduser().resolve())
PY
)
SOURCE_REAL=$(python3 - "$SOURCE_DIR" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve())
PY
)

if [[ "$SOURCE_REAL" != "$TARGET" ]]; then
  mkdir -p "$(dirname -- "$TARGET")"
  if [[ -e "$TARGET" ]]; then
    if [[ "$FORCE" -ne 1 ]]; then
      echo "Target already exists: $TARGET" >&2
      echo "Re-run with --force to create a timestamped backup and replace it." >&2
      exit 3
    fi
    BACKUP="${TARGET}.backup.$(date +%Y%m%d-%H%M%S)"
    mv -- "$TARGET" "$BACKUP"
    echo "Existing installation backed up to: $BACKUP"
  fi
  STAGING="${TARGET}.installing.$$"
  trap 'rm -rf -- "$STAGING"' EXIT
  mkdir -p "$STAGING"
  cp -a "$SOURCE_DIR"/. "$STAGING"/
  mv -- "$STAGING" "$TARGET"
  trap - EXIT
fi

chmod +x "$TARGET/bin/iis-observatory" "$TARGET/install.sh" "$TARGET/uninstall.sh"

if [[ "$CREATE_LINK" -eq 1 ]]; then
  mkdir -p "$BIN_DIR"
  LINK="$BIN_DIR/iis-observatory"
  if [[ -e "$LINK" && ! -L "$LINK" ]]; then
    echo "Cannot replace non-symlink command: $LINK" >&2
    exit 4
  fi
  ln -sfn "$TARGET/bin/iis-observatory" "$LINK"
  echo "Command linked: $LINK -> $TARGET/bin/iis-observatory"
fi

"$TARGET/bin/iis-observatory" version >/dev/null
cat <<EOF
IIS Observatory installed.
Source:  $TARGET
Command: ${BIN_DIR}/iis-observatory

Try:
  iis-observatory overview ~/project
  iis-observatory scan ~/project/tax
EOF
