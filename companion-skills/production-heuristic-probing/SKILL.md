---
name: production-heuristic-probing
description: 실제 서비스에서 문서와 다른 동작, 숨은 라우팅·상태 전이, 입력 변화에 따른 비정상 분기 또는 계층 경계의 우회 경로를 블랙박스로 조사할 때 사용한다. 특히 최소 입력 트리거를 찾거나 UI·모달리티·인증·캐시·네트워크 경계를 넘나드는 원인 탐색 요청에 적용한다. 문서화된 API 예제 구현, 일반 코딩, 실제 동작 불일치가 없는 설명 요청에는 사용하지 않는다.
---

# Production Heuristic Probing

## Caller contract

For the normal IIS completion path, the finalization-owning caller supplies the unchanged current sources and the settled successful verification:

- **Project Root:** exact canonical absolute path.
- **Thesis:** every exact source bound by the Scope, revision and full UTF-8 SHA-256.
- **Scope:** exact canonical `docs/planning/work/<slug>/SCOPE.md` path.
- **Transition Authority:** exact applicable project-local baseline path/digest and selected conditions when present, otherwise `None`.
- **Completed verification:** exact unchanged result from the completed independent verifier invocation, its actual identity and raw primary-evidence locations, including initial state, trigger/order, readbacks, observation windows, cleanup and currentness.
- **Target/source identity:** exact stable target paths and byte/runtime identities, declared scenario-effect paths, bound source paths/digests and verification pre/post currentness observations.
- **Prior Probe:** exact predecessor Probe result plus correction/new evidence for follow-up, or `None`.
- **User instructions:** current read-only/execution limits, external-effect authority and selected model/effort policy.

Tell the worker: **read every bound Thesis source, the exact Scope, the current implementation paths and the verifier's primary evidence directly before judgment.** Caller summaries, prior success labels and latest-file lookup are navigation only.

### Evidence and effect boundary — copy into every assignment

> **Evidence and effect boundary — apply before role-specific work**
> - Do not use mocks, stubs, canned responses, seeded success states or surrogate readbacks as evidence for a real boundary they replace.
> - Prefer the smallest safe observation or trigger. Stable product source/config/planning/authority and protected production data are not Probe mutation surfaces.
> - Execute a black-box probe only when current user authority permits the exact action and any effect is disposable/controlled, attributable, settled and cleaned up. If the necessary probe would mutate a stable target, non-disposable production state or an unauthorized external system, do not execute it; return the exact limitation or route it for separately authorized work and fresh verification.
> - If a required primary observation is unavailable, preserve the exact evidence/authority limit. Do not infer no finding.

## Purpose and ownership

Answer one bounded question: **even if the verifier's recorded observations are correct, can an actual reachable service or implementation path still violate the same approved Scope outcome, or expose a material false-success path, while those observations pass?**

The Probe owns independent post-verification heuristic search and verifier-evidence sanity checking. It is not a second semantic verifier: `scope-verify` owns Scope admission, every authored Acceptance scenario, evidence sufficiency and the only `VERIFIED | FAILED | INCONCLUSIVE` verdict. Main owns completion recording. The Probe never rewrites Thesis, Scope, Plan, verifier evidence or Scope status and never turns a heuristic finding into an Acceptance verdict.

The Probe's distinctive job is to test actual behavior where specification-shaped checking is weak: minimal abnormal inputs, hidden routing, state transitions and adjacent UI/auth/cache/network/modality boundaries. It may also inspect implementation and raw evidence read-only when active probing is unavailable or unnecessary.

## Invocation

On the normal ready-to-done path, arrange exactly one independent Probe invocation only after the independent verifier has settled with semantic `VERIFIED`. `FAILED`, `INCONCLUSIVE`, non-started, missing or incomplete verification skips the normal-success Probe and cannot progress Scope status.

A user may also request this capability directly for investigation. A standalone Probe can report production findings but does not manufacture a verifier verdict or completion eligibility.

Use the caller-selected model/effort under the existing IIS selection policy. Do not add consensus, a second Probe, a fixed risk roster or a hidden fallback. If an independent invocation required by the normal completion path is unavailable, return that limitation rather than relabeling Main or the verifier.

## Bounded heuristic investigation

1. Establish the exact Scope `Outcome`, authored `Acceptance`, applicable Thesis meaning and the verifier's actual observation boundary. Preserve explicit Non-Goals and do not invent new requirements.
2. Trace the current ordinary entrypoint through deciding routers, writers/readers, state/effect owners and authoritative readback. Cross an adjacent boundary only when a concrete clue can change the current hypothesis.
3. Search for the smallest discriminating trigger before designing a broad workaround: one byte, one pixel, one line, one header, one selector, one state bit, one ordering change or the narrowest equivalent input that separates conforming from failing behavior.
4. Prefer abnormal and boundary conditions over replaying normal inputs already discriminated by verification. Investigate hidden route selection, stale identity, auth/session boundaries, cache/currentness, network/provider transition, UI/render versus stored state, modality conversion and lifecycle state only when connected to the current Scope or a concrete observed clue.
5. Inspect verifier primary evidence rather than its narrative alone. For load-bearing claims compare exact initial state, trigger/order, identity, readback, observation window and settlement against reachable states the implementation can produce. A passing verifier observation is not repeated merely to agree with it.
6. For each candidate, resolve it as an evidence-backed dismissal, a concrete finding or an exact evidence/authority limit. An unexecuted branch alone is not a finding.

