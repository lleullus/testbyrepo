from __future__ import annotations

import fcntl
from pathlib import Path
from typing import Iterable, Protocol

from durable_backend import VerificationCompletion
from durable_work import DurableResultIntegrityError, DurableWorkStore
from effect_observation import EffectObservationModule, effect_requests, normalize_effect
from implementation_execution import (
    _capture,
    _overlaps,
    _read_json,
    _value_identity,
    _write_json,
    _write_json_once,
)
from implementation_verification import (
    Candidate,
    CriterionOutcome,
    CriterionResult,
    Currentness,
    PublicResult,
)


class FreshVerifierContext(Protocol):
    identity: str

    def plan(
        self,
        candidate: Candidate,
        retained_source: Path,
        supported_observations: tuple[str, ...],
    ) -> object: ...

    def assess(
        self,
        candidate: Candidate,
        plan: dict[str, object],
        evidence: tuple[dict[str, object], ...],
    ) -> object: ...


class FreshVerifierAdapter(Protocol):
    fresh_context_enforced: bool
    read_only_enforced: bool

    def open(
        self,
        candidate: Candidate,
        retained_source: Path,
        supported_observations: tuple[str, ...],
        effect_safety: str,
    ) -> FreshVerifierContext: ...


class EvidenceRunnerAdapter(Protocol):
    read_only_enforced: bool
    authenticated_read_enforced: bool
    effect_observation_enforced: bool
    supported_observations: tuple[str, ...]

    def read_authority(
        self,
        candidate: Candidate,
        observation: dict[str, object],
    ) -> object: ...

    def run(
        self,
        candidate: Candidate,
        retained_source: Path,
        scratch_root: Path,
        observation: dict[str, object],
    ) -> object: ...


def _candidate_source(candidate: Candidate) -> tuple[Path, str]:
    source = candidate.source
    if not isinstance(source, dict):
        raise DurableResultIntegrityError("Candidate source record is malformed")
    retained_root = source.get("retainedRoot")
    identity = source.get("identity")
    if not isinstance(retained_root, str) or not isinstance(identity, str):
        raise DurableResultIntegrityError("Candidate source record is malformed")
    root = Path(retained_root)
    try:
        _, observed = _capture(root)
    except Exception as exc:
        raise DurableResultIntegrityError("retained Candidate source is unreadable") from exc
    if observed != identity:
        raise DurableResultIntegrityError("retained Candidate source differs")
    return root, identity


_READ_AUTHORITY_FIELDS = {
    "binding",
    "outsideWritableScope",
    "current",
    "credentialOpaque",
    "redactionEnforced",
}


def _read_binding(candidate: Candidate, observation: dict[str, object]) -> dict[str, object]:
    return {
        "work": str(candidate.work),
        "candidateIdentity": candidate.result_identity,
        "planning": candidate.planning,
        "sourceIdentity": candidate.source["identity"],
        "observationIdentity": observation["observationIdentity"],
        "requests": observation["requests"],
    }


def _read_authority_matches(
    candidate: Candidate,
    observation: dict[str, object],
    authority: object,
) -> bool:
    return (
        isinstance(authority, dict)
        and set(authority) == _READ_AUTHORITY_FIELDS
        and authority["binding"] == _read_binding(candidate, observation)
        and authority["outsideWritableScope"] is True
        and authority["current"] is True
        and authority["credentialOpaque"] is True
        and authority["redactionEnforced"] is True
    )


def _unsafe_read_result(observation: dict[str, object]) -> dict[str, object]:
    return {
        "status": "UNSAFE_REDACTION",
        "subattempts": [
            {"request": request, "status": "UNSAFE_REDACTION"}
            for request in observation["requests"]
        ],
        "observed": None,
        "artifact": None,
    }


