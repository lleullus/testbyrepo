from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Protocol

from implementation_verification import Candidate


class FixedEffectAdapter(Protocol):
    identity: str
    fixed_requests_enforced: bool
    authoritative_readback_enforced: bool
    redaction_enforced: bool

    def authority(self, binding: dict[str, object], effect: dict[str, object]) -> object: ...

    def dispatch(
        self,
        binding: dict[str, object],
        effect: dict[str, object],
        stage: str,
        request: object,
    ) -> object: ...


@dataclass(frozen=True)
class EffectObservationResult:
    raw: dict[str, object]
    unresolved: dict[str, object] | None = None
    projection: dict[str, object] | None = None
    resolved_identities: tuple[str, ...] = ()


_EFFECT_FIELDS = {
    "adapterIdentity",
    "intent",
    "target",
    "occurrence",
    "actionRequest",
    "readbackRequests",
    "cleanupRequest",
    "cleanupReadbackRequests",
    "finalDisposition",
    "safetyProperty",
}
_AUTHORITY_FIELDS = {
    "adapterIdentity",
    "binding",
    "intent",
    "target",
    "occurrence",
    "actionRequest",
    "cleanupRequest",
    "finalDisposition",
    "safetyProperty",
    "outsideWritableScope",
    "current",
    "credentialOpaque",
    "redactionEnforced",
    "allowNewOccurrence",
}
_DISPOSITIONS = {"RETAIN", "REMOVE", "RESTORE", "TERMINAL_RECEIPT"}
_SAFETY_PROPERTIES = {"NO_REPLAY"}


