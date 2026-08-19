from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SYNC = ROOT / "scripts/sync-iis-pi-models.mjs"
MODEL_IDS = [
    "command-code/meta-muse-spark-1.2-contributor",
    "google-antigravity/gemini-3.7-flash",
    "gpt-5.6-luna",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
]


class PiModelSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.omp_models = self.work / "models.yml"
        self.agent_dir = self.work / "agent"
        self.agent_dir.mkdir()
        self.pi_models = self.agent_dir / "models.json"
        self.auth = self.agent_dir / "auth.json"
        self.log = self.work / "pi.log"
        self.actual_pi = shutil.which("pi")
        if not self.actual_pi:
            self.skipTest("Pi runtime is unavailable")

        self.omp_models.write_text(self._omp_yaml(), encoding="utf-8")
        self.current_pi = {
            "localPolicy": {"owner": "pi"},
            "providers": {
                "opencodex": {
                    "baseUrl": "http://old.invalid/v1",
                    "api": "openai-responses",
                    "apiKey": "pi-owned-secret-credential",
                    "headers": {"X-Pi-Owned": "preserve-me"},
                    "models": [
                        {
                            "id": "gpt-5.6-sol",
                            "name": "old-sol",
                            "api": "openai-responses",
                            "reasoning": True,
                            "input": ["text"],
                            "contextWindow": 1,
                            "maxTokens": 1,
                            "thinkingLevelMap": {"high": "high"},
                            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                        }
                    ],
                },
                "pi-owned-provider": {
                    "baseUrl": "http://pi-owned.invalid/v1",
                    "api": "openai-completions",
                    "apiKey": "other-pi-secret",
                    "models": [],
                },
            },
        }
        self.pi_models.write_text(json.dumps(self.current_pi, indent=2) + "\n", encoding="utf-8")
        self.pi_models.chmod(0o600)
        self.auth.write_text('{"opencodex":{"type":"api_key","key":"auth-store-secret"}}\n', encoding="utf-8")
        self.auth.chmod(0o600)

        self.effective = {"models": [self._effective_model(model_id) for model_id in MODEL_IDS]}
        self.omp = self.work / "fake-omp.py"
        self.omp.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json
                import sys
                if sys.argv[1:] != ["models", "opencodex", "--json"]:
                    raise SystemExit(3)
                print({json.dumps(json.dumps(self.effective))})
                """
            ),
            encoding="utf-8",
        )
        self.omp.chmod(0o755)

        self.pi = self.work / "fake-pi.py"
        self.pi.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import signal
                import sys

                args = sys.argv[1:]
                signal.alarm(2)
                sys.stdin.read()
                signal.alarm(0)
                agent_dir = os.environ["PI_CODING_AGENT_DIR"]
                with open(os.path.join(agent_dir, "models.json"), encoding="utf-8") as stream:
                    config = json.load(stream)
                provider = config["providers"]["opencodex"]
                if "--list-models" in args:
                    print("provider  model  context  max-out  thinking  images")
                    for model in provider["models"]:
                        print(f"opencodex  {model['id']}  1K  1K  yes  yes")
                    raise SystemExit(0)

                binding = args[args.index("--model") + 1]
                model_id = binding.split("/", 1)[1]
                model = next(model for model in provider["models"] if model["id"] == model_id)
                api = model.get("api", provider["api"])
                with open(os.environ["FAKE_PI_LOG"], "a", encoding="utf-8") as stream:
                    stream.write(json.dumps({"binding": binding, "api": api}) + "\\n")
                stale_path = os.environ.get("FAKE_PI_STALE_OMP")
                if stale_path and not os.path.exists(stale_path + ".mutated"):
                    with open(stale_path, "a", encoding="utf-8") as stream:
                        stream.write("\\n# concurrent update\\n")
                    open(stale_path + ".mutated", "w", encoding="utf-8").close()
                stale_pi_path = os.environ.get("FAKE_PI_STALE_PI")
                if stale_pi_path and not os.path.exists(stale_pi_path + ".mutated"):
                    with open(stale_pi_path, "w", encoding="utf-8") as stream:
                        stream.write(os.environ["FAKE_PI_STALE_PI_CONTENT"])
                    open(stale_pi_path + ".mutated", "w", encoding="utf-8").close()
                if os.environ.get("FAKE_PI_FAIL_SMOKE") == "1":
                    raise SystemExit(9)
                print(json.dumps({
                    "type": "message_end",
                    "message": {
                        "role": "assistant",
                        "api": api,
                        "model": model_id,
                        "content": [{"type": "text", "text": "IIS_PI_MODEL_SYNC_SMOKE_OK"}],
                    },
                }))
                """
            ),
            encoding="utf-8",
        )
        self.pi.chmod(0o755)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _omp_yaml() -> str:
        model_rows = []
        for model_id in MODEL_IDS:
            api = "\n        api: openai-responses" if model_id.startswith("gpt-") else ""
            efforts = "[low, medium, high]" if "gemini" in model_id else "[minimal, low, medium, high, xhigh, max]"
            model_rows.append(
                f"""\
      - id: {model_id}
        name: {model_id}-name{api}
        reasoning: true
        input: [text, image]
        contextWindow: 500000
        maxTokens: 32000
        thinking:
          mode: effort
          efforts: {efforts}"""
            )
        return (
            "compactionModel: opencodex/gpt-5.6-luna\n"
            "thinking:\n  defaultLevel: medium\n"
            "providers:\n"
            "  opencodex:\n"
            "    baseUrl: http://127.0.0.1:10100/v1\n"
            "    api: openai-completions\n"
            "    apiKey: omp-owned-do-not-copy\n"
            "    models:\n"
            + "\n".join(model_rows)
            + "\n"
        )

    @staticmethod
    def _effective_model(model_id: str) -> dict[str, object]:
        return {
            "provider": "opencodex",
            "id": model_id,
            "name": f"{model_id}-name",
            "reasoning": True,
            "input": ["text", "image"],
            "contextWindow": 500000,
            "maxTokens": 32000,
            "thinking": (
                ["low", "medium", "high"]
                if "gemini" in model_id
                else ["minimal", "low", "medium", "high", "xhigh", "max"]
            ),
            "cost": {"input": 1, "output": 2, "cacheRead": 0.1, "cacheWrite": 0},
        }

    def run_sync(
        self, mode: str, *, extra_env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SYNC), mode],
            cwd=ROOT,
            env={
                **os.environ,
                "IIS_OMP_MODELS_PATH": str(self.omp_models),
                "IIS_PI_AGENT_DIR": str(self.agent_dir),
                "OMP_BIN": str(self.omp),
                "IIS_PI_BIN": str(self.pi),
                "IIS_PI_YAML_RUNTIME": str(self.actual_pi),
                "FAKE_PI_LOG": str(self.log),
                **(extra_env or {}),
            },
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_check_reports_full_drift_without_writes_or_secrets(self) -> None:
        before_omp = self.omp_models.read_bytes()
        before_pi = self.pi_models.read_bytes()
        before_auth = self.auth.read_bytes()
        completed = self.run_sync("--check")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("DRIFT", completed.stdout)
        self.assertIn("OMP models: 5", completed.stdout)
        self.assertIn("Pi models: 1", completed.stdout)
        self.assertIn("command-code/meta-muse-spark-1.2-contributor", completed.stdout)
        self.assertNotIn("pi-owned-secret-credential", completed.stdout + completed.stderr)
        self.assertNotIn("omp-owned-do-not-copy", completed.stdout + completed.stderr)
        self.assertEqual(self.omp_models.read_bytes(), before_omp)
        self.assertEqual(self.pi_models.read_bytes(), before_pi)
        self.assertEqual(self.auth.read_bytes(), before_auth)
        self.assertFalse(self.log.exists())

    def test_apply_preserves_pi_authority_and_smokes_each_api_family(self) -> None:
        before_auth = self.auth.read_bytes()
        other_provider = self.current_pi["providers"]["pi-owned-provider"]
        completed = self.run_sync("--apply")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("APPLIED:", completed.stdout)
        self.assertNotIn("pi-owned-secret-credential", completed.stdout + completed.stderr)
        applied = json.loads(self.pi_models.read_text(encoding="utf-8"))
        provider = applied["providers"]["opencodex"]
        self.assertEqual(provider["apiKey"], "pi-owned-secret-credential")
        self.assertEqual(provider["headers"], {"X-Pi-Owned": "preserve-me"})
        self.assertEqual(provider["api"], "openai-completions")
        self.assertEqual(provider["baseUrl"], "http://127.0.0.1:10100/v1")
        self.assertEqual([model["id"] for model in provider["models"]], MODEL_IDS)
        self.assertEqual(
            {model["api"] for model in provider["models"] if model["id"].startswith("gpt-")},
            {"openai-responses"},
        )
        gemini = next(model for model in provider["models"] if "gemini" in model["id"])
        self.assertIsNone(gemini["thinkingLevelMap"]["minimal"])
        self.assertIsNone(gemini["thinkingLevelMap"]["xhigh"])
        self.assertEqual(applied["providers"]["pi-owned-provider"], other_provider)
        self.assertEqual(applied["localPolicy"], {"owner": "pi"})
        self.assertNotIn("compactionModel", applied)
        self.assertNotIn("thinking", applied)
        self.assertEqual(self.auth.read_bytes(), before_auth)
        self.assertEqual(stat.S_IMODE(self.pi_models.stat().st_mode), 0o600)
        smokes = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual({smoke["api"] for smoke in smokes}, {"openai-completions", "openai-responses"})
        self.assertEqual(len(smokes), 2)

    def test_failed_inference_preserves_existing_pi_config(self) -> None:
        before = self.pi_models.read_bytes()
        completed = self.run_sync("--apply", extra_env={"FAKE_PI_FAIL_SMOKE": "1"})
        self.assertEqual(completed.returncode, 2)
        self.assertIn("ERROR:", completed.stderr)
        self.assertEqual(self.pi_models.read_bytes(), before)

    def test_stale_omp_input_aborts_without_overwriting_pi_config(self) -> None:
        before = self.pi_models.read_bytes()
        completed = self.run_sync(
            "--apply", extra_env={"FAKE_PI_STALE_OMP": str(self.omp_models)}
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("STALE INPUT", completed.stderr)
        self.assertEqual(self.pi_models.read_bytes(), before)

    def test_stale_pi_input_aborts_and_preserves_concurrent_update(self) -> None:
        concurrent_config = json.loads(json.dumps(self.current_pi))
        concurrent_config["providers"]["opencodex"][
            "apiKey"
        ] = "concurrent-pi-owned-credential"
        concurrent_config["localPolicy"]["revision"] = "concurrent-writer"
        concurrent_payload = json.dumps(concurrent_config, indent=2) + "\n"
        completed = self.run_sync(
            "--apply",
            extra_env={
                "FAKE_PI_STALE_PI": str(self.pi_models),
                "FAKE_PI_STALE_PI_CONTENT": concurrent_payload,
            },
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("STALE INPUT", completed.stderr)
        self.assertEqual(self.pi_models.read_bytes(), concurrent_payload.encode())


if __name__ == "__main__":
    unittest.main()
