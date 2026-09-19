from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import socket
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evaluation/ready-verification/fixture_catalog.py"


def load_catalog():
    spec = importlib.util.spec_from_file_location("calibration_fixture_boundaries", CATALOG)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



class FixtureBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = load_catalog()
        self.environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")



    def test_holdout_helper_passes_while_actual_entrypoint_contradicts_it(self):
        metadata = self.catalog.materialize(
            {"family": "wrong-entry", "variant": "holdout"},
            self.root / "product", self.root / "support", port=12345,
        )
        helper = subprocess.run(
            [sys.executable, str(Path(metadata["project_root"]) / "tests/test_helper.py")],
            env=self.environment, capture_output=True, text=True,
        )
        actual = subprocess.run(metadata["trigger_argv"], env=self.environment, check=True, capture_output=True, text=True)
        self.assertEqual(helper.returncode, 0, helper.stderr)
        self.assertEqual(json.loads(actual.stdout), {"value": "original-value", "input": "sample"})


    def test_feedback_loop_shared_parser_defect_and_normal_twin(self):
        defect = self.catalog.materialize(
            {"family": "feedback-loop", "variant": "shared-defect"},
            self.root / "defect-product", self.root / "defect-support", port=12345,
        )
        lookup = subprocess.run(
            defect["trigger_argv"], env=self.environment, check=True, capture_output=True, text=True,
        )
        display = subprocess.run(
            defect["additional_trigger_argv"][0], env=self.environment, check=True, capture_output=True, text=True,
        )
        expected_error = {"error": "invalid composite identifier", "input": "org:west:item-42"}
        self.assertEqual(json.loads(lookup.stdout), expected_error)
        self.assertEqual(json.loads(display.stdout), expected_error)

        normal = self.catalog.materialize(
            {"family": "feedback-loop", "variant": "all-correct"},
            self.root / "normal-product", self.root / "normal-support", port=12345,
        )
        lookup = subprocess.run(
            normal["trigger_argv"], env=self.environment, check=True, capture_output=True, text=True,
        )
        display = subprocess.run(
            normal["additional_trigger_argv"][0], env=self.environment, check=True, capture_output=True, text=True,
        )
        self.assertEqual(json.loads(lookup.stdout), {
            "consumer": "lookup", "tenant": "org", "region": "west", "record": "item-42",
        })
        self.assertEqual(json.loads(display.stdout), {
            "consumer": "display", "identifier": "org:west:item-42", "label": "org/west/item-42",
        })

    def test_weak_oracle_passes_both_twins_but_actual_value_differs(self):
        for variant, expected in (("defective", "original-value"), ("normal", "revised-value")):
            metadata = self.catalog.materialize(
                {"family": "weak-oracle", "variant": variant},
                self.root / f"{variant}-product", self.root / f"{variant}-support", port=12345,
            )
            helper = subprocess.run([sys.executable, str(Path(metadata["project_root"]) / "tests/test_helper.py")], env=self.environment, capture_output=True)
            actual = subprocess.run(metadata["trigger_argv"], env=self.environment, check=True, capture_output=True, text=True)
            self.assertEqual(helper.returncode, 0)
            self.assertEqual(json.loads(actual.stdout)["value"], expected)

    def test_other_lane_cleanup_requires_resource_isolation(self):
        for variant, expected in (("shared", None), ("isolated", "lane-a")):
            metadata = self.catalog.materialize(
                {"family": "parallel-contamination", "variant": variant},
                self.root / f"{variant}-product", self.root / f"{variant}-support", port=12345,
            )
            for argv in (metadata["trigger_argv"], metadata["additional_trigger_argv"][0]):
                subprocess.run(argv, env=self.environment, check=True, capture_output=True)
            readback = subprocess.run(metadata["readback_argv"], env=self.environment, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(readback.stdout), {"identity": "lane-a", "value": expected})

    def test_feedback_loop_remote_execution_is_separate_and_observable(self):
        for variant, should_post in (("mixed-reported-defects", False), ("all-correct", True)):
            with self.subTest(variant=variant):
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", 0))
                    port = probe.getsockname()[1]
                metadata = self.catalog.materialize(
                    {"family": "feedback-loop", "variant": variant},
                    self.root / f"{variant}-product", self.root / f"{variant}-support", port=port,
                )
                subprocess.run(metadata["reset_argv"], env=self.environment, check=True, capture_output=True)
                protected = [Path(path) for path in [*metadata["target_paths"], metadata["scope_path"]]]
                before = {path: path.read_bytes() for path in protected}
                service = subprocess.Popen(
                    metadata["service_argv"], env=self.environment,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                try:
                    deadline = time.monotonic() + 5
                    while True:
                        try:
                            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                                break
                        except OSError:
                            if time.monotonic() >= deadline:
                                self.fail(f"feedback service did not become ready for {variant}")
                            time.sleep(0.02)
                    started = time.monotonic()
                    remote = subprocess.run(
                        metadata["additional_trigger_argv"][1], env=self.environment,
                        check=True, capture_output=True, text=True, timeout=5,
                    )
                    elapsed = time.monotonic() - started
                    observed = subprocess.run(
                        metadata["observer_argv"], env=self.environment,
                        check=True, capture_output=True, text=True, timeout=5,
                    )
                finally:
                    service.terminate()
                    try:
                        service.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        service.kill()
                        service.wait(timeout=3)

                requests = [
                    json.loads(line) for line in Path(metadata["request_log_path"]).read_text().splitlines()
                ]
                feedback_posts = [
                    item for item in requests
                    if item["method"] == "POST" and item["path"] == "/feedback/settle"
                ]
                self.assertEqual(bool(feedback_posts), should_post)
                if should_post:
                    self.assertGreaterEqual(elapsed, 1.5)
                    self.assertEqual(json.loads(remote.stdout)["body"]["request_id"], "feedback-1")
                    self.assertEqual(json.loads(observed.stdout)["body"], {"key": "gamma", "settled": True})
                else:
                    self.assertEqual(json.loads(remote.stdout)["body"]["request_id"], "local-only")
                    self.assertEqual(json.loads(observed.stdout)["body"], {"present": False})
                self.assertEqual({path: path.read_bytes() for path in protected}, before)


if __name__ == "__main__":
    unittest.main()
