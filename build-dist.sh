#!/usr/bin/env bash
set -euo pipefail

# Build a distributable archive of logtrim for offline deployment
# Usage: ./build-dist.sh [--zip]
# Creates: dist/logtrim-source-YYYY-MM-DD.tar.gz (or .zip with --zip)

OUTPUT_DIR="dist"
DATE=$(date +%Y-%m-%d)
VERSION=$(grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
ARCHIVE_NAME="logtrim-$VERSION-source-${DATE}"

mkdir -p "$OUTPUT_DIR"
echo "Building distribution archive: $ARCHIVE_NAME"

tar czf "$OUTPUT_DIR/${ARCHIVE_NAME}.tar.gz" \
    --exclude='.git' \
    --exclude='.worktrees' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='*.egg-info' \
    --exclude='logtrim.egg-info' \
    --exclude='tests' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='oracle-pingpong-*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    --exclude='oracle*.log' \
    --exclude='oracle_*_capture*' \
    --exclude='r1_capture.md' \
    --exclude='simple_test_capture.md' \
    --exclude='input.txt' \
    --exclude='output.txt' \
    --exclude='.gitignore' \
    .

SIZE=$(du -h "$OUTPUT_DIR/${ARCHIVE_NAME}.tar.gz" | cut -f1)
echo "  tar.gz: $OUTPUT_DIR/${ARCHIVE_NAME}.tar.gz ($SIZE)"

if [ "${1:-}" = "--zip" ]; then
    if command -v zip &>/dev/null; then
        rm -rf "$ARCHIVE_NAME" 2>/dev/null || true
        mkdir -p "$ARCHIVE_NAME"
        tar xzf "$OUTPUT_DIR/${ARCHIVE_NAME}.tar.gz" -C "$ARCHIVE_NAME" --strip-components=1
        cd "$ARCHIVE_NAME"
        rm -rf tests __pycache__ dist "*.egg-info" logtrim.egg-info 2>/dev/null || true
        zip -r "../$OUTPUT_DIR/${ARCHIVE_NAME}.zip" . \
            -x "*.pyc" "__pycache__/*" "tests/*" ".git/*" ".venv/*" \
            --symlinks 2>/dev/null || true
        SIZE=$(du -h "../$OUTPUT_DIR/${ARCHIVE_NAME}.zip" | cut -f1)
        echo "  zip:    $OUTPUT_DIR/${ARCHIVE_NAME}.zip ($SIZE)"
        cd ..
        rm -rf "$ARCHIVE_NAME"
    else
        echo "[WARN] zip command not available, skipping .zip"
    fi
fi

echo ""
echo "Distribution files in $OUTPUT_DIR/:"
ls -la "$OUTPUT_DIR/"