def _normalize_plan(candidate: Candidate, source_identity: str, proposed: object) -> dict[str, object] | None:
    if not isinstance(proposed, (list, tuple)):
        return None
    observations: list[dict[str, object]] = []
    identities: set[str] = set()
    coverage = [0 for _ in candidate.acceptance_criteria]
    for item in proposed:
        if not isinstance(item, dict) or not {
            "observationIdentity",
            "kind",
            "criterionIndexes",
            "requests",
            "expected",
        }.issubset(item):
            return None
        identity = item["observationIdentity"]
        kind = item["kind"]
        indexes = item["criterionIndexes"]
        requests = item["requests"]
        if (
            not isinstance(identity, str)
            or not identity
            or identity in identities
            or kind not in {"SOURCE", "LOCAL", "READ", "EFFECT"}
            or not isinstance(indexes, (list, tuple))
            or not indexes
            or len(set(indexes)) != len(indexes)
            or not isinstance(requests, (list, tuple))
            or not requests
        ):
            return None
        for index in indexes:
            if not isinstance(index, int) or isinstance(index, bool) or not 1 <= index <= len(coverage):
                return None
            coverage[index - 1] += 1
        normalized = {
            "observationIdentity": identity,
            "kind": kind,
            "criterionIndexes": list(indexes),
            "requests": list(requests),
            "expected": item["expected"],
        }
        if kind == "EFFECT":
            effect_fields = {
                "observationIdentity",
                "kind",
                "criterionIndexes",
                "requests",
                "expected",
                "effect",
            }
            if set(item) == effect_fields - {"effect"}:
                pass
            elif set(item) != effect_fields:
                return None
            else:
                effect = normalize_effect(item["effect"])
                if effect is None or list(requests) != effect_requests(effect):
                    return None
                normalized["effect"] = effect
        elif set(item) != {
            "observationIdentity",
            "kind",
            "criterionIndexes",
            "requests",
            "expected",
        }:
            return None
        try:
            _value_identity(normalized)
        except (TypeError, ValueError):
            return None
        identities.add(identity)
        observations.append(normalized)
    if not observations or any(count == 0 for count in coverage):
        return None
    plan: dict[str, object] = {
        "candidateIdentity": candidate.result_identity,
        "planning": candidate.planning,
        "acceptanceCriteria": list(candidate.acceptance_criteria),
        "sourceIdentity": source_identity,
        "observations": observations,
    }
    plan["planIdentity"] = _value_identity(plan)
    return plan


def _incomplete_evidence(
    candidate: Candidate,
    observation: dict[str, object],
    status: str,
    pre_currentness: Currentness,
    post_currentness: Currentness,
) -> dict[str, object]:
    return {
        "candidateIdentity": candidate.result_identity,
        "planning": candidate.planning,
        "sourceIdentity": candidate.source["identity"],
        "observationIdentity": observation["observationIdentity"],
        "kind": observation["kind"],
        "criterionIndexes": observation["criterionIndexes"],
        "requests": observation["requests"],
        "expected": observation["expected"],
        "preCurrentness": pre_currentness.value,
        "postCurrentness": post_currentness.value,
        "runnerStatus": status,
        "subattempts": [],
        "observed": None,
        "artifact": None,
        "artifactIdentity": None,
        "complete": False,
    }


