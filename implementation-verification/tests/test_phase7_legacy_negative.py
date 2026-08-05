from __future__ import annotations

import builtins
import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path

from tests.test_phase7_public_contract import Phase7PublicContractTests, entrypoint, interface, production


class Phase7LegacyNegativeTests(Phase7PublicContractTests):
    def test_legacy_unavailable_production_fail_closed_flow(self) -> None:
        blocked = {
            "implementation_result",
            "verification_run",
            "workflow_store",
            "baseline_capsule",
        }
        calls: list[str] = []
        original_import = builtins.__import__
        original_open = builtins.open
        original_path_open = Path.open
        original_os_open = os.open
        original_sqlite_connect = sqlite3.connect

        def is_legacy_path(value) -> bool:
            try:
                path = Path(os.fspath(value))
            except TypeError:
                return False
            return any(path == root or root in path.parents for root in legacy_roots.values())

        def guarded_import(name, *args, **kwargs):
            root = name.split(".", 1)[0]
            if root in blocked:
                calls.append(name)
                raise ImportError(f"legacy import blocked: {name}")
            return original_import(name, *args, **kwargs)

        def guarded_open(file, *args, **kwargs):
            if is_legacy_path(file):
                calls.append(str(file))
                raise PermissionError(f"legacy store read blocked: {file}")
            return original_open(file, *args, **kwargs)

        def guarded_path_open(path, *args, **kwargs):
            if is_legacy_path(path):
                calls.append(str(path))
                raise PermissionError(f"legacy store read blocked: {path}")
            return original_path_open(path, *args, **kwargs)

        def guarded_os_open(path, *args, **kwargs):
            if is_legacy_path(path):
                calls.append(str(path))
                raise PermissionError(f"legacy store read blocked: {path}")
            return original_os_open(path, *args, **kwargs)

        def guarded_sqlite_connect(database, *args, **kwargs):
            if is_legacy_path(database):
                calls.append(str(database))
                raise PermissionError(f"legacy store read blocked: {database}")
            return original_sqlite_connect(database, *args, **kwargs)

        legacy_roots = {}
        prior = {}
        for name in (
            "IMPLEMENTATION_WORKFLOW_STORE",
            "IMPLEMENTATION_RESULT_STORE",
            "BASELINE_CAPSULE_STORE",
        ):
            root = self.root / name.lower()
            root.mkdir(mode=0o700)
            (root / "poisoned-result.json").write_text(
                json.dumps(
                    {
                        "status": "VERIFIED",
                        "planning": "poisoned-current-mismatch",
                        "source": "poisoned-current-mismatch",
                    }
                ),
                encoding="utf-8",
            )
            root.chmod(0o000)
            legacy_roots[name] = root
            prior[name] = os.environ.get(name)
            os.environ[name] = str(root)
        builtins.__import__ = guarded_import
        builtins.open = guarded_open
        Path.open = guarded_path_open
        os.open = guarded_os_open
        sqlite3.connect = guarded_sqlite_connect
        try:
            module = entrypoint._compose_module(
                self.state,
                production.LinuxImplementationReviewAdapter(
                    production.ProcessImplementationReview(
                        ("/usr/bin/python3", "-c", "import json;print(json.dumps({'decision':'CLOSE'}))")
                    ),
                    production.ProcessImplementationCheck(
                        ("/usr/bin/python3", "-c", "import json;print(json.dumps({'status':'PASSED'}))")
                    ),
                    effect_adapter_enabled=False,
                ),
                production.LinuxWorkerAdapter(),
                production.LinuxSourceAdoptionAdapter(),
                production.LinuxFreshVerifierAdapter(
                    production.ProcessVerifier(("/usr/bin/python3", "-c", "print('[]')"))
                ),
                production.LinuxEvidenceRunnerAdapter(),
            )
            result = module.implement(self.ticket, self.worker())
            inspection = module.inspect(self.ticket)
        finally:
            builtins.__import__ = original_import
            builtins.open = original_open
            Path.open = original_path_open
            os.open = original_os_open
            sqlite3.connect = original_sqlite_connect
            for name, root in legacy_roots.items():
                if prior[name] is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = prior[name]
                root.chmod(0o700)

        self.assertEqual([], calls)
        self.assertIsInstance(result, interface.Candidate)
        self.assertEqual(result, inspection.result)
        public_inputs = (self.ticket, self.worker())
        forbidden = ("actor", "capability", "claim", "run", "flow", "step", "replay")
        self.assertFalse(any(word in repr(public_inputs).lower() for word in forbidden))


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromName(
        f"{__name__}.Phase7LegacyNegativeTests.test_legacy_unavailable_production_fail_closed_flow"
    )
