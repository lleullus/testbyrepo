#!/usr/bin/env python3
from pathlib import Path

for root in (Path("commands"), Path("skills")):
    for file in root.rglob("*.md"):
        text = file.read_text(encoding="utf-8")
        text = text.replace("${CLAUDE_PLUGIN_ROOT}", "${OMP_PLUGIN_ROOT}")
        text = text.replace(
            "When installed as a Claude Code plugin",
            "When installed as an OMP plugin",
        )
        text = text.replace("Claude Code plugin", "OMP plugin")
        text = text.replace("Claude Code에서는", "OMP에서는")
        file.write_text(text, encoding="utf-8")