def _runner_evidence(
    candidate: Candidate,
    observation: dict[str, object],
    raw: object,
    pre_currentness: Currentness,
    post_currentness: Currentness,
) -> tuple[dict[str, object], dict[str, object] | None]:
    if not isinstance(raw, dict):
        return (
            _incomplete_evidence(
                candidate,
                observation,
                "MALFORMED_RUNNER_RESULT",
                pre_currentness,
                post_currentness,
            ),
            None,
        )
    status = raw.get("status")
    subattempts = raw.get("subattempts")
    if not isinstance(status, str) or not isinstance(subattempts, list):
        return (
            _incomplete_evidence(
                candidate,
                observation,
                "MALFORMED_RUNNER_RESULT",
                pre_currentness,
                post_currentness,
            ),
            None,
        )
    try:
        _value_identity(raw)
    except (TypeError, ValueError):
        return (
            _incomplete_evidence(
                candidate,
                observation,
                "MALFORMED_RUNNER_RESULT",
                pre_currentness,
                post_currentness,
            ),
            None,
        )
    requests = observation["requests"]
    request_binding = (
        len(subattempts) == len(requests)
        and all(
            isinstance(attempt, dict)
            and attempt.get("request") == request
            and isinstance(attempt.get("status"), str)
            for attempt, request in zip(subattempts, requests)
        )
    )
    artifact = raw.get("artifact")
    artifact_identity = None if artifact is None else _value_identity(artifact)
    complete = status == "COMPLETE" and request_binding and artifact_identity is not None
    evidence = {
        "candidateIdentity": candidate.result_identity,
        "planning": candidate.planning,
        "sourceIdentity": candidate.source["identity"],
        "observationIdentity": observation["observationIdentity"],
        "kind": observation["kind"],
        "criterionIndexes": observation["criterionIndexes"],
        "requests": observation["requests"],
        "expected": observation["expected"],
        "preCurrentness": pre_currentness.value,
        "postCurrentness": post_currentness.value,
        "runnerStatus": status,
        "subattempts": subattempts,
        "observed": raw.get("observed"),
        "artifact": artifact,
        "artifactIdentity": artifact_identity,
        "complete": complete,
    }
    unresolved = None
    if status == "UNRESOLVED_EFFECT":
        target = raw.get("target")
        if raw.get("liveOwnerAbsent") is not True or target is None:
            raise RuntimeError("unresolved effect cannot be safely retained")
        unresolved_value = {
            "candidateIdentity": candidate.result_identity,
            "observationIdentity": observation["observationIdentity"],
            "requests": observation["requests"],
            "target": target,
            "mayHaveRun": True,
        }
        unresolved_value["identity"] = _value_identity(unresolved_value)
        unresolved = unresolved_value
    return evidence, unresolved


def _evidence_by_identity(
    evidence: Iterable[dict[str, object]],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for item in evidence:
        identity = item.get("observationIdentity")
        if isinstance(identity, str):
            result[identity] = item
    return result


def _undetermined_results(
    candidate: Candidate,
    evidence: tuple[dict[str, object], ...],
) -> tuple[CriterionResult, ...]:
    return tuple(
        CriterionResult(
            criterion,
            CriterionOutcome.UNDETERMINED,
            tuple(item for item in evidence if index in item.get("criterionIndexes", [])),
        )
        for index, criterion in enumerate(candidate.acceptance_criteria, start=1)
    )


def _assess_results(
    candidate: Candidate,
    plan: dict[str, object],
    evidence: tuple[dict[str, object], ...],
    claims: object,
    final_currentness: Currentness,
) -> tuple[CriterionResult, ...]:
    if not isinstance(claims, (list, tuple)) or len(claims) != len(candidate.acceptance_criteria):
        return _undetermined_results(candidate, evidence)
    by_index: dict[int, dict[str, object]] = {}
    for claim in claims:
        if not isinstance(claim, dict):
            return _undetermined_results(candidate, evidence)
        index = claim.get("criterionIndex")
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 1 <= index <= len(candidate.acceptance_criteria)
            or index in by_index
            or not isinstance(claim.get("outcome"), str)
            or not isinstance(claim.get("evidenceObservationIdentities"), (list, tuple))
        ):
            return _undetermined_results(candidate, evidence)
        by_index[index] = claim
    if len(by_index) != len(candidate.acceptance_criteria):
        return _undetermined_results(candidate, evidence)

    observations = plan["observations"]
    evidence_map = _evidence_by_identity(evidence)
    results: list[CriterionResult] = []
    for index, criterion in enumerate(candidate.acceptance_criteria, start=1):
        obligation_ids = {
            item["observationIdentity"]
            for item in observations
            if index in item["criterionIndexes"]
        }
        claim = by_index[index]
        reference_ids = claim["evidenceObservationIdentities"]
        if (
            len(set(reference_ids)) != len(reference_ids)
            or any(identity not in obligation_ids or identity not in evidence_map for identity in reference_ids)
        ):
            results.append(CriterionResult(criterion, CriterionOutcome.UNDETERMINED))
            continue
        referenced = tuple(evidence_map[identity] for identity in reference_ids)
        try:
            claimed_outcome = CriterionOutcome(claim["outcome"])
        except ValueError:
            claimed_outcome = CriterionOutcome.UNDETERMINED
        if claimed_outcome is CriterionOutcome.SATISFIED:
            allowed = (
                set(reference_ids) == obligation_ids
                and bool(referenced)
                and final_currentness is Currentness.CURRENT
                and all(
                    item.get("complete") is True
                    and item.get("preCurrentness") == Currentness.CURRENT.value
                    and item.get("postCurrentness") == Currentness.CURRENT.value
                    for item in referenced
                )
            )
        elif claimed_outcome is CriterionOutcome.NOT_SATISFIED:
            allowed = bool(referenced) and all(
                item.get("complete") is True
                and item.get("preCurrentness") == Currentness.CURRENT.value
                for item in referenced
            )
        else:
            allowed = False
        if allowed:
            results.append(CriterionResult(criterion, claimed_outcome, referenced))
        else:
            relevant = tuple(
                item for item in evidence if index in item.get("criterionIndexes", [])
            )
            results.append(CriterionResult(criterion, CriterionOutcome.UNDETERMINED, relevant))
    return tuple(results)


