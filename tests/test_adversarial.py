from __future__ import annotations

import io
import unittest

from logtrim.pipeline import process_stream


class TestMustMerge(unittest.TestCase):
    """Volatile-only changes must produce one normalized group."""

    def test_timestamp_only_difference_merges(self) -> None:
        output = _process(
            "2026-04-07T11:00:00Z app[1]: Connection timeout to db-host\n"
            "2026-04-07T11:00:05Z app[1]: Connection timeout to db-host\n"
        )
        self.assertIn("[2] <TS> app[<PID>]: Connection timeout to db-host", output)
        self.assertEqual(output.count("count: 2\n"), 1)

    def test_pid_only_difference_merges(self) -> None:
        output = _process(
            "2026-04-07T11:00:00Z app[1]: Connection timeout to db-host\n"
            "2026-04-07T11:00:00Z app[2]: Connection timeout to db-host\n"
        )
        self.assertIn("[2] <TS> app[<PID>]: Connection timeout to db-host", output)
        self.assertEqual(output.count("count: 2\n"), 1)

    def test_uuid_only_difference_merges_in_json_request_id(self) -> None:
        output = _process(
            '{"level":"ERROR","message":"request timeout",'
            '"request_id":"11111111-1111-1111-1111-111111111111",'
            '"ts":"2026-04-07T11:00:00Z"}\n'
            '{"level":"ERROR","message":"request timeout",'
            '"request_id":"22222222-2222-2222-2222-222222222222",'
            '"ts":"2026-04-07T11:00:05Z"}\n'
        )
        self.assertIn('[2] {"level":"ERROR","message":"request timeout"}', output)
        self.assertEqual(output.count("count: 2\n"), 1)


class TestMustNotMerge(unittest.TestCase):
    """Semantic differences must remain visible as separate groups."""

    def test_component_identity_is_preserved(self) -> None:
        output = _process(
            "2026-04-07T11:00:00Z nginx[1]: Failed to start\n"
            "2026-04-07T11:00:01Z postgres[2]: Failed to start\n"
        )
        patterns = _patterns_with_count(output, 1)
        self.assertIn("<TS> nginx[<PID>]: Failed to start", patterns)
        self.assertIn("<TS> postgres[<PID>]: Failed to start", patterns)
        self.assertNotIn("[2] <TS> <PID>: Failed to start", output)

    def test_different_errors_do_not_merge(self) -> None:
        output = _process(
            "2026-04-07T11:00:00Z app[1]: timeout\n"
            "2026-04-07T11:00:01Z app[2]: connection refused\n"
        )
        patterns = _patterns_with_count(output, 1)
        self.assertIn("<TS> app[<PID>]: timeout", patterns)
        self.assertIn("<TS> app[<PID>]: connection refused", patterns)

    def test_permission_and_disk_errors_do_not_merge(self) -> None:
        output = _process(
            "2026-04-07T11:00:00Z app[1]: permission denied\n"
            "2026-04-07T11:00:01Z app[2]: disk full\n"
        )
        patterns = _patterns_with_count(output, 1)
        self.assertIn("<TS> app[<PID>]: permission denied", patterns)
        self.assertIn("<TS> app[<PID>]: disk full", patterns)


def _process(text: str) -> str:
    return "".join(process_stream(io.StringIO(text)))


def _patterns_with_count(output: str, count: int) -> set[str]:
    prefix = f"[{count}] "
    return {line[len(prefix) :] for line in output.splitlines() if line.startswith(prefix)}


if __name__ == "__main__":
    unittest.main()