A material finding states the exact Scope/Thesis obligation, actual mechanism or service path, minimal reachable trigger/condition, wrong result, the verifier observation that cannot distinguish it, and the narrowest next action. Separate observed facts from inference.

For every executed Probe action, preserve the actual independent invocation identity and result reference, exact trigger/action, authorized mutable effect path or state, authoritative readback and raw evidence location, stable target/runtime identity before and after, and cleanup/settlement result. A read-only investigation records `Probe effect paths: None` and still identifies its actual reads/evidence. Missing action, currentness or settlement attribution is a material result limitation, not an implicit successful cleanup.

### Scope materiality

A real production defect outside the current Scope is still reportable, but it does not automatically block this Scope. Mark it `OUT_OF_SCOPE` unless it invalidates the verified target/currentness or an explicit premise of this Scope. Only a finding or evidence limit that can materially falsify the current approved Scope result withholds normal completion progression.

Classify limitations by the same rule. A Scope-material limitation withholds completion. An out-of-scope limitation is reported separately and does not block this Scope unless it prevents target/currentness attribution or invalidates a load-bearing Scope premise.

### Production access unavailable

Lack of live/production access does not become `None found`. Fall back to read-only inspection of the actual implementation, routes/state owners and unchanged verifier evidence. If that is sufficient to dismiss the candidate, record the basis. If the approved Scope claim still depends on an unavailable observation, return the exact limitation. Artifact-only or planning-only work must not invent a production runtime merely to satisfy this role.

## Termination

The Probe is not an open-ended hunt. Its frontier is the current Scope, the verifier's observation boundary and concrete implementation/runtime clues. Stop when every material candidate raised within that frontier is resolved as dismissal, finding or exact limitation. Do not search remote possibilities merely because another input might exist, require a fixed finding count, or keep probing after the current hypothesis is discriminated.

`COMPLETE` means this bounded investigation finished; it may contain findings and is not proof that all bugs are absent. Tool failure, missing evidence, unsafe required effects, unattributable action/currentness/settlement or unfinished material investigation is `PARTIAL` or `BLOCKED`, never a synthetic no-finding result.

## Result

Return one ordinary result preserving the complete execution/readback boundary needed by the caller:

```text
PRODUCTION HEURISTIC PROBE RESULT
Independent Probe invocation: <actual identity and result/evidence reference>
Scope: <exact canonical Scope>
Reviewed verification: <exact report and primary-evidence references | None for standalone investigation>
Target and authority: <exact current identities and authority limits>
Probe actions and primary evidence: <trigger/action/authoritative readback/raw evidence | Read-only inspection only>
Probe effect paths: <mutable paths/state, authorized effects and attribution | None>
Currentness before / after: <stable source/config/runtime identities and limitations>
Cleanup and settlement: <actual final state/readback and limitations | None>
Completion: COMPLETE | PARTIAL | BLOCKED
Scope-material findings: None | <material findings>
Out-of-scope findings: None | <findings that do not block this Scope>
Scope-material limitations: None | <limits that withhold this Scope's completion>
Out-of-scope limitations: None | <limits that do not block this Scope>
```

## Caller continuation

The caller preserves the verifier's unchanged semantic verdict while the Probe runs.

- `COMPLETE` with attributable invocation/actions/evidence/currentness, all Probe effects settled, and no unresolved Scope-material finding or limitation permits Main to apply the currentness and status-only recording procedure in `scope-verify/SKILL.md`.
- A Scope-material reachable violation or limitation withholds recording and routes the exact finding/limit under `iis-workflow`'s existing re-entry rules. It does not overwrite `VERIFIED` with a Probe verdict or authorize automatic repair.
- `PARTIAL`/`BLOCKED`, missing invocation/action/effect/currentness/cleanup attribution, or unsafe/unknown required effects withhold completion and state the exact next owner/action.
- An out-of-scope finding or limitation is routed separately and does not block the current Scope unless it invalidates the current target or a load-bearing Scope premise.
- Any stable source/config/authority change caused independently while Probe is running requires a fresh current-target verifier cycle. Probe does not patch or resume the old verdict.

For follow-up after correction, targeted probing is allowed only when the predecessor Probe is attributable, its basis is readable, unresolved items are exact, a new settled whole-Scope verifier result exists for the current target, and the unchanged basis outside the follow-up frontier remains applicable. Otherwise perform the normal Scope-bounded Probe. Do not create a Probe registry, fingerprint store, scheduler, approval layer or new lifecycle state.