def _has_supported_contradiction(claims: object, evidence: tuple[dict[str, object], ...]) -> bool:
    if not isinstance(claims, (list, tuple)):
        return False
    evidence_map = _evidence_by_identity(evidence)
    for claim in claims:
        if not isinstance(claim, dict) or claim.get("outcome") != CriterionOutcome.NOT_SATISFIED.value:
            continue
        identities = claim.get("evidenceObservationIdentities")
        if not isinstance(identities, (list, tuple)) or not identities:
            continue
        referenced = [evidence_map.get(identity) for identity in identities]
        if all(
            item is not None
            and item.get("complete") is True
            and item.get("preCurrentness") == Currentness.CURRENT.value
            for item in referenced
        ):
            return True
    return False


def _results_payload(results: tuple[CriterionResult, ...]) -> list[dict[str, object]]:
    return [
        {
            "criterionIndex": index,
            "outcome": result.outcome.value,
            "evidence": list(result.evidence),
        }
        for index, result in enumerate(results, start=1)
    ]


def _results_from_payload(
    candidate: Candidate,
    payload: object,
) -> tuple[CriterionResult, ...]:
    if not isinstance(payload, list) or len(payload) != len(candidate.acceptance_criteria):
        raise RuntimeError("private verification result progress is malformed")
    results: list[CriterionResult] = []
    for expected_index, item in enumerate(payload, start=1):
        if (
            not isinstance(item, dict)
            or item.get("criterionIndex") != expected_index
            or not isinstance(item.get("evidence"), list)
        ):
            raise RuntimeError("private verification result progress is malformed")
        results.append(
            CriterionResult(
                candidate.acceptance_criteria[expected_index - 1],
                CriterionOutcome(item["outcome"]),
                tuple(item["evidence"]),
            )
        )
    return tuple(results)


