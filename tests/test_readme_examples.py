from __future__ import annotations

import unittest
from pathlib import Path

from logtrim.pipeline import process_stream


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


class TestReadmeExamples(unittest.TestCase):
    """The documented event and snapshot examples are executable contracts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = README.read_text(encoding="utf-8")

    def test_event_example_matches_documented_output(self) -> None:
        input_text = _fenced_text(self.readme, "Example event log input:")
        expected = _fenced_text(self.readme, "Example output:")
        actual = "".join(process_stream(input_text.splitlines(keepends=True)))
        self.assertEqual(expected, actual)

    def test_snapshot_example_matches_documented_output(self) -> None:
        input_text = _fenced_text(self.readme, "Example snapshot input:")
        expected = _fenced_text(self.readme, "Example snapshot output:")
        actual = "".join(process_stream(input_text.splitlines(keepends=True)))
        self.assertEqual(expected, actual)


def _fenced_text(document: str, marker: str) -> str:
    section = document.split(marker, 1)[1]
    opening = "```text\n"
    start = section.index(opening) + len(opening)
    end = section.index("\n```", start)
    return section[start:end] + "\n"


if __name__ == "__main__":
    unittest.main()