def _identity(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_effect(effect: object) -> dict[str, object] | None:
    if not isinstance(effect, dict) or set(effect) != _EFFECT_FIELDS:
        return None
    if (
        not isinstance(effect["adapterIdentity"], str)
        or not effect["adapterIdentity"]
        or not isinstance(effect["readbackRequests"], (list, tuple))
        or not isinstance(effect["cleanupReadbackRequests"], (list, tuple))
        or effect["finalDisposition"] not in _DISPOSITIONS
        or effect["safetyProperty"] not in _SAFETY_PROPERTIES
    ):
        return None
    action = effect["actionRequest"]
    cleanup = effect["cleanupRequest"]
    readbacks = list(effect["readbackRequests"])
    cleanup_readbacks = list(effect["cleanupReadbackRequests"])
    if action is None and cleanup is not None:
        return None
    if cleanup is None and cleanup_readbacks:
        return None
    if cleanup is not None and not cleanup_readbacks:
        return None
    if effect["finalDisposition"] == "TERMINAL_RECEIPT":
        if cleanup is not None:
            return None
    elif not readbacks:
        return None
    normalized = dict(effect)
    normalized["readbackRequests"] = readbacks
    normalized["cleanupReadbackRequests"] = cleanup_readbacks
    try:
        _identity(normalized)
    except (TypeError, ValueError):
        return None
    return normalized


def effect_requests(effect: dict[str, object]) -> list[object]:
    requests: list[object] = []
    if effect["actionRequest"] is not None:
        requests.append(effect["actionRequest"])
    requests.extend(effect["readbackRequests"])  # type: ignore[arg-type]
    if effect["cleanupRequest"] is not None:
        requests.append(effect["cleanupRequest"])
    requests.extend(effect["cleanupReadbackRequests"])  # type: ignore[arg-type]
    return requests


class EffectObservationModule:
    def __init__(self, adapter: FixedEffectAdapter) -> None:
        self._adapter = adapter

    @property
    def available(self) -> bool:
        return (
            isinstance(getattr(self._adapter, "identity", None), str)
            and bool(self._adapter.identity)
            and getattr(self._adapter, "fixed_requests_enforced", False) is True
            and getattr(self._adapter, "authoritative_readback_enforced", False) is True
            and getattr(self._adapter, "redaction_enforced", False) is True
        )

    @staticmethod
    def _binding(candidate: Candidate, observation: dict[str, object]) -> dict[str, object]:
        return {
            "work": str(candidate.work),
            "candidateIdentity": candidate.result_identity,
            "planning": candidate.planning,
            "sourceIdentity": candidate.source["identity"],
            "observationIdentity": observation["observationIdentity"],
        }

    @staticmethod
    def _keys(effect: dict[str, object]) -> tuple[str, str, str]:
        target = _identity(
            {"adapterIdentity": effect["adapterIdentity"], "target": effect["target"]}
        )
        consequence = _identity(
            {
                "adapterIdentity": effect["adapterIdentity"],
                "intent": effect["intent"],
                "target": effect["target"],
                "finalDisposition": effect["finalDisposition"],
                "safetyProperty": effect["safetyProperty"],
            }
        )
        occurrence = _identity(effect["occurrence"])
        return target, consequence, occurrence

    @staticmethod
    def _authority_matches(
        authority: object,
        binding: dict[str, object],
        effect: dict[str, object],
    ) -> bool:
        return (
            isinstance(authority, dict)
            and set(authority) == _AUTHORITY_FIELDS
            and authority["adapterIdentity"] == effect["adapterIdentity"]
            and authority["binding"] == binding
            and authority["intent"] == effect["intent"]
            and authority["target"] == effect["target"]
            and authority["occurrence"] == effect["occurrence"]
            and authority["actionRequest"] == effect["actionRequest"]
            and authority["cleanupRequest"] == effect["cleanupRequest"]
            and authority["finalDisposition"] == effect["finalDisposition"]
            and authority["safetyProperty"] == effect["safetyProperty"]
            and authority["outsideWritableScope"] is True
            and authority["current"] is True
            and authority["credentialOpaque"] is True
            and authority["redactionEnforced"] is True
            and isinstance(authority["allowNewOccurrence"], bool)
        )

    @staticmethod
    def _attempt(request: object, stage: str, value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            return {
                "request": request,
                "stage": stage,
                "status": "MALFORMED",
                "authoritative": False,
                "redacted": False,
            }
        attempt = dict(value)
        attempt["request"] = request
        attempt["stage"] = stage
        if not isinstance(attempt.get("status"), str):
            attempt["status"] = "MALFORMED"
        if attempt.get("redacted") is not True:
            return {
                "request": request,
                "stage": stage,
                "status": "UNSAFE_REDACTION",
                "authoritative": False,
                "redacted": False,
            }
        try:
            _identity(attempt)
        except (TypeError, ValueError):
            return {
                "request": request,
                "stage": stage,
                "status": "MALFORMED",
                "authoritative": False,
                "redacted": False,
            }
        return attempt

    def observe(
        self,
        candidate: Candidate,
        observation: dict[str, object],
        prior_facts: tuple[object, ...],
        mark_may_have_run: Callable[[dict[str, object]], None],
    ) -> EffectObservationResult:
        effect = normalize_effect(observation.get("effect"))
        binding = self._binding(candidate, observation)
        if (
            not self.available
            or effect is None
            or effect["adapterIdentity"] != self._adapter.identity
            or observation.get("requests") != effect_requests(effect)
        ):
            return EffectObservationResult(
                {"status": "UNSAFE_EFFECT_PLAN", "subattempts": [], "artifact": None}
            )
        try:
            authority = self._adapter.authority(binding, effect)
        except Exception:
            authority = None
        if not self._authority_matches(authority, binding, effect):
            return EffectObservationResult(
                {"status": "MISSING_CURRENT_AUTHORITY", "subattempts": [], "artifact": None}
            )

        target_identity, consequence_identity, occurrence_identity = self._keys(effect)
        overlap: list[dict[str, object]] = []
        for item in prior_facts:
            if (
                isinstance(item, dict)
                and item.get("adapterIdentity") == effect["adapterIdentity"]
                and item.get("targetIdentity") == target_identity
                and item.get("consequenceIdentity") == consequence_identity
            ):
                overlap.append(item)
        same_occurrence = [
            item for item in overlap if item.get("occurrenceIdentity") == occurrence_identity
        ]
        different_occurrence = [
            item for item in overlap if item.get("occurrenceIdentity") != occurrence_identity
        ]
        action_request = effect["actionRequest"]
        suppress_action = bool(same_occurrence)
        if different_occurrence and authority["allowNewOccurrence"] is not True:
            return EffectObservationResult(
                {"status": "UNSAFE_PRIOR_EFFECT", "subattempts": [], "artifact": None}
            )

        attempts: list[dict[str, object]] = []
        action_may_have_run = False
        if action_request is not None and not suppress_action:
            marker = {
                "binding": binding,
                "adapterIdentity": effect["adapterIdentity"],
                "targetIdentity": target_identity,
                "consequenceIdentity": consequence_identity,
                "occurrenceIdentity": occurrence_identity,
                "stage": "ACTION",
                "request": action_request,
                "mayHaveRun": True,
            }
            mark_may_have_run(marker)
            action_may_have_run = True
            try:
                value = self._adapter.dispatch(binding, effect, "ACTION", action_request)
            except Exception:
                value = {"status": "RESPONSE_LOST", "redacted": True, "authoritative": False}
            attempts.append(self._attempt(action_request, "ACTION", value))
        elif action_request is not None:
            attempts.append(
                {
                    "request": action_request,
                    "stage": "ACTION",
                    "status": "SUPPRESSED_PRIOR_OCCURRENCE",
                    "authoritative": False,
                    "redacted": True,
                }
            )

        for request in effect["readbackRequests"]:  # type: ignore[union-attr]
            try:
                value = self._adapter.dispatch(binding, effect, "READBACK", request)
            except Exception:
                value = {"status": "RESPONSE_LOST", "redacted": True, "authoritative": False}
            attempts.append(self._attempt(request, "READBACK", value))

        cleanup_request = effect["cleanupRequest"]
        cleanup_may_have_run = False
        prior_unresolved = any(item.get("state") == "UNRESOLVED" for item in same_occurrence)
        prior_cleanup_may_have_run = any(
            item.get("cleanupMayHaveRun") is True or item.get("stage") == "CLEANUP"
            for item in same_occurrence
        )
        if cleanup_request is not None and (
            action_may_have_run or prior_unresolved
        ) and not prior_cleanup_may_have_run:
            marker = {
                "binding": binding,
                "adapterIdentity": effect["adapterIdentity"],
                "targetIdentity": target_identity,
                "consequenceIdentity": consequence_identity,
                "occurrenceIdentity": occurrence_identity,
                "stage": "CLEANUP",
                "request": cleanup_request,
                "mayHaveRun": True,
            }
            mark_may_have_run(marker)
            cleanup_may_have_run = True
            try:
                value = self._adapter.dispatch(binding, effect, "CLEANUP", cleanup_request)
            except Exception:
                value = {"status": "RESPONSE_LOST", "redacted": True, "authoritative": False}
            attempts.append(self._attempt(cleanup_request, "CLEANUP", value))
            for request in effect["cleanupReadbackRequests"]:  # type: ignore[union-attr]
                try:
                    value = self._adapter.dispatch(binding, effect, "CLEANUP_READBACK", request)
                except Exception:
                    value = {
                        "status": "RESPONSE_LOST",
                        "redacted": True,
                        "authoritative": False,
                    }
                attempts.append(self._attempt(request, "CLEANUP_READBACK", value))
        elif cleanup_request is not None:
            attempts.append(
                {
                    "request": cleanup_request,
                    "stage": "CLEANUP",
                    "status": "SUPPRESSED_PRIOR_COMPLETION",
                    "authoritative": False,
                    "redacted": True,
                }
            )
            for request in effect["cleanupReadbackRequests"]:  # type: ignore[union-attr]
                try:
                    value = self._adapter.dispatch(binding, effect, "CLEANUP_READBACK", request)
                except Exception:
                    value = {
                        "status": "RESPONSE_LOST",
                        "redacted": True,
                        "authoritative": False,
                    }
                attempts.append(self._attempt(request, "CLEANUP_READBACK", value))

        readbacks = [item for item in attempts if item.get("stage") == "READBACK"]
        cleanup_readbacks = [
            item for item in attempts if item.get("stage") == "CLEANUP_READBACK"
        ]
        if effect["finalDisposition"] == "TERMINAL_RECEIPT":
            action_attempts = [item for item in attempts if item.get("stage") == "ACTION"]
            observed_complete = any(
                item.get("authoritative") is True
                and item.get("terminalReceipt") is True
                and item.get("finalDispositionConfirmed") is True
                for item in action_attempts
            )
        else:
            observed_complete = any(
                item.get("authoritative") is True
                and item.get("matchesExpected") is True
                and item.get("finalDispositionConfirmed") is True
                for item in readbacks
            )
        cleanup_complete = cleanup_request is None or any(
            item.get("authoritative") is True
            and item.get("finalDispositionConfirmed") is True
            for item in cleanup_readbacks
        )
        redaction_safe = all(item.get("redacted") is True for item in attempts)
        complete = observed_complete and cleanup_complete and redaction_safe

        fact_base: dict[str, object] = {
            "work": str(candidate.work),
            "adapterIdentity": effect["adapterIdentity"],
            "targetIdentity": target_identity,
            "consequenceIdentity": consequence_identity,
            "occurrenceIdentity": occurrence_identity,
            "finalDisposition": effect["finalDisposition"],
            "safetyProperty": effect["safetyProperty"],
        }
        resolved = tuple(
            item["identity"]
            for item in same_occurrence
            if item.get("state") == "UNRESOLVED"
            and isinstance(item.get("identity"), str)
        )
        if complete:
            projection = dict(fact_base)
            projection["state"] = "COMPLETED"
            projection["identity"] = _identity(projection)
            raw = {
                "status": "COMPLETE",
                "subattempts": attempts,
                "observed": observation["expected"],
                "artifact": {
                    "binding": binding,
                    "authority": {
                        "identity": _identity(authority),
                        "outsideWritableScope": True,
                        "current": True,
                    },
                    "target": effect["target"],
                    "fixedRequests": observation["requests"],
                    "subattempts": attempts,
                    "finalDisposition": effect["finalDisposition"],
                    "unresolved": False,
                    "redacted": True,
                },
            }
            return EffectObservationResult(raw, projection=projection, resolved_identities=resolved)

        may_have_run = action_may_have_run or cleanup_may_have_run or any(
            item.get("state") == "UNRESOLVED" for item in same_occurrence
        )
        if may_have_run:
            unresolved = dict(fact_base)
            unresolved.update(
                {
                    "candidateIdentity": candidate.result_identity,
                    "observationIdentity": observation["observationIdentity"],
                    "target": effect["target"],
                    "requests": observation["requests"],
                    "mayHaveRun": True,
                    "actionMayHaveRun": action_may_have_run or prior_unresolved,
                    "cleanupMayHaveRun": cleanup_may_have_run
                    or prior_cleanup_may_have_run,
                    "state": "UNRESOLVED",
                }
            )
            unresolved["identity"] = _identity(unresolved)
            return EffectObservationResult(
                {
                    "status": "UNRESOLVED_EFFECT",
                    "subattempts": attempts,
                    "observed": None,
                    "artifact": None,
                    "target": effect["target"],
                    "liveOwnerAbsent": True,
                },
                unresolved=unresolved,
            )
        return EffectObservationResult(
            {"status": "INCONCLUSIVE_READBACK", "subattempts": attempts, "artifact": None}
        )