class VerificationExecution:
    def __init__(
        self,
        state_root: str | Path,
        store: DurableWorkStore,
        fresh_verifier: FreshVerifierAdapter,
        runner: EvidenceRunnerAdapter,
        observe_currentness,
        effect_observer: EffectObservationModule | None = None,
    ) -> None:
        self._state_root = Path(state_root).expanduser().resolve(strict=False)
        self._store = store
        self._fresh_verifier = fresh_verifier
        self._runner = runner
        self._observe_currentness = observe_currentness
        self._effect_observer = effect_observer

    def _supported_observations(self) -> tuple[str, ...]:
        kinds = tuple(
            kind
            for kind in self._runner.supported_observations
            if kind in {"SOURCE", "LOCAL"}
        )
        if (
            "READ" in self._runner.supported_observations
            and getattr(self._runner, "authenticated_read_enforced", False) is True
            and callable(getattr(self._runner, "read_authority", None))
        ):
            kinds += ("READ",)
        if self._effect_observer is not None and self._effect_observer.available:
            kinds += ("EFFECT",)
        return kinds

    def _transition_root(self, transition_identity: str) -> Path:
        return self._state_root / "verification" / _value_identity(transition_identity)

    def _persist_completion(
        self,
        progress_path: Path,
        progress: dict[str, object],
        results: tuple[CriterionResult, ...],
    ) -> VerificationCompletion:
        progress["criterionResults"] = _results_payload(results)
        _write_json(progress_path, progress)
        unresolved = progress.get("unresolvedObservations", [])
        resolved = progress.get("resolvedObservationIdentities", [])
        projections = progress.get("effectSafetyProjections", [])
        if (
            not isinstance(unresolved, list)
            or not isinstance(resolved, list)
            or not all(isinstance(item, str) for item in resolved)
            or not isinstance(projections, list)
        ):
            raise RuntimeError("private unresolved observation progress is malformed")
        return VerificationCompletion(
            results,
            tuple(unresolved),
            tuple(resolved),
            tuple(projections),
        )

    def _evidence(self, progress: dict[str, object]) -> tuple[dict[str, object], ...]:
        refs = progress.get("evidenceRefs", [])
        if not isinstance(refs, list):
            raise RuntimeError("private evidence progress is malformed")
        return tuple(_read_json(Path(ref)) for ref in refs)

    def verify(
        self,
        candidate: Candidate,
        transition_identity: str,
        *,
        reenter: bool,
    ) -> VerificationCompletion:
        transition_root = self._transition_root(transition_identity)
        transition_root.mkdir(parents=True, exist_ok=True)
        with (transition_root / "execution.lock").open("a+b") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            return self._verify_locked(candidate, transition_root, reenter=reenter)

    def _verify_locked(
        self,
        candidate: Candidate,
        transition_root: Path,
        *,
        reenter: bool,
    ) -> VerificationCompletion:
        retained_root, source_identity = _candidate_source(candidate)
        progress_path = transition_root / "progress.json"
        if progress_path.exists():
            progress = _read_json(progress_path)
            if progress.get("candidateIdentity") != candidate.result_identity:
                raise RuntimeError("private verification progress Candidate differs")
            if "criterionResults" in progress:
                results = _results_from_payload(candidate, progress["criterionResults"])
                unresolved = progress.get("unresolvedObservations", [])
                resolved = progress.get("resolvedObservationIdentities", [])
                projections = progress.get("effectSafetyProjections", [])
                if (
                    not isinstance(unresolved, list)
                    or not isinstance(resolved, list)
                    or not isinstance(projections, list)
                ):
                    raise RuntimeError("private unresolved observation progress is malformed")
                return VerificationCompletion(
                    results,
                    tuple(unresolved),
                    tuple(resolved),
                    tuple(projections),
                )
            if reenter and progress.get("contextMayHaveStarted") is True:
                active = progress.get("activeObservation")
                if isinstance(active, dict) and active.get("kind") == "EFFECT":
                    marker = active.get("effectDispatch")
                    if not isinstance(marker, dict) or marker.get("mayHaveRun") is not True:
                        raise RuntimeError("effect observation may have run without a safe unresolved binding")
                    unresolved = dict(marker)
                    unresolved.update(
                        {
                            "candidateIdentity": candidate.result_identity,
                            "observationIdentity": active.get("observationIdentity"),
                            "requests": active.get("requests"),
                            "target": marker.get("targetIdentity"),
                            "state": "UNRESOLVED",
                        }
                    )
                    unresolved["identity"] = _value_identity(unresolved)
                    progress.setdefault("unresolvedObservations", []).append(unresolved)
                    progress.pop("activeObservation", None)
                return self._persist_completion(
                    progress_path,
                    progress,
                    _undetermined_results(candidate, self._evidence(progress)),
                )
        else:
            if reenter:
                raise RuntimeError("private verification progress is absent")
            progress = {
                "candidateIdentity": candidate.result_identity,
                "contextMayHaveStarted": False,
                "evidenceRefs": [],
                "unresolvedObservations": [],
                "resolvedObservationIdentities": [],
                "effectSafetyProjections": [],
            }
            _write_json(progress_path, progress)

        scratch_root = transition_root / "scratch"
        scratch_root.mkdir(parents=True, exist_ok=True)
        planning = candidate.planning
        project_root = (
            Path(planning["projectRoot"])
            if isinstance(planning, dict) and isinstance(planning.get("projectRoot"), str)
            else None
        )
        if (
            _overlaps(scratch_root, retained_root)
            or (project_root is not None and _overlaps(scratch_root, project_root))
            or getattr(self._fresh_verifier, "fresh_context_enforced", False) is not True
            or getattr(self._fresh_verifier, "read_only_enforced", False) is not True
        ):
            return self._persist_completion(
                progress_path,
                progress,
                _undetermined_results(candidate, ()),
            )

        prior_effect_facts = self._store.effect_safety_facts(candidate)
        prior_unresolved = tuple(
            item
            for item in prior_effect_facts
            if isinstance(item, dict) and item.get("state") == "UNRESOLVED"
        )
        effect_safety = "UNSAFE" if prior_unresolved else "SUPPORTED"
        supported_observations = self._supported_observations()
        progress["contextMayHaveStarted"] = True
        progress["planCurrentness"] = self._observe_currentness(candidate).value
        _write_json(progress_path, progress)
        try:
            context = self._fresh_verifier.open(
                candidate,
                retained_root,
                supported_observations,
                effect_safety,
            )
            if not isinstance(context.identity, str) or not context.identity:
                raise ValueError("fresh verifier context identity is missing")
            proposed = context.plan(
                candidate,
                retained_root,
                supported_observations,
            )
            _, retained_after_plan = _capture(retained_root)
            if retained_after_plan != source_identity:
                raise DurableResultIntegrityError("Verifier changed retained Candidate source while planning")
            plan = _normalize_plan(candidate, source_identity, proposed)
        except DurableResultIntegrityError:
            raise
        except Exception:
            return self._persist_completion(
                progress_path,
                progress,
                _undetermined_results(candidate, ()),
            )
        if plan is None:
            return self._persist_completion(
                progress_path,
                progress,
                _undetermined_results(candidate, ()),
            )
        plan_path = transition_root / "observation-plan.json"
        _write_json_once(plan_path, plan)
        progress["contextIdentity"] = context.identity
        progress["planRef"] = str(plan_path)
        _write_json(progress_path, progress)

        evidence: list[dict[str, object]] = []
        unresolved: list[object] = []
        contradiction = False
        observations = plan["observations"]
        for position, observation in enumerate(observations):
            pre_currentness = self._observe_currentness(candidate)
            kind = observation["kind"]
            if kind == "EFFECT" and contradiction:
                item = _incomplete_evidence(
                    candidate,
                    observation,
                    "CONTRADICTION_SHORT_CIRCUIT",
                    pre_currentness,
                    self._observe_currentness(candidate),
                )
                unresolved_item = None
                effect_result = None
            elif kind == "READ" and (
                getattr(self._runner, "read_only_enforced", False) is not True
                or kind not in supported_observations
            ):
                item = _incomplete_evidence(
                    candidate,
                    observation,
                    "RUNNER_ISOLATION_UNAVAILABLE"
                    if getattr(self._runner, "read_only_enforced", False) is not True
                    else "UNSUPPORTED_OBSERVATION",
                    pre_currentness,
                    self._observe_currentness(candidate),
                )
                unresolved_item = None
                effect_result = None
            elif kind == "READ":
                try:
                    read_authority = self._runner.read_authority(candidate, observation)
                except Exception:
                    read_authority = None
                if not _read_authority_matches(candidate, observation, read_authority):
                    item = _incomplete_evidence(
                        candidate,
                        observation,
                        "MISSING_READ_AUTHORITY",
                        pre_currentness,
                        self._observe_currentness(candidate),
                    )
                    unresolved_item = None
                    effect_result = None
                else:
                    progress["activeObservation"] = {
                        "position": position,
                        "observationIdentity": observation["observationIdentity"],
                        "kind": kind,
                        "requests": observation["requests"],
                        "mayHaveRun": True,
                        "preCurrentness": pre_currentness.value,
                    }
                    _write_json(progress_path, progress)
                    raw = self._runner.run(
                        candidate,
                        retained_root,
                        scratch_root,
                        observation,
                    )
                    if not isinstance(raw, dict) or raw.get("redacted") is not True:
                        raw = _unsafe_read_result(observation)
                    _, retained_after = _capture(retained_root)
                    if retained_after != source_identity:
                        raise DurableResultIntegrityError("Runner changed retained Candidate source")
                    item, unresolved_item = _runner_evidence(
                        candidate,
                        observation,
                        raw,
                        pre_currentness,
                        self._observe_currentness(candidate),
                    )
                    effect_result = None
            elif (
                (
                    kind != "EFFECT"
                    and getattr(self._runner, "read_only_enforced", False) is not True
                )
                or kind not in supported_observations
                or (kind == "EFFECT" and pre_currentness is not Currentness.CURRENT)
            ):
                item = _incomplete_evidence(
                    candidate,
                    observation,
                    "RUNNER_ISOLATION_UNAVAILABLE"
                    if kind != "EFFECT"
                    and getattr(self._runner, "read_only_enforced", False) is not True
                    else "UNSUPPORTED_OBSERVATION",
                    pre_currentness,
                    self._observe_currentness(candidate),
                )
                unresolved_item = None
                effect_result = None
            else:
                progress["activeObservation"] = {
                    "position": position,
                    "observationIdentity": observation["observationIdentity"],
                    "kind": kind,
                    "requests": observation["requests"],
                    "mayHaveRun": True,
                    "preCurrentness": pre_currentness.value,
                }
                _write_json(progress_path, progress)
                if kind == "EFFECT":
                    if self._effect_observer is None:
                        raise RuntimeError("effect observation seam is absent")

                    def mark_effect(marker: dict[str, object]) -> None:
                        active = progress.get("activeObservation")
                        if not isinstance(active, dict):
                            raise RuntimeError("active effect observation is absent")
                        active["effectDispatch"] = marker
                        _write_json(progress_path, progress)

                    effect_result = self._effect_observer.observe(
                        candidate,
                        observation,
                        prior_effect_facts,
                        mark_effect,
                    )
                    raw = effect_result.raw
                else:
                    effect_result = None
                    raw = self._runner.run(
                        candidate,
                        retained_root,
                        scratch_root,
                        observation,
                    )
                _, retained_after = _capture(retained_root)
                if retained_after != source_identity:
                    raise DurableResultIntegrityError("Runner changed retained Candidate source")
                post_currentness = self._observe_currentness(candidate)
                item, unresolved_item = _runner_evidence(
                    candidate,
                    observation,
                    raw,
                    pre_currentness,
                    post_currentness,
                )
                if effect_result is not None:
                    unresolved_item = effect_result.unresolved
                    if effect_result.projection is not None:
                        progress["effectSafetyProjections"].append(effect_result.projection)
                    progress["resolvedObservationIdentities"].extend(
                        identity
                        for identity in effect_result.resolved_identities
                        if identity not in progress["resolvedObservationIdentities"]
                    )
            evidence_path = transition_root / "evidence" / f"{position:04d}.json"
            _write_json_once(evidence_path, item)
            evidence.append(item)
            progress["evidenceRefs"].append(str(evidence_path))
            progress.pop("activeObservation", None)
            if unresolved_item is not None:
                unresolved.append(unresolved_item)
                progress["unresolvedObservations"].append(unresolved_item)
            _write_json(progress_path, progress)
            try:
                partial_claims = context.assess(candidate, plan, tuple(evidence))
            except Exception:
                partial_claims = ()
            contradiction = contradiction or _has_supported_contradiction(
                partial_claims,
                tuple(evidence),
            )

        try:
            claims = context.assess(candidate, plan, tuple(evidence))
        except Exception:
            claims = ()
        _, retained_after_assessment = _capture(retained_root)
        if retained_after_assessment != source_identity:
            raise DurableResultIntegrityError("Verifier changed retained Candidate source while assessing")
        final_currentness = self._observe_currentness(candidate)
        results = _assess_results(
            candidate,
            plan,
            tuple(evidence),
            claims,
            final_currentness,
        )
        return self._persist_completion(progress_path, progress, results)


class ModuleExecution:
    def __init__(self, implementation, verification: VerificationExecution) -> None:
        self._implementation = implementation
        self._verification = verification

    def implement(self, work, worker, transition_identity, *, reenter):
        return self._implementation.implement(
            work,
            worker,
            transition_identity,
            reenter=reenter,
        )

    def verify(self, candidate, transition_identity, *, reenter):
        return self._verification.verify(
            candidate,
            transition_identity,
            reenter=reenter,
        )

    def observe_currentness(self, result: PublicResult) -> Currentness:
        return self._implementation.observe_currentness(result)
