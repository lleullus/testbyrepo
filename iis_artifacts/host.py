"""Canonical trusted-host API with fail-closed Assurance operations."""
from __future__ import annotations

import base64
import json
from pathlib import Path

from . import supervisor as _core
from .admission import admission_record, AdmissionError
from .store import ArtifactStoreError

HostBoundaryError = _core.HostBoundaryError
HostIntegrationUnavailable = _core.HostIntegrationUnavailable
SupervisorClient = _core.SupervisorClient
ASSURANCE = _core.ASSURANCE


class HostSupervisor(_core.HostSupervisor):
    """Shipped supervisor boundary; workers cannot mint Assurance ledger records."""

    @staticmethod
    def _strict_execution_path(binding: dict, value: str) -> str:
        source_root = Path(binding["source"]["root"]).resolve(strict=True)
        source_text = str(source_root)
        path = Path(value)
        if path.is_absolute():
            try:
                relative = path.resolve(strict=False).relative_to(source_root)
            except ValueError:
                if source_text in value:
                    raise ValueError("UNSAFE_EMBEDDED_SOURCE_PATH")
                return value
            return str(Path(binding["execution_root"]) / relative)
        if source_text in value:
            raise ValueError("UNSAFE_EMBEDDED_SOURCE_PATH")
        return value

    def _require_registered_binding(self, binding: dict) -> dict:
        if not isinstance(binding, dict):
            raise ValueError("INVALID_BINDING")
        record = ASSURANCE._binding_record(self.store, binding.get("binding_id", ""))
        if record["binding_json"] != ASSURANCE._canonical(binding):
            raise ValueError("BINDING_RECORD_MISMATCH")
        if Path(binding["source"]["root"]) != self.project_root:
            raise ValueError("FOREIGN_PROJECT")
        admission = admission_record(self.store, binding["admission_id"])
        request = json.loads(admission["request_ref_json"])
        if self.store.read_bytes(request).decode("utf-8") != self.current_request:
            raise ValueError("ADMISSION_CURRENT_REQUEST_MISMATCH")
        return record

    def _validate_gate_paths(self, baseline_path: Path, binding: dict, gate_id: str) -> None:
        self._require_registered_binding(binding)
        baseline = ASSURANCE.current(Path(baseline_path), self.store, binding)
        gate = ASSURANCE.rows(baseline["gates"], "gates")[gate_id]
        for value in gate["argv"]:
            self._strict_execution_path(binding, value)
        self._strict_execution_path(binding, gate["cwd"])
        if gate["jobs_path"] is not None:
            self._strict_execution_path(binding, gate["jobs_path"])

    def run_assurance_gate(self, baseline_path: Path, binding: dict, gate_id: str, output: Path) -> dict:
        self._validate_gate_paths(Path(baseline_path), binding, gate_id)
        return super().run_assurance_gate(Path(baseline_path), binding, gate_id, Path(output))

    def begin_assurance_invocation(self, binding: dict, kind: str, item_id: str) -> dict:
        self._require_registered_binding(binding)
        return {
            "invocation_id": ASSURANCE.begin_host_invocation(
                self.store, binding, kind, item_id
            )
        }

    def capture_assurance_evidence(
        self,
        binding: dict,
        invocation_id: str,
        files: dict[str, bytes],
    ) -> dict:
        self._require_registered_binding(binding)
        if not isinstance(files, dict) or not files:
            raise ValueError("ASSURANCE_EVIDENCE_FILES_REQUIRED")
        return {
            "evidence": ASSURANCE.capture_invocation_evidence(
                self.store, binding, invocation_id, files
            )
        }

    def complete_assurance_invocation(
        self,
        binding: dict,
        invocation_id: str,
        result: dict,
    ) -> dict:
        self._require_registered_binding(binding)
        return ASSURANCE.complete_host_invocation(
            self.store, binding, invocation_id, result
        )

    def record_assurance_effect(
        self,
        binding: dict,
        effect_id: str,
        *,
        owner: str,
        state: str,
        evidence: list[dict],
    ) -> dict:
        self._require_registered_binding(binding)
        if state == "SETTLED" and not evidence:
            raise ValueError("MISSING_EVIDENCE")
        ASSURANCE.record_effect(
            self.store,
            binding,
            effect_id,
            owner=owner,
            state=state,
            evidence=evidence,
        )
        return {"status": "RECORDED", "effect_id": effect_id, "state": state}

    def _validate_assurance_ledgers(self, binding: dict) -> None:
        self._require_registered_binding(binding)
        with self.store.connect() as db:
            invocations = db.execute(
                "SELECT * FROM assurance_invocations WHERE binding_id=? ORDER BY started_sequence",
                (binding["binding_id"],),
            ).fetchall()
            effects = {
                row["effect_id"]: row
                for row in db.execute(
                    "SELECT * FROM assurance_effects WHERE binding_id=? ORDER BY sequence",
                    (binding["binding_id"],),
                ).fetchall()
            }
        for row in invocations:
            if row["status"] != "COMPLETE" or not row["result_ref_json"]:
                continue
            ref = json.loads(row["result_ref_json"])
            self.store.assert_producer(
                ref,
                run_id=binding["run_id"],
                invocation_id=row["invocation_id"],
                kind="assurance-result",
            )
            result = json.loads(self.store.read_bytes(ref))
            reported = result.get("effects")
            if not isinstance(reported, list) or not all(
                isinstance(item, str) and item for item in reported
            ):
                raise ValueError("INVALID_RESULT_EFFECTS")
            if len(reported) != len(set(reported)):
                raise ValueError("DUPLICATE_RESULT_EFFECT")
            if not set(reported).issubset(effects):
                raise ValueError("UNRECORDED_EFFECT")
        for row in effects.values():
            evidence = json.loads(row["evidence_json"])
            if row["state"] == "SETTLED" and not evidence:
                raise ValueError("MISSING_EVIDENCE")
            ASSURANCE.effect_evidence(self.store, binding, evidence, settled=row["state"] == "SETTLED")

    def close_assurance(self, baseline_path: Path, binding: dict) -> dict:
        try:
            self._validate_assurance_ledgers(binding)
        except (ValueError, KeyError, TypeError, OSError, ArtifactStoreError, AdmissionError) as exc:
            return {
                "schema": "iis-assurance-closure/v3",
                "binding": binding.get("binding_id") if isinstance(binding, dict) else None,
                "status": "BLOCKED",
                "reasons": [str(exc)],
            }
        return super().close_assurance(Path(baseline_path), binding)

    @staticmethod
    def _decode_assurance_files(values: object) -> dict[str, bytes]:
        if not isinstance(values, dict) or not values:
            raise ValueError("ASSURANCE_EVIDENCE_FILES_REQUIRED")
        decoded: dict[str, bytes] = {}
        for path, content in values.items():
            if not isinstance(path, str) or not path or not isinstance(content, str):
                raise ValueError("INVALID_ASSURANCE_EVIDENCE_FILES")
            decoded[path] = base64.b64decode(content, validate=True)
        return decoded

    def handle_admin(self, request: dict) -> dict:
        action = request.get("action")
        if action == "begin_assurance_invocation":
            return self.begin_assurance_invocation(
                request["binding"], request["kind"], request["item_id"]
            )
        if action == "capture_assurance_evidence":
            return self.capture_assurance_evidence(
                request["binding"],
                request["invocation_id"],
                self._decode_assurance_files(request["files_b64"]),
            )
        if action == "complete_assurance_invocation":
            return self.complete_assurance_invocation(
                request["binding"], request["invocation_id"], request["result"]
            )
        if action == "record_assurance_effect":
            return self.record_assurance_effect(
                request["binding"],
                request["effect_id"],
                owner=request["owner"],
                state=request["state"],
                evidence=request.get("evidence", []),
            )
        return super().handle_admin(request)


__all__ = [
    "HostBoundaryError",
    "HostIntegrationUnavailable",
    "HostSupervisor",
    "SupervisorClient",
]
