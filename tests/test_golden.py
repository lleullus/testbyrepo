from __future__ import annotations

import unittest
from pathlib import Path

from logtrim.pipeline import process_stream


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class TestGoldenFixtures(unittest.TestCase):
    """Each source-family fixture must remain byte-for-byte stable."""

    def test_family_fixtures(self) -> None:
        for family in ("event", "json", "snapshot", "describe", "generic", "mixed"):
            with self.subTest(family=family):
                input_path = FIXTURES / f"{family}_basic.input"
                expected_path = FIXTURES / f"{family}_basic.output"
                actual = _process_fixture(input_path)
                self.assertEqual(expected_path.read_bytes(), actual)


def _process_fixture(input_path: Path) -> bytes:
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        chunks = list(process_stream(input_file))

    # The CLI intentionally removes the title for a generic-only capture.
    if len(chunks) == 1 and chunks[0].startswith("Generic Text\n"):
        chunks[0] = chunks[0][len("Generic Text\n") :]
    return "".join(chunks).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
