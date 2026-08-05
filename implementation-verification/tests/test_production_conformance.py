from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


interface = load("implementation_verification", ROOT / "implementation_verification.py")
load("durable_work", ROOT / "durable_work.py")
load("durable_backend", ROOT / "durable_backend.py")
implementation = load("implementation_execution", ROOT / "implementation_execution.py")
verification = load("verification_execution", ROOT / "verification_execution.py")
production = load("production_adapters", ROOT / "production_adapters.py")
entrypoint = load("production_entrypoint", ROOT / "production_entrypoint.py")


class ProductionAdapterConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def candidate(self, retained: Path, canonical: Path) -> object:
        ticket = self.root / "TICKET.md"
        ticket.write_text("ticket", encoding="utf-8")
        _, identity = implementation._capture(retained)
        return interface.Candidate(
            work=ticket.resolve(),
            planning={"projectRoot": str(canonical.resolve()), "planning": "exact"},
            acceptance_criteria=({"criterion": "full"},),
            source={"identity": identity, "retainedRoot": str(retained.resolve())},
            implementation_changes=("app.txt",),
            preserved_changes=(),
            result_identity="candidate:physical-probe",
        )

    def review_adapter(self, review_code: str, check_code: str, *, timeout: float = 300):
        return production.LinuxImplementationReviewAdapter(
            production.ProcessImplementationReview(("/usr/bin/python3", "-c", review_code), timeout),
            production.ProcessImplementationCheck(("/usr/bin/python3", "-c", check_code), timeout),
            effect_adapter_enabled=False,
        )

    def test_implementation_review_check_run_in_read_only_source_namespace(self) -> None:
        source = self.root / "source"
        source.mkdir()
        target = source / "app.txt"
        target.write_text("baseline", encoding="utf-8")
        module_state = self.root / "module-state"
        module_state.mkdir()
        state_canary = module_state / "canary.txt"
        state_canary.write_text("state", encoding="utf-8")
        work = self.root / "TICKET.md"
        work.write_text("exact ticket", encoding="utf-8")
        outside = self.root / "outside-projection-canary.txt"
        outside.write_text("outside", encoding="utf-8")
        work_sha256 = __import__("hashlib").sha256(work.read_bytes()).hexdigest()
        review = (
            "import json,pathlib;"
            "r=json.loads(pathlib.Path('/input/request.json').read_text());"
            f"outside={str(outside)!r};state={str(state_canary)!r};work_sha256={work_sha256!r};"
            "blocked=False;"
            "\ntry: pathlib.Path('/source/app.txt').write_text('forbidden')\n"
            "except Exception: blocked=True\n"
            "assert set(r)=={'operation','work','source'} and r['operation']=='ASSIGNMENT';"
            "assert r['work']=={'path':'/input/ticket.md','sha256':work_sha256};"
            "assert r['source']['root']=='/source' and isinstance(r['source']['identity'],str);"
            "assert pathlib.Path('/input/ticket.md').read_text()=='exact ticket' and not pathlib.Path(outside).exists() and not pathlib.Path(state).exists() and blocked;"
            "print(json.dumps({'decision':'ASSIGN','assignment':{'path':'app.txt','value':'implemented'}}))"
        )
        closure = (
            "import json,pathlib;"
            "r=json.loads(pathlib.Path('/input/request.json').read_text());"
            "assert r['operation']=='CLOSURE' and pathlib.Path('/source/app.txt').read_text()=='baseline';"
            "print(json.dumps({'decision':'CLOSE'}))"
        )
        check = (
            "import json,pathlib;"
            "r=json.loads(pathlib.Path('/input/request.json').read_text());blocked=False;"
            "\ntry: pathlib.Path('/source/app.txt').write_text('forbidden')\n"
            "except Exception: blocked=True\n"
            "assert r['operation']=='CHECK' and blocked;print(json.dumps({'status':'PASSED'}))"
        )
        adapter = self.review_adapter(review, check)

        assignment = adapter.next_assignment(work, source)
        closed = self.review_adapter(closure, check).close(work, source)
        checked = adapter.check(work, source)

        self.assertEqual({"path": "app.txt", "value": "implemented"}, assignment)
        self.assertIsNone(closed)
        self.assertIsNone(checked)
        self.assertEqual(b"baseline", target.read_bytes())
        self.assertEqual(b"state", state_canary.read_bytes())

    def test_implementation_review_rejects_unbounded_assignment_and_closure(self) -> None:
        source = self.root / "source"
        source.mkdir()
        work = self.root / "TICKET.md"
        work.write_text("exact ticket", encoding="utf-8")
        invalid_assignment = self.review_adapter(
            "import json;print(json.dumps({'decision':'ASSIGN','assignment':{'path':'../outside','value':'x'}}))",
            "import json;print(json.dumps({'status':'PASSED'}))",
        ).next_assignment(work, source)
        invalid_closure = self.review_adapter(
            "import json;print(json.dumps({'decision':'ASSIGN','assignment':{'path':'app.txt','value':'x'}}))",
            "import json;print(json.dumps({'status':'PASSED'}))",
        ).close(work, source)

        self.assertIsInstance(invalid_assignment, implementation.ImplementationBlocker)
        self.assertIsInstance(invalid_closure, implementation.ImplementationBlocker)

    def test_implementation_review_timeout_and_missing_tool_stop(self) -> None:
        source = self.root / "source"
        source.mkdir()
        work = self.root / "TICKET.md"
        work.write_text("exact ticket", encoding="utf-8")
        timed_out = self.review_adapter(
            "import time;time.sleep(1)",
            "import json;print(json.dumps({'status':'PASSED'}))",
            timeout=0.01,
        ).next_assignment(work, source)
        unavailable = production.LinuxImplementationReviewAdapter(
            production.ProcessImplementationReview(("/missing/implementation-review",)),
            production.ProcessImplementationCheck(("/usr/bin/python3", "-c", "import json;print(json.dumps({'status':'PASSED'}))")),
            effect_adapter_enabled=False,
        ).next_assignment(work, source)
        malformed = self.review_adapter(
            "print('not-json')",
            "import json;print(json.dumps({'status':'PASSED'}))",
        ).next_assignment(work, source)

        self.assertEqual("production implementation review timed out", timed_out.reason)
        self.assertEqual("production implementation review is unavailable", unavailable.reason)
        self.assertEqual("production implementation review result is unreadable", malformed.reason)

    def test_implementation_check_timeout_missing_tool_and_unreadable_result_stop(self) -> None:
        source = self.root / "source"
        source.mkdir()
        work = self.root / "TICKET.md"
        work.write_text("exact ticket", encoding="utf-8")
        timed_out = self.review_adapter(
            "import json;print(json.dumps({'decision':'CLOSE'}))",
            "import time;time.sleep(1)",
            timeout=0.01,
        ).check(work, source)
        unavailable = production.LinuxImplementationReviewAdapter(
            production.ProcessImplementationReview(("/usr/bin/python3", "-c", "import json;print(json.dumps({'decision':'CLOSE'}))")),
            production.ProcessImplementationCheck(("/missing/implementation-check",)),
            effect_adapter_enabled=False,
        ).check(work, source)
        unreadable = self.review_adapter(
            "import json;print(json.dumps({'decision':'CLOSE'}))",
            "print('not-json')",
        ).check(work, source)

        self.assertEqual("production implementation check timed out", timed_out.reason)
        self.assertEqual("production implementation check is unavailable", unavailable.reason)
        self.assertEqual("production implementation check result is unreadable", unreadable.reason)

    def test_dangerous_implementation_check_requires_enabled_effect_adapter(self) -> None:
        source = self.root / "source"
        source.mkdir()
        work = self.root / "TICKET.md"
        work.write_text("exact ticket", encoding="utf-8")
        adapter = production.LinuxImplementationReviewAdapter(
            production.ProcessImplementationReview(("/usr/bin/python3", "-c", "import json;print(json.dumps({'decision':'CLOSE'}))")),
            production.ProcessImplementationCheck(
                ("/usr/bin/python3", "-c", "import json;print(json.dumps({'status':'PASSED'}))"),
                requires_effect_adapter=True,
            ),
            effect_adapter_enabled=False,
        )

        result = adapter.check(work, source)

        self.assertEqual("dangerous implementation check authority is unavailable", result.reason)

    def test_worker_namespace_only_allows_private_workspace_writes(self) -> None:
        workspace = self.root / "workspace"
        canonical = self.root / "canonical"
        planning = self.root / "planning"
        state = self.root / "state"
        for directory in (workspace, canonical, planning, state):
            directory.mkdir()
        ticket = self.root / "unused-ticket.md"
        ticket.write_text("ticket", encoding="utf-8")
        protected = []
        for directory in (canonical, planning, state):
            path = directory / "canary.txt"
            path.write_text(directory.name, encoding="utf-8")
            protected.append((path, path.read_bytes(), path.lstat()))
        code = (
            "import json,pathlib;"
            "request=json.loads(pathlib.Path('/input/request.json').read_text());"
            "pathlib.Path('/workspace/result.txt').write_text(request['assignment']['value']);"
            f"targets={json.dumps([str(item[0]) for item in protected])};"
            "failures=[];"
            "[(pathlib.Path(p).write_text('forbidden') if False else None) for p in []];"
            "\nfor p in targets:\n"
            " try: pathlib.Path(p).write_text('forbidden')\n"
            " except Exception: failures.append(p)\n"
            "pathlib.Path('/workspace/failures.json').write_text(json.dumps(failures))"
        )
        worker = production.ProcessWorker(
            "worker-conformance",
            ("/usr/bin/python3", "-c", code),
        )

        production.LinuxWorkerAdapter().run(
            worker,
            ticket,
            workspace,
            {"value": "private-result"},
        )

        self.assertEqual("private-result", (workspace / "result.txt").read_text(encoding="utf-8"))
        self.assertEqual(len(protected), len(json.loads((workspace / "failures.json").read_text())))
        for path, raw, before in protected:
            self.assertEqual(raw, path.read_bytes())
            after = path.lstat()
            self.assertEqual((before.st_dev, before.st_ino, stat.S_IMODE(before.st_mode)), (
                after.st_dev,
                after.st_ino,
                stat.S_IMODE(after.st_mode),
            ))

    def test_production_composition_uses_module_owned_review_then_stops_at_source_adoption(self) -> None:
        project = self.root / "project"
        project.mkdir()
        (project / "app.txt").write_text("baseline", encoding="utf-8")
        spec = self.root / "SPEC.md"
        spec.write_text(
            "# Spec\nStatus: approved\nOwner: owner\n\n"
            + "".join(
                f"## {name}\nvalue\n\n"
                for name in (
                    "Problem",
                    "Desired Outcome",
                    "Requirements",
                    "Non-Goals",
                    "Implementation Constraints",
                    "Verification Expectations",
                    "UI / UX",
                    "Open Questions",
                )
            ),
            encoding="utf-8",
        )
        ticket = self.root / "TICKET.md"
        ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {spec}\nProject-Root: {project}\nWorker: \nUI: no\n\n"
            "## Goal\nImplement.\n\n## Acceptance Criteria\n- implemented\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead app.\n\n## References\nNone.\n",
            encoding="utf-8",
        )
        module = entrypoint._compose_module(
            self.root / "state",
            production.LinuxImplementationReviewAdapter(
                production.ProcessImplementationReview(
                (
                    "/usr/bin/python3",
                    "-c",
                    "import json,pathlib;pathlib.Path('/input/request.json').read_text();"
                    "p=pathlib.Path('/source/app.txt');"
                    "print(json.dumps({'decision':'CLOSE'} if p.read_text()=='implemented' else "
                    "{'decision':'ASSIGN','assignment':{'path':'app.txt','value':'implemented'}}))",
                )
                ),
                production.ProcessImplementationCheck(
                ("/usr/bin/python3", "-c", "import json;print(json.dumps({'status':'PASSED'}))")
                ),
                effect_adapter_enabled=False,
            ),
            production.LinuxWorkerAdapter(),
            production.LinuxSourceAdoptionAdapter(),
            production.LinuxFreshVerifierAdapter(production.ProcessVerifier(("/usr/bin/python3", "-c", "print('[]')"))),
            production.LinuxEvidenceRunnerAdapter(),
        )
        result = module.implement(
            ticket,
            production.ProcessWorker(
                "source-adoption-blocked-worker",
                (
                    "/usr/bin/python3",
                    "-c",
                    "import json,pathlib;r=json.loads(pathlib.Path('/input/request.json').read_text());"
                    "a=r['assignment'];(pathlib.Path('/workspace')/a['path']).write_text(a['value'])",
                ),
            ),
        )

        self.assertIsInstance(result, interface.ImplementationStopped)
        self.assertEqual(
            "conditional source adoption is unavailable",
            result.reason,
        )
        self.assertEqual(b"baseline", (project / "app.txt").read_bytes())

    def test_production_composition_closes_zero_mutation_source(self) -> None:
        project = self.root / "project"
        project.mkdir()
        (project / "app.txt").write_text("implemented", encoding="utf-8")
        spec = self.root / "SPEC.md"
        spec.write_text(
            "# Spec\nStatus: approved\nOwner: owner\n\n"
            + "".join(
                f"## {name}\nvalue\n\n"
                for name in (
                    "Problem",
                    "Desired Outcome",
                    "Requirements",
                    "Non-Goals",
                    "Implementation Constraints",
                    "Verification Expectations",
                    "UI / UX",
                    "Open Questions",
                )
            ),
            encoding="utf-8",
        )
        ticket = self.root / "TICKET.md"
        ticket.write_text(
            "# Ticket\nStatus: ready\n"
            f"Parent-Spec: {spec}\nProject-Root: {project}\nWorker: \nUI: no\n\n"
            "## Goal\nImplement.\n\n## Acceptance Criteria\n- implemented\n\n"
            "## Scope\napp.txt\n\n## Non-Goals\nNone.\n\n## Blockers\nNone.\n\n"
            "## Verification\nRead app.\n\n## References\nNone.\n",
            encoding="utf-8",
        )
        module = entrypoint._compose_module(
            self.root / "state",
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
            production.LinuxFreshVerifierAdapter(production.ProcessVerifier(("/usr/bin/python3", "-c", "print('[]')"))),
            production.LinuxEvidenceRunnerAdapter(),
        )

        result = module.implement(ticket, production.ProcessWorker("unused-zero-mutation-worker", ("/usr/bin/false",)))

        self.assertIsInstance(result, interface.Candidate)
        self.assertEqual((), result.implementation_changes)
        self.assertEqual(b"implemented", (project / "app.txt").read_bytes())

    def test_fresh_verifier_namespace_excludes_prior_context_and_source_writes(self) -> None:
        canonical = self.root / "canonical"
        retained = self.root / "retained"
        canonical.mkdir()
        retained.mkdir()
        (canonical / "app.txt").write_text("canonical", encoding="utf-8")
        (retained / "app.txt").write_text("candidate", encoding="utf-8")
        prior = self.root / "prior"
        prior.mkdir()
        canaries = []
        for name in ("verdict", "plan", "raw-artifact", "implementation-check"):
            path = prior / name
            path.write_text(f"forbidden-{name}", encoding="utf-8")
            canaries.append(str(path))
        candidate = self.candidate(retained, canonical)
        script = (
            "import json,pathlib;"
            "request=json.loads(pathlib.Path('/input/request.json').read_text());"
            f"canaries={json.dumps(canaries)};"
            "visible=[p for p in canaries if pathlib.Path(p).exists()];"
            "writes=[];"
            "\nfor p in ['/candidate/app.txt',request['candidate']['planning']['projectRoot']+'/app.txt']:\n"
            " try: pathlib.Path(p).write_text('forbidden')\n"
            " except Exception: writes.append(p)\n"
            "result=[{'observationIdentity':'source','kind':'SOURCE','criterionIndexes':[1],"
            "'requests':[{'path':'app.txt'}],'expected':'candidate'}];"
            "assert not visible and len(writes)==2 and request['candidate']['acceptanceCriteria'];"
            "print(json.dumps(result))"
        )
        adapter = production.LinuxFreshVerifierAdapter(
            production.ProcessVerifier(("/usr/bin/python3", "-c", script))
        )
        context = adapter.open(candidate, retained, ("SOURCE",), "SUPPORTED")

        plan = context.plan(candidate, retained, ("SOURCE",))

        self.assertEqual("source", plan[0]["observationIdentity"])
        self.assertEqual(b"candidate", (retained / "app.txt").read_bytes())
        self.assertEqual(b"canonical", (canonical / "app.txt").read_bytes())

    def test_evidence_runner_owns_read_only_source_and_local_evidence(self) -> None:
        canonical = self.root / "canonical"
        retained = self.root / "retained"
        scratch = self.root / "scratch"
        for directory in (canonical, retained, scratch):
            directory.mkdir()
        (canonical / "app.txt").write_text("canonical", encoding="utf-8")
        (retained / "app.txt").write_text("candidate", encoding="utf-8")
        candidate = self.candidate(retained, canonical)
        runner = production.LinuxEvidenceRunnerAdapter()
        source_observation = {
            "observationIdentity": "source",
            "kind": "SOURCE",
            "criterionIndexes": [1],
            "requests": [{"path": "app.txt"}],
            "expected": "candidate",
        }
        local_observation = {
            "observationIdentity": "local",
            "kind": "LOCAL",
            "criterionIndexes": [1],
            "requests": [
                {
                    "argv": [
                        "/usr/bin/python3",
                        "-c",
                        "import pathlib;"
                        "failed=False;"
                        "\ntry: pathlib.Path('/candidate/app.txt').write_text('forbidden')\n"
                        "except Exception: failed=True\n"
                        "pathlib.Path('/scratch/result').write_text('owned');"
                        "print('isolated' if failed else 'unsafe')",
                    ]
                }
            ],
            "expected": "isolated",
        }

        source = runner.run(candidate, retained, scratch, source_observation)
        local = runner.run(candidate, retained, scratch, local_observation)

        self.assertEqual("candidate", source["observed"])
        self.assertEqual("isolated", local["observed"])
        self.assertEqual(b"candidate", (retained / "app.txt").read_bytes())
        self.assertEqual(b"canonical", (canonical / "app.txt").read_bytes())
        self.assertTrue(local["artifact"])

    def test_source_adoption_fails_closed_before_existing_file_mutation(self) -> None:
        project = self.root / "project"
        workspace = self.root / "workspace"
        project.mkdir()
        workspace.mkdir()
        target = project / "app.txt"
        source = workspace / "app.txt"
        target.write_text("expected", encoding="utf-8")
        target.chmod(0o640)
        source.write_text("intended", encoding="utf-8")
        source.chmod(0o600)
        expected = production._physical_entry(target)
        intended = production._physical_entry(source)
        adapter = production.LinuxSourceAdoptionAdapter()

        before = target.lstat()
        with self.assertRaises(implementation.AdoptionConflict):
            adapter.apply(
                project,
                workspace,
                ({"path": "app.txt", "expected": expected, "intended": intended},),
                lambda: True,
            )
        after = target.lstat()
        self.assertEqual("expected", target.read_text(encoding="utf-8"))
        self.assertEqual((before.st_dev, before.st_ino, stat.S_IMODE(before.st_mode)), (
            after.st_dev,
            after.st_ino,
            stat.S_IMODE(after.st_mode),
        ))

    def test_source_adoption_fails_closed_before_create_directory_or_symlink(self) -> None:
        project = self.root / "project"
        workspace = self.root / "workspace"
        project.mkdir()
        workspace.mkdir()
        (workspace / "new-dir").mkdir(mode=0o750)
        (workspace / "new-link").symlink_to("new-dir")
        adapter = production.LinuxSourceAdoptionAdapter()
        changes = (
            {
                "path": "new-dir",
                "expected": None,
                "intended": production._physical_entry(workspace / "new-dir"),
            },
            {
                "path": "new-link",
                "expected": None,
                "intended": production._physical_entry(workspace / "new-link"),
            },
        )

        with self.assertRaises(implementation.AdoptionConflict):
            adapter.apply(project, workspace, changes, lambda: True)
        self.assertFalse((project / "new-dir").exists())
        self.assertFalse((project / "new-link").exists())

    def test_source_adoption_mismatch_rollback_cannot_delete_latest_user_write(self) -> None:
        project = self.root / "project"
        workspace = self.root / "workspace"
        project.mkdir()
        workspace.mkdir()
        target = project / "app.txt"
        source = workspace / "app.txt"
        target.write_text("expected", encoding="utf-8")
        source.write_text("intended", encoding="utf-8")
        expected = production._physical_entry(target)
        intended = production._physical_entry(source)
        latest = project / "latest-user.txt"
        latest.write_text("latest-user", encoding="utf-8")
        os.replace(latest, target)
        latest_inode = target.lstat().st_ino

        with self.assertRaises(implementation.AdoptionConflict):
            production.LinuxSourceAdoptionAdapter().apply(
                project,
                workspace,
                ({"path": "app.txt", "expected": expected, "intended": intended},),
                lambda: True,
            )

        self.assertEqual(b"latest-user", target.read_bytes())
        self.assertEqual(latest_inode, target.lstat().st_ino)
        self.assertFalse(latest.exists())

    def test_source_adoption_directory_mode_change_preserves_nonempty_children(self) -> None:
        project = self.root / "project"
        workspace = self.root / "workspace"
        project.mkdir()
        workspace.mkdir()
        target = project / "directory"
        source = workspace / "directory"
        target.mkdir(mode=0o755)
        source.mkdir(mode=0o700)
        child = target / "canonical-child.txt"
        child.write_text("canonical-child", encoding="utf-8")
        expected = production._physical_entry(target)
        intended = production._physical_entry(source)

        with self.assertRaises(implementation.AdoptionConflict):
            production.LinuxSourceAdoptionAdapter().apply(
                project,
                workspace,
                ({"path": "directory", "expected": expected, "intended": intended},),
                lambda: True,
            )

        self.assertEqual(b"canonical-child", child.read_bytes())
        self.assertEqual(0o755, stat.S_IMODE(target.lstat().st_mode))

    def test_authenticated_read_root_cannot_self_grant_production_authority(self) -> None:
        canonical = self.root / "canonical"
        retained = self.root / "retained"
        scratch = self.root / "scratch"
        remote = self.root / "remote"
        for directory in (canonical, retained, scratch, remote):
            directory.mkdir()
        secret = "TOP-SECRET"
        (retained / "app.txt").write_text("candidate", encoding="utf-8")
        (remote / "secret.txt").write_text(secret, encoding="utf-8")
        candidate = self.candidate(retained, canonical)
        observation = {
            "observationIdentity": "unsafe-authenticated-read",
            "kind": "READ",
            "criterionIndexes": [1],
            "requests": [{"path": "secret.txt"}],
            "expected": {
                "path": "secret.txt",
                "sha256": __import__("hashlib").sha256(secret.encode()).hexdigest(),
                "byteCount": len(secret),
            },
        }
        runner = production.LinuxEvidenceRunnerAdapter()

        with self.assertRaises(TypeError):
            production.LinuxEvidenceRunnerAdapter(remote)
        with self.assertRaises(TypeError):
            entrypoint.create_production_module(
                self.root / "state",
                ("/usr/bin/python3", "-c", "print('[]')"),
                remote,
            )
        self.assertFalse(runner.authenticated_read_enforced)
        self.assertNotIn("READ", runner.supported_observations)
        self.assertIsNone(runner.read_authority(candidate, observation))
        with self.assertRaisesRegex(RuntimeError, "authenticated read authority is unavailable"):
            runner.run(candidate, retained, scratch, observation)

    def test_multi_request_results_preserve_each_request_artifact_identity(self) -> None:
        canonical = self.root / "canonical"
        retained = self.root / "retained"
        scratch = self.root / "scratch"
        for directory in (canonical, retained, scratch):
            directory.mkdir()
        (retained / "one.txt").write_text("source-one", encoding="utf-8")
        (retained / "two.txt").write_text("source-two", encoding="utf-8")
        candidate = self.candidate(retained, canonical)
        runner = production.LinuxEvidenceRunnerAdapter()
        observations = (
            {
                "observationIdentity": "source",
                "kind": "SOURCE",
                "criterionIndexes": [1],
                "requests": [{"path": "one.txt"}, {"path": "two.txt"}],
                "expected": ["source-one", "source-two"],
            },
            {
                "observationIdentity": "local",
                "kind": "LOCAL",
                "criterionIndexes": [1],
                "requests": [
                    {"argv": ["/usr/bin/printf", "local-one"]},
                    {"argv": ["/usr/bin/printf", "local-two"]},
                ],
                "expected": ["local-one", "local-two"],
            },
        )

        for observation in observations:
            raw = runner.run(candidate, retained, scratch, observation)
            evidence, _ = verification._runner_evidence(
                candidate,
                observation,
                raw,
                interface.Currentness.CURRENT,
                interface.Currentness.CURRENT,
            )
            self.assertTrue(evidence["complete"])
            self.assertEqual(observation["requests"], [item["request"] for item in raw["subattempts"]])
            self.assertEqual(
                [item["artifactIdentity"] for item in raw["subattempts"]],
                [implementation._value_identity(item["artifact"]) for item in raw["subattempts"]],
            )
            self.assertEqual([item["observed"] for item in raw["subattempts"]], raw["observed"])
            self.assertEqual(
                [item["artifact"] for item in raw["subattempts"]],
                raw["artifact"]["subattemptArtifacts"],
            )


if __name__ == "__main__":
    unittest.main()
