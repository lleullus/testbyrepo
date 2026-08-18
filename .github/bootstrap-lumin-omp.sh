#!/usr/bin/env bash
set -euo pipefail

SOURCE_REPO="https://github.com/annyeong844/lumin-repo-lens.git"
SOURCE_SHA="f7a9cee61d49e06a8350cd125a6b0641a64a59c0"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git clone --filter=blob:none --no-checkout "$SOURCE_REPO" "$tmp/source"
git -C "$tmp/source" checkout --detach "$SOURCE_SHA"

# Keep the bootstrap control files until the final commit.
find . -mindepth 1 -maxdepth 1 \
  ! -name .git ! -name .github \
  -exec rm -rf {} +
mkdir -p .port-overlay
tar -xzf .github/port-overlay.tar.gz -C .port-overlay
rsync -a --exclude='.git' --exclude='.github' "$tmp/source/" ./

# Replace Claude host integration with OMP-native package surfaces.
rm -rf .claude-plugin hooks
rsync -a .port-overlay/ ./
python3 scripts/transform-upstream.py

# Collection fields such as `paths` carry strings directly. Preserve them
# when adapting OMP multi-file edit calls to the existing preimage engine.
python3 - <<'PY'
from pathlib import Path

path = Path("extensions/adapter.mjs")
text = path.read_text()
needle = '  if (typeof value !== "object") return;\n'
replacement = (
    '  if (typeof value === "string") {\n'
    '    addPath(out, value);\n'
    '    return;\n'
    '  }\n\n'
    '  if (typeof value !== "object") return;\n'
)
if needle not in text:
    raise SystemExit("adapter patch anchor not found")
path.write_text(text.replace(needle, replacement, 1))
PY

# The generated branch commit excludes workflow files because Actions'
# GITHUB_TOKEN cannot create/update workflows. CI is added immediately
# afterward through the GitHub connector's workflow-capable credential.
rm -rf \
  .port-overlay \
  .github/port-overlay.tar.gz \
  .github/bootstrap-lumin-omp.sh \
  .github/trigger-lumin-omp \
  .github/workflows/bootstrap-lumin-omp.yml \
  .github/workflows/ci.yml

node scripts/verify-omp-port.mjs
node --test tests/*.test.mjs
npm --prefix skills/lumin-repo-lens ci
npm --prefix skills/lumin-repo-lens run smoke
bun test tests/omp-extension.test.ts
bun build extensions/lumin-repo-lens.ts \
  --target=bun \
  --external @oh-my-pi/pi-coding-agent \
  --outdir "$tmp/omp-build"

git status --short
