from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "verification-lead/tools/verification-run/executable_identity.py"
SPEC = importlib.util.spec_from_file_location("executable_identity", MODULE)
assert SPEC and SPEC.loader
executable_identity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(executable_identity)


class ExecutableIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.executable = self.root / "tool"
        self.payload = b"#!/bin/sh\nprintf 'stable\\n'\n"
        self.executable.write_bytes(self.payload)
        self.executable.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def observe(self) -> dict[str, Any]:
        return executable_identity.observe_executable_identity(self.executable)

    def assert_identity_error(self, code: str, operation: Callable[[], object]) -> None:
        with self.assertRaises(executable_identity.ExecutableIdentityError) as caught:
            operation()
        self.assertEqual(code, caught.exception.code)

    def test_observation_returns_exact_typed_projection(self) -> None:
        metadata = self.executable.stat(follow_symlinks=False)

        identity = self.observe()

        self.assertEqual(
            {
                "canonicalPath": str(self.executable.resolve(strict=True)),
                "contentSha256": hashlib.sha256(self.payload).hexdigest(),
                "byteCount": len(self.payload),
                "executableMode": stat.S_IMODE(metadata.st_mode),
                "ownerUid": metadata.st_uid,
                "ownerGid": metadata.st_gid,
            },
            identity,
        )
        self.assertEqual(identity, executable_identity.validate_executable_identity(identity))

    def test_observation_uses_no_follow_and_close_on_exec_open_flags(self) -> None:
        real_open = os.open
        with mock.patch.object(executable_identity.os, "open", wraps=real_open) as opened:
            self.observe()

        flags = opened.call_args.args[1]
        if hasattr(os, "O_NOFOLLOW"):
            self.assertTrue(flags & os.O_NOFOLLOW)
        if hasattr(os, "O_CLOEXEC"):
            self.assertTrue(flags & os.O_CLOEXEC)

    def test_missing_no_follow_support_fails_closed_before_open(self) -> None:
        with mock.patch.object(executable_identity.os, "O_NOFOLLOW", None), mock.patch.object(
            executable_identity.os, "open"
        ) as opened:
            self.assert_identity_error(
                "EXECUTABLE_IDENTITY_UNSUPPORTED",
                lambda: executable_identity.observe_executable_identity(self.executable),
            )
        opened.assert_not_called()

    def test_relative_noncanonical_and_symlink_paths_fail_closed(self) -> None:
        self.assert_identity_error(
            "EXECUTABLE_PATH_INVALID",
            lambda: executable_identity.observe_executable_identity("tool"),
        )
        self.assert_identity_error(
            "EXECUTABLE_PATH_INVALID",
            lambda: executable_identity.observe_executable_identity(
                f"{self.root}/./{self.executable.name}"
            ),
        )
        link = self.root / "tool-link"
        link.symlink_to(self.executable)
        self.assert_identity_error(
            "EXECUTABLE_PATH_INVALID",
            lambda: executable_identity.observe_executable_identity(link),
        )

    def test_non_regular_unreadable_and_non_executable_paths_fail_closed(self) -> None:
        fifo = self.root / "tool.fifo"
        os.mkfifo(fifo, 0o755)
        self.assert_identity_error(
            "EXECUTABLE_NOT_REGULAR",
            lambda: executable_identity.observe_executable_identity(fifo),
        )

        self.executable.chmod(0o111)
        self.assert_identity_error(
            "EXECUTABLE_NOT_READABLE",
            lambda: executable_identity.observe_executable_identity(self.executable),
        )

        self.executable.chmod(0o644)
        self.assert_identity_error(
            "EXECUTABLE_NOT_EXECUTABLE",
            lambda: executable_identity.observe_executable_identity(self.executable),
        )

    def test_content_swap_during_streaming_fails_closed(self) -> None:
        real_read = os.read
        before = self.executable.stat(follow_symlinks=False)
        swapped = False

        def swapping_read(descriptor: int, maximum: int) -> bytes:
            nonlocal swapped
            chunk = real_read(descriptor, maximum)
            if chunk and not swapped:
                swapped = True
                self.executable.write_bytes(b"x" * len(self.payload))
                self.executable.chmod(0o755)
                os.utime(
                    self.executable,
                    ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000),
                )
            return chunk

        with mock.patch.object(executable_identity.os, "read", side_effect=swapping_read):
            with self.assertRaises(executable_identity.ExecutableIdentityError) as caught:
                executable_identity.observe_executable_identity(self.executable)
        self.assertEqual("EXECUTABLE_IDENTITY_UNSTABLE", caught.exception.code)
        self.assertEqual(len(self.payload), caught.exception.bytes_hashed)
        self.assertTrue(swapped)

    def test_mode_swap_during_streaming_fails_closed(self) -> None:
        real_read = os.read
        swapped = False

        def swapping_read(descriptor: int, maximum: int) -> bytes:
            nonlocal swapped
            chunk = real_read(descriptor, maximum)
            if chunk and not swapped:
                swapped = True
                self.executable.chmod(0o700)
            return chunk

        with mock.patch.object(executable_identity.os, "read", side_effect=swapping_read):
            self.assert_identity_error(
                "EXECUTABLE_IDENTITY_UNSTABLE",
                lambda: executable_identity.observe_executable_identity(self.executable),
            )
        self.assertTrue(swapped)

    def test_path_replacement_during_streaming_fails_closed(self) -> None:
        real_read = os.read
        replacement = self.root / "replacement"
        replacement.write_bytes(b"replacement executable\n")
        replacement.chmod(0o755)
        swapped = False

        def swapping_read(descriptor: int, maximum: int) -> bytes:
            nonlocal swapped
            chunk = real_read(descriptor, maximum)
            if chunk and not swapped:
                swapped = True
                os.replace(replacement, self.executable)
            return chunk

        with mock.patch.object(executable_identity.os, "read", side_effect=swapping_read):
            self.assert_identity_error(
                "EXECUTABLE_IDENTITY_UNSTABLE",
                lambda: executable_identity.observe_executable_identity(self.executable),
            )
        self.assertTrue(swapped)

    def test_streamed_byte_count_must_equal_stable_stat_size(self) -> None:
        real_read = os.read
        injected = False

        def oversized_read(descriptor: int, maximum: int) -> bytes:
            nonlocal injected
            chunk = real_read(descriptor, maximum)
            if not chunk and not injected:
                injected = True
                return b"x"
            return chunk

        with mock.patch.object(executable_identity.os, "read", side_effect=oversized_read):
            self.assert_identity_error(
                "EXECUTABLE_IDENTITY_UNSTABLE",
                lambda: executable_identity.observe_executable_identity(self.executable),
            )
        self.assertTrue(injected)

    def test_projection_validator_rejects_extra_fields_and_wrong_runtime_types(self) -> None:
        identity = self.observe()
        mutations = [
            {**identity, "callerSupplied": True},
            {**identity, "contentSha256": str(identity["contentSha256"]).upper()},
            {**identity, "byteCount": True},
            {**identity, "executableMode": 0o10000},
            {**identity, "executableMode": 0o644},
            {**identity, "executableMode": 0o111},
            {**identity, "ownerUid": -1},
            {**identity, "ownerGid": -1},
            {**identity, "canonicalPath": f"{self.root}/../elsewhere/tool"},
        ]

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                def validate_mutation() -> object:
                    return executable_identity.validate_executable_identity(mutation)

                self.assert_identity_error(
                    "INVALID_EXECUTABLE_IDENTITY",
                    validate_mutation,
                )

    def test_projection_validator_can_bind_the_expected_canonical_path(self) -> None:
        identity = self.observe()

        self.assertEqual(
            identity,
            executable_identity.validate_executable_identity(
                identity, expected_canonical_path=self.executable
            ),
        )
        self.assert_identity_error(
            "EXECUTABLE_PATH_MISMATCH",
            lambda: executable_identity.validate_executable_identity(
                identity, expected_canonical_path=self.root / "other-tool"
            ),
        )

    def test_exact_compare_validates_both_projections_and_compares_every_field(self) -> None:
        identity = self.observe()
        self.assertTrue(executable_identity.executable_identities_equal(identity, dict(identity)))

        replacements = {
            "canonicalPath": str(self.root / "other-tool"),
            "contentSha256": "0" * 64,
            "byteCount": int(identity["byteCount"]) + 1,
            "executableMode": 0o700,
            "ownerUid": int(identity["ownerUid"]) + 1,
            "ownerGid": int(identity["ownerGid"]) + 1,
        }
        for field, replacement in replacements.items():
            changed = {**identity, field: replacement}
            with self.subTest(field=field):
                self.assertFalse(
                    executable_identity.executable_identities_equal(identity, changed)
                )

        malformed = {**identity, "byteCount": False}
        self.assert_identity_error(
            "INVALID_EXECUTABLE_IDENTITY",
            lambda: executable_identity.executable_identities_equal(identity, malformed),
        )


if __name__ == "__main__":
    unittest.main()
