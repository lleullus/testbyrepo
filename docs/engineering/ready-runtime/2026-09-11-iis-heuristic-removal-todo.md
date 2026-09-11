# IIS 별도 Heuristic 완전 제거 — 실제 저장소 구현 TODO

## 0. 문서 성격과 기준

- 문서 상태: **IMPLEMENTATION TODO**
- 이 문서는 제거 작업의 실행 순서·파일 범위·검증 조건을 고정하는 engineering 계획이다.
- 이 문서는 `iis-plan-review/v1` 독립 검토 산출물이나 구현 admission이 아니며, 그 자체로 source mutation을 허가하지 않는다.
- 조사 원문: `/tmp/iis-heuristic-removal-impact-report-20260911.md`
- 조사 원문 SHA-256: `7db3cc94f4627c01fcb720388e79e2085c7af364cbac2fc7c20661616d6e154b`
- 실제 Repository Root: `/home/user01/project/iis-skills`
- 기준 branch / HEAD: `main` / `fed5ed51ee0795f26b0c3392ff230554a7c1bc13`
- 이 TODO 작성 직전 실제 Git 상태: `git status --short --branch` → `## main`
- 기준일: 2026-09-11

이 계획의 정상 경로는 다음으로 고정한다.

```text
Ready Ticket
  → Grounded Plan
  → Independent Plan Review
  → Implement
  → Verify
```

여기서 제거하는 것은 **별도 사전 Heuristic 역할·호출·reference·evidence field·모델 선택·고정 revision turn**이다. 다음 책임은 제거하지 않는다.

- Planner의 Code Grounding, competing-cause 및 falsifying-observation 작성 책임
- 작성자와 분리된 Independent Plan Review
- `ADMIT | REVISE | EVIDENCE_NEEDED`
- reviewed conditional first work
- material method change 시 dependent mutation 중단, affected Plan 재작성, 새 independent review, fresh implementing actor
- Verify의 통합 counterexample discovery, 모든 authored Flow/AC 판정, authoritative readback 및 finding disposition
- 이미 구현된 `ready` 대상의 verification-only 직접 진입
- `Verification: no`에서 final verifier·semantic verdict·`done`이 없어야 하는 경계
- opaque terminal handle과 caller-owned `ready_finalize`
- immutable bundle prepare/check/activate 및 retired-install cleanup

## 1. 완료 후 목표 상태

### 1.1 준비 책임

정상 preparation은 다음 세 invocation으로 끝난다.

1. **Planner** — 원계약·현재 코드·실행 경계를 조사하고 grounded Plan을 작성한다.
2. **Independent Plan Reviewer** — writer와 분리된 invocation에서 원계약을 직접 먼저 읽고, 현재 Plan과 primary evidence를 검토하여 `ADMIT | REVISE | EVIDENCE_NEEDED`를 쓴다.
3. **Lead fan-in** — Planner session을 이어 받아 실제 review artifact, currentness, 요청 Ticket denominator 및 terminal 형식만 대조한다. 두 번째 의미 검토나 승인이 아니다.

정상 평가 경로의 고정 호출 수는 현재 5회에서 3회로 줄어든다. 이 사실은 호출 구조 변화만 뜻하며 시간·토큰·비용 절감률을 미리 주장하지 않는다.

### 1.2 새 Plan Review JSON

`schema`는 기본적으로 `iis-plan-review/v1`을 유지한다. 정상 producer는 더 이상 `heuristic` object를 만들지 않는다.

```json
{
  "schema": "iis-plan-review/v1",
  "project_root": "<canonical absolute root>",
  "plans": [
    {"path": "<exact absolute Plan path>", "sha256": "<actual bytes sha256>"}
  ],
  "contracts": [
    {
      "ticket_path": "<exact Ticket path>",
      "ticket_sha256": "<actual bytes sha256>",
      "authority_digest": "<inspect_authority result>"
    }
  ],
  "review_origin": {
    "reviewer": "<actual independent reviewer>",
    "evidence_reference": "<raw reviewer invocation / primary evidence>"
  },
  "decisions": [
    {
      "ticket_path": "<exact Ticket path>",
      "decision": "ADMIT | REVISE | EVIDENCE_NEEDED",
      "rationale": "<complete semantic basis, counterexamples, unknowns and dispositions>",
      "start_scope": "<exact work that may start>",
      "conditions": []
    }
  ]
}
```

전환 원칙:

- 새 producer는 `heuristic` field를 **생성하지 않는다**.
- 새 consumer는 `heuristic` field를 **요구하지 않는다**.
- JSON의 알 수 없는 추가 field를 거절하는 새 로직을 만들지 않는다. 따라서 과거 artifact의 여분 `heuristic` field는 구조적으로 무시할 수 있다.
- 과거 artifact를 수용할지는 field 존재 여부가 아니라 current Plan/Ticket/authority bytes, 실제 reviewer provenance와 의미 currentness로 결정한다.
- 새 artifact는 기존 consumer에서 거절되므로 source·skill·consumer·fixture·평가 harness를 같은 immutable bundle로 배포한다.
- 저장소 밖에 독립 배포된 consumer가 실제로 발견되면 구현을 멈추고 v1 유지, v2, dual-reader 중 호환 정책을 다시 결정한다. 현재 근거만으로 v2나 migration converter를 만들지 않는다.

### 1.3 독립 reviewer에 남길 최소 탐색 책임

`references/heuristic.md` 전체를 Review에 복사하지 않는다. `review.md`에 다음 최소 책임만 명시한다.

- Planner diagnosis를 프레임으로 받아들이기 전에 exact Ticket, Parent Spec, Behavior/UI authority와 현재 product path를 직접 읽는다.
- 현재 method의 실제 의존 경계에서 다음 material false-start path를 직접 판단한다.
  - wrong cause
  - ordinary entry bypass
  - second writer/reader 또는 external owner
  - producer/consumer mismatch
  - ordering, interruption, partial effect
  - stale identity 또는 weak proxy readback
  - repair-induced state/order/ownership path
  - preserved behavior 손실
- check frontier는 고정 quota가 아니라 현재 method의 load-bearing dependencies와 proposed change에서 bounded하게 도출한다.
- 관측된 contradiction, inference, missing evidence를 구분한다.
- 값싸고 현재 권한으로 가능한 load-bearing observation을 최종 verifier로 미루는 Plan은 `REVISE` 또는 `EVIDENCE_NEEDED`로 남긴다.
- no finding은 자동 `ADMIT`가 아니다. reviewer가 전체 원계약에 대해 한 semantic decision만 쓴다.
- evidence currentness는 `review_origin.evidence_reference`, primary evidence와 각 decision `rationale`로 보존한다. 새 fingerprint DB, evidence ledger, reviewer-authentication gate를 만들지 않는다.

## 2. 실제 저장소 결합 지도

| 영역 | 현재 실제 결합 | 목표 상태 | 조치 유형 |
|---|---|---|---|
| `ready-ticket-plan` | Planner → Heuristic → writer revision → reviewer → lead | Planner → reviewer → lead | 필수 수정 및 reference 삭제 |
| Plan revision contract | conditional/refutation/R5가 Heuristic refresh 요구 | affected Plan revision → current independent review | 필수 수정 |
| Review JSON | top-level `heuristic` object 예시·설명 | field 완전 미생성 | 필수 수정 |
| Admission consumer | `plan-binding.js`가 `review.heuristic` 필수 검사 | reviewer origin만 필수; 기존 bindings/decision 유지 | 필수 수정 |
| Shared fixture | `helpers.js`가 Heuristic field 생성 | 새 정상 no-Heuristic fixture | 필수 수정 |
| Implementation re-entry | material method change가 Heuristic으로 복귀 | Plan revision → independent review → fresh actor | 필수 수정 |
| Verify | 같은 verifier의 integrated discovery를 Heuristic 명칭으로 보고 | Counterexample/Finding 일반 명칭 | 명칭 수정, 기능 유지 |
| Adaptive routing | stage/mode/model/disabled path가 Heuristic role을 요구 | Planner/Review만 선택·라우팅 | 필수 수정 |
| Evaluation | 고정 5 turns 및 exact 5-role setup 검사 | 실제 3 turns 및 exact 3-role provenance | 필수 수정 |
| Immutable installer | retired Probe payload 거절 및 구 host link 제거 | 그대로 유지 | 원칙적으로 수정 금지 |
| Current project Plan | `PLAN-001.md`가 Heuristic return route 포함 | 실제 다음 소비 여부에 따라 owner가 처리 | 조건부 수정 |
| Historical engineering docs | 과거 Probe/runtime 사실 기록 | 과거 사실 보존 | 수정 금지 |

## 3. Cutover 불변 조건

아래 항목 중 하나라도 깨지면 제거 작업을 완료로 처리하지 않는다.

- [ ] `review_origin.reviewer`와 `review_origin.evidence_reference`는 계속 필수다.
- [ ] Plan path는 project-local canonical absolute path이고 실제 bytes hash와 일치해야 한다.
- [ ] Ticket hash와 `authority_digest`가 현재여야 한다.
- [ ] `ADMIT`가 아닌 `REVISE`와 `EVIDENCE_NEEDED`는 구현 admission을 얻지 못한다.
- [ ] `rationale`, `start_scope`, `conditions` shape 검사는 유지한다.
- [ ] Plan byte 변경은 기존 review를 stale하게 만든다.
- [ ] 일반 implementation source 변경만으로 Plan review를 자동 stale 처리하지 않는다.
- [ ] source/search/runtime의 load-bearing premise 변화는 hash 일치만으로 의미 currentness가 증명되지 않으며 reviewer가 영향 판단한다.
- [ ] writer는 같은 writing invocation에서 자기 Plan을 independent `ADMIT`로 승인하지 못한다.
- [ ] material method change는 현재 implementation invocation의 terminal 경계다.
- [ ] fresh actor는 prior worker/process settlement와 새 current admission 뒤에만 시작한다.
- [ ] verification-only 경로는 새 execution Plan을 강제하지 않는다.
- [ ] Verify terminal machine fields, opaque handle, finalizer 권한과 `ready → done` compare-and-swap은 변경하지 않는다.
- [ ] retired Probe 차단·구 설치 cleanup·rollback 복원 동작은 유지한다.

## 4. 구현 순서와 상세 TODO

부분 변경 상태를 실제 host에 활성화하지 않는다. 아래 phase는 개발 commit 단위로 나눌 수 있지만, candidate bundle에는 모두 포함되어야 한다.

### H0 — 착수 전 기준 고정과 외부 경계 확인

- [ ] **H0.1** 구현 시작 시 `git status --short --branch`와 `git rev-parse --verify HEAD`를 다시 기록한다.
  - 기준과 달라졌다면 이 문서의 line anchor가 아니라 실제 최신 bytes를 다시 읽는다.
  - unrelated working-tree change가 있으면 이번 변경과 분리 가능한지 먼저 확인한다.
- [ ] **H0.2** active workflow 범위에 대한 bounded search를 다시 수행한다.
  - 대상: `companion-skills`, `delivery-tools/ready-ticket`, `iis-adaptive-planning`, `iis-workflow`, `evaluation/ready-verification`, root `README.md`, 관련 tests.
  - 역사 문서, retired cleanup, 이 TODO 자체는 active dependency와 분리해 분류한다.
- [ ] **H0.3** 저장소 밖에 독립 배포된 `iis-plan-review/v1` consumer가 있다는 실제 배포 계약이 있는지 확인한다.
  - 발견되지 않으면 same-v1/no-field 방식을 유지한다.
  - 발견되면 호환 정책 결정 전 producer shape를 변경하지 않는다.
- [ ] **H0.4** 현재 소비 예정인 Plan/review/worker가 있는지 operator 또는 caller가 제공한 exact identifier로 확인한다.
  - 특히 `docs/planning/work/transition-baseline-protocol/plans/PLAN-001.md`가 current implementation admission에 사용되는지 확인한다.
  - network/transport 실패만으로 worker 부재, review 만료 또는 artifact 부재를 추론하지 않는다.
  - write/activate 호출이 timeout이면 같은 변경을 즉시 반복하지 않고 installed state 또는 target bytes를 먼저 읽는다.
- [ ] **H0.5** source 구현과 operating-install activation을 분리한다.
  - source/test/candidate 확인 전 설치 포인터를 바꾸지 않는다.
  - installed immutable release 내부 파일을 직접 편집하지 않는다.

**H0 Exit:** 변경 대상의 실제 최신 bytes와 외부 consumer/current-artifact 경계가 기록되어 있고, 부분 activation이 금지되어 있다.

### H1 — `ready-ticket-plan`의 canonical 준비 계약 단순화

#### H1-A. `companion-skills/ready-ticket-plan/SKILL.md`

- [ ] **H1.1** frontmatter description에서 `Heuristic`을 제거하고 Planner + independent Plan Review 구조를 설명한다.
- [ ] **H1.2** Purpose/authority를 다음으로 바꾼다.
  - Planner: grounded execution method 작성과 reviewer finding에 대한 revision 소유.
  - Independent reviewer: start sufficiency, counterexample/unknown 판단, per-Ticket decision 소유.
  - Lead: attribution/currentness/denominator fan-in만 소유.
- [ ] **H1.3** 필수 reference 목록을 `plan.md`, `review.md` 두 개로 줄인다.
- [ ] **H1.4** independence 규칙을 유지한다.
  - reviewer는 Plan writer와 분리된 invocation이어야 한다.
  - DIRECT writer가 같은 writing invocation에서 self-approve할 수 없다.
  - independent invocation이 없으면 유용한 Plan은 남기되 `ADMIT`를 합성하지 않는다.
- [ ] **H1.5** preparation flow를 다시 쓴다.
  1. exact Ticket denominator와 current authority bind
  2. Planner 조사·Plan 작성
  3. Independent reviewer가 원계약과 current Plan/evidence를 직접 읽고 JSON decision 작성
  4. `REVISE/EVIDENCE_NEEDED`는 owning Planner/evidence owner에게 반환
  5. current `ADMIT`일 때만 lead가 exact terminal을 fan-in
- [ ] **H1.6** unconditional writer revision step을 제거한다.
  - revision은 reviewer가 실제 `REVISE`를 반환했을 때만 별도 후속 작업이다.
  - 같은 unresolved issue를 evidence/method change 없이 자동 재제출하지 않는 기존 원칙은 유지한다.
- [ ] **H1.7** terminal 설명에서 “Planner/Heuristic intermediate”를 현재 구조에 맞게 “Planner 또는 reviewer intermediate output”으로 정리한다.
- [ ] **H1.8** `COMPLETE` 분모는 모든 required Ticket의 actual current independent `ADMIT`라는 기존 의미를 유지한다.

#### H1-B. `companion-skills/ready-ticket-plan/references/plan.md`

- [ ] **H1.9** Conditional first work refutation route를 다음으로 바꾼다.

```text
affected Plan revision
  → current independent Plan Review
  → fresh implementation actor admission
```

- [ ] **H1.10** Revision ownership에서 important cause/owner/interface/persistence/readback/effect change가 Planner revision + independent review로 돌아가게 한다.
- [ ] **H1.11** Plan byte 변경 시 review identity가 무효화되는 규칙을 유지한다.
- [ ] **H1.12** R5를 “Refresh affected review”로 재정의한다.
  - 직접 연관된 contract/source/schema/search/runtime premise 재확인
  - repair-induced state/order/ownership path 확인
  - 영향 범위와 evidence limit를 current reviewer에게 전달
  - 별도 Heuristic invocation/carry-forward identity는 제거
- [ ] **H1.13** R1–R4와 R6의 정상 의미를 보존한다.
  - Normalize, Reinspect, Bound impact, Revise/self-check, Resubmit-or-return
  - 새 revision controller, retry quota, approval count를 만들지 않는다.

#### H1-C. `companion-skills/ready-ticket-plan/references/review.md`

- [ ] **H1.14** 첫 절에 independent original-contract-first pass를 명시한다.
- [ ] **H1.15** reviewer가 현재 method의 load-bearing dependency에서 material counterexample을 직접 조사하도록 명시한다.
- [ ] **H1.16** wrong cause, second writer/reader, ordinary entry bypass, producer/consumer mismatch, ordering/interruption/partial effect, weak readback, repair-induced path를 bounded review 항목으로 남긴다.
- [ ] **H1.17** no-finding을 별도 result나 approval로 만들지 않는다.
- [ ] **H1.18** 모든 Heuristic evidence/refresh/carry-forward 문구를 reviewer-owned primary evidence/currentness 문구로 바꾼다.
- [ ] **H1.19** JSON 예시에서 top-level `heuristic` object를 완전히 제거한다.
- [ ] **H1.20** material finding/unknown/dismissal의 semantic basis는 각 decision `rationale`에 둔다.
- [ ] **H1.21** reviewer raw provenance는 기존 `review_origin.evidence_reference`에 둔다.
- [ ] **H1.22** schema/root, plans, contracts, decisions, conditions와 `ADMIT | REVISE | EVIDENCE_NEEDED`는 그대로 유지한다.
- [ ] **H1.23** `ready_contract check_plan_admission`은 구조/current-byte boundary이며 semantic sufficiency를 자동 판정하지 않는다는 설명을 유지한다.

#### H1-D. reference 및 prompt surface

- [ ] **H1.24** `companion-skills/ready-ticket-plan/references/heuristic.md`를 삭제한다.
- [ ] **H1.25** 삭제 파일을 가리키는 link/reference가 active payload에 남지 않게 한다.
- [ ] **H1.26** `companion-skills/ready-ticket-plan/agents/openai.yaml`의 default prompt를 Planner + independent reviewer 구조로 바꾼다.
- [ ] **H1.27** 새 prompt가 다음을 계속 요구하는지 확인한다.
  - exact Ready Tickets
  - current product authority/evidence
  - outside-root review artifact
  - writer/reviewer independence
  - no source implementation
  - no final verification verdict

**H1 Exit:** plan Skill을 처음 읽는 actor가 삭제된 역할이나 reference를 요청하지 않으며, reviewer가 독립 원계약·반례·currentness 판단을 소유한다.

### H2 — Review JSON producer/consumer/fixture의 원자적 전환

#### H2-A. `delivery-tools/ready-ticket/src/plan-binding.js`

- [ ] **H2.1** 현재 line 27의 결합 검사를 분리한다.
  - 계속 필수: `review_origin.reviewer`
  - 계속 필수: `review_origin.evidence_reference`
  - 제거: `review.heuristic.evidence_reference`
  - 제거: `review.heuristic.disposition_summary`
- [ ] **H2.2** missing reviewer origin은 계속 `PLAN_REVIEW_STALE`로 실패시킨다.
- [ ] **H2.3** 다음 검사는 수정하지 않는다.
  - canonical outside-root review path
  - `iis-plan-review/v1` 및 exact project root
  - nonempty plans와 contracts/decisions arrays
  - project-local Plan paths와 SHA currentness
  - exact one Ticket contract/decision pairing
  - Ticket hash와 `authority_digest`
  - decision enum
  - `rationale`, `start_scope`, `conditions`
  - conditional fields
  - non-ADMIT의 `PLAN_NOT_ADMITTED`
- [ ] **H2.4** unknown extra JSON field를 금지하는 strict schema layer를 새로 만들지 않는다.
- [ ] **H2.5** 오류 메시지를 바꾼다면 tests는 코드(`PLAN_REVIEW_STALE`)와 실제 missing reviewer origin을 판정하며 과거 “or heuristic result” 문구에는 의존하지 않게 한다.

#### H2-B. `delivery-tools/ready-ticket/tests/helpers.js`

- [ ] **H2.6** shared `reviewData` fixture에서 `heuristic` object를 제거한다.
- [ ] **H2.7** fixture의 `review_origin`은 실제 구조 테스트용 provenance로 유지한다.
- [ ] **H2.8** fixture가 semantic independent review의 증명은 아니라는 현재 제한을 유지한다.

#### H2-C. `delivery-tools/ready-ticket/tests/authority-plan.test.js`

- [ ] **H2.9** 기본 no-Heuristic fixture가 `ADMIT`되고 `iis-implementation-admission/v1`을 반환하는 test를 유지/명시한다.
- [ ] **H2.10** legacy extra `heuristic` object를 임시로 추가해도 새 consumer가 그것을 요구하거나 해석하지 않는 regression을 추가한다.
- [ ] **H2.11** `review_origin.reviewer` 누락을 `PLAN_REVIEW_STALE`로 확인한다.
- [ ] **H2.12** `review_origin.evidence_reference` 누락을 `PLAN_REVIEW_STALE`로 확인한다.
- [ ] **H2.13** `REVISE`와 `EVIDENCE_NEEDED` 각각 `PLAN_NOT_ADMITTED`인지 확인한다.
- [ ] **H2.14** Plan bytes 변경은 `PLAN_REVIEW_STALE`인지 확인한다.
- [ ] **H2.15** Ticket 또는 applicable authority bytes 변경은 stale authority로 거절되는 test를 추가하거나 기존 equivalent coverage를 정확히 연결한다.
- [ ] **H2.16** ordinary implementation source 변경은 reviewed Plan을 자동 stale하게 만들지 않는 기존 test를 유지한다.
- [ ] **H2.17** 다른 Node tests가 shared fixture를 사용하므로 전체 `npm test`에서 no-Heuristic shape로 통과하는지 확인한다.

#### H2-D. Boundary README

- [ ] **H2.18** `delivery-tools/ready-ticket/README.md`의 material-method return route에서 Heuristic을 제거한다.
- [ ] **H2.19** stateless admission, ordinary command failure, no blind replay, fresh actor, verification binding/finalization 설명은 변경하지 않는다.

**H2 Exit:** 새 정상 review shape가 실제 core admission을 통과하고 reviewer provenance/stale/non-ADMIT 보호가 유지된다.

### H3 — Implementation material-method re-entry 정리

대상:

- `companion-skills/ready-ticket-implement/SKILL.md`
- `companion-skills/ready-ticket-implement/references/implement.md`
- `companion-skills/ready-ticket-implement/agents/openai.yaml`

- [ ] **H3.1** 모든 `Plan -> Heuristic -> independent review` 문구를 `affected Plan revision -> current independent review`로 바꾼다.
- [ ] **H3.2** terminal next action을 정확히 다음으로 고정한다.

```text
Next allowed action: revise affected Plan -> independent review
```

- [ ] **H3.3** material method change에서 현재 worker가 새 방향을 구현하거나 bound Plan을 직접 고쳐 gate를 맞추지 못하게 한다.
- [ ] **H3.4** current invocation이 `PARTIAL | BLOCKED`로 끝나야 하는 기존 규칙을 유지한다.
- [ ] **H3.5** prior worker/process/service settlement 확인 전 같은 mutable worktree에 replacement를 시작하지 않는 규칙을 유지한다.
- [ ] **H3.6** fresh actor가 새 `plan_review_path`로 admission부터 다시 수행하게 한다.
- [ ] **H3.7** naming/private helper/equivalent local fix는 current worker 재량이라는 경계를 유지한다.
- [ ] **H3.8** product meaning change는 method reviewer가 아니라 Scope/Behavior/Matt/Spec/Ticket 원권위로 반환한다.
- [ ] **H3.9** external/non-idempotent effect response loss에서 blind replay 금지와 authoritative readback 경계를 유지한다.
- [ ] **H3.10** start/end `check_plan_admission`, Ticket `ready` 유지, separate verification authority 경계를 유지한다.

**H3 Exit:** 최초 준비와 구현 중 재진입이 모두 존재하지 않는 역할을 가리키지 않고, old ADMIT/same worker 우회가 불가능하다.

### H4 — Verify의 명칭만 정리하고 기능은 보존

대상:

- `companion-skills/ready-ticket-verify/references/verify.md`
- root `README.md`

- [ ] **H4.1** verifier ownership 설명의 `heuristic finding disposition`을 `finding disposition`으로 바꾼다.
- [ ] **H4.2** heading `Heuristic Finding Disposition`을 `Finding Disposition`으로 바꾼다.
- [ ] **H4.3** scenario report의 `Heuristic frontier`를 `Counterexample frontier`로 바꾼다.
- [ ] **H4.4** scenario report의 `Heuristic findings / proposed verifier dispositions`를 `Findings / proposed verifier dispositions`로 바꾼다.
- [ ] **H4.5** `VERIFIED` closure 항목의 `heuristic finding dispositions`를 `finding dispositions`로 바꾼다.
- [ ] **H4.6** final report field `Heuristic finding dispositions`를 `Finding dispositions`로 바꾼다.
- [ ] **H4.7** 다음 disposition enum과 의미를 그대로 유지한다.
  - `REPRODUCED`
  - `CURRENT_READBACK_CONFIRMED`
  - `OUT_OF_SCOPE`
  - `UNATTRIBUTABLE`
  - `SUPERSEDED_BY_CURRENT_TARGET`
- [ ] **H4.8** bounded post-implementation frontier, authored Flow denominator, every AC verdict, current target attribution, cleanup, absence window, external-effect settlement을 삭제하거나 축소하지 않는다.
- [ ] **H4.9** root `README.md`의 “heuristic discovery”를 “integrated counterexample discovery” 또는 동등한 현재 책임 명칭으로 바꾼다.
- [ ] **H4.10** 다음 machine/host 계약에는 source diff를 만들지 않는다.
  - `READY TICKET VERIFICATION RESULT` heading
  - verification binding path/SHA
  - stable/effect paths
  - semantic verdict enum
  - `Verifier Ticket Progression`
  - opaque host terminal handle
  - `ready_finalize` sole input와 guarded status transition
- [ ] **H4.11** `delivery-tools/ready-ticket/src/verification-binding.js`는 review를 optional navigation으로만 읽으며 Heuristic field를 소비하지 않으므로 변경하지 않는다.

**H4 Exit:** active Verify prose에는 별도 단계처럼 보이는 이름이 없고, 실제 discovery/adjudication/finalization 의미는 byte-level machine contract까지 보존된다.

### H5 — Adaptive 및 IIS router의 stage/mode/model/disabled 경로 동기화

대상:

- `iis-adaptive-planning/references/00-baseline-coexistence.md`
- `iis-adaptive-planning/references/06-verification-triage.md`
- `iis-adaptive-planning/references/07-terminal-report.md`
- `iis-adaptive-planning/references/08-delivery-continuation.md`
- `iis-adaptive-planning/references/09-run-contract.md`
- `iis-adaptive-planning/templates/ADAPTIVE-RUN-CONTRACT.template.md`
- `iis-adaptive-planning/agents/openai.yaml`
- `iis-workflow/SKILL.md`

- [ ] **H5.1** `00-baseline-coexistence.md`에서 Outer Main이 takeover하지 않는 authority 목록을 현재 Planner/implementation/verification ownership에 맞춘다.
- [ ] **H5.2** 같은 파일의 final verifier 설명을 “integrated counterexample discovery”로 바꾼다.
- [ ] **H5.3** `06-verification-triage.md`의 implementation method defect route를 Planner → independent review로 바꾼다.
- [ ] **H5.4** `07-terminal-report.md`에서 intermediate output을 Planner/reviewer와 actual lead terminal로 구분한다.
- [ ] **H5.5** `08-delivery-continuation.md`의 preparation owner 설명을 grounded method preparation + independent current per-Ticket start review로 바꾼다.
- [ ] **H5.6** preparation invocation/model 설명에서 Heuristic role을 제거한다.
  - actual Planner/writer-side continuation과 independent Plan Review만 선택 대상으로 설명한다.
  - lead는 writer session의 fan-in continuation이며 별도 approval/model roster를 만들지 않는다.
  - 두 개의 서로 다른 모델을 의무화하지 않는다. 하나의 현재 user selection이 적용 가능한 역할을 포괄할 수 있다.
- [ ] **H5.7** `Verification: no`에서 final verifier/final verdict/`done`은 계속 금지하되 `Implementation: yes`는 current independent Plan Review를 요구하게 한다.
- [ ] **H5.8** event-loop table에서 intermediate Heuristic result를 admission으로 오인하는 예시를 현재 Planner/reviewer intermediate result로 바꾼다.
- [ ] **H5.9** preparation handoff에서 실제 `READY TICKET PLAN RESULT`와 exact review artifact만 소비하도록 유지한다.
- [ ] **H5.10** material method change route를 affected Plan revision → independent review → fresh actor로 바꾼다.
- [ ] **H5.11** `09-run-contract.md`의 stage overrides를 갱신한다.
  - `do not verify` + implementation yes: pre-implementation independent review는 유지
  - verification-only: already implemented stable target이면 새 plan ADMIT 불필요
- [ ] **H5.12** Delivery Model Selection에서 actual delegated preparation role을 Planner/Plan Review로 한정한다.
- [ ] **H5.13** `READY_EXECUTION_PLANS` readback 설명에서 “Heuristic no-finding”을 삭제하고 actual independent review/current evidence만 남긴다.
- [ ] **H5.14** `09-run-contract.md`의 일반명사 “any other heuristic”은 의미를 보존한 채 `inference`, `proxy`, 또는 동등한 표현으로 바꿔 역할명과 혼동을 없앤다.
- [ ] **H5.15** Run Contract template의 `Preparation selections`를 실제 Planner/Plan Review invocation과 writer continuation 구조로 갱신한다.
- [ ] **H5.16** template에 preparation switch나 third stage를 새로 만들지 않는다.
- [ ] **H5.17** Adaptive default prompt의 material-method return route를 갱신한다.
- [ ] **H5.18** `iis-workflow/SKILL.md`의 companion 안내를 “plans and independent start review”로 바꾼다.
- [ ] **H5.19** Baseline IIS terminal, planning-only/preparation-only 의미, Required/Candidate semantics, Run Contract Approval Gate, user-selected model/effort 보존 규칙은 변경하지 않는다.
- [ ] **H5.20** `tests/test_adaptive_run_contract_check.py` 전체를 실행해 template/checker의 현재 structural vocabulary가 유지되는지 확인한다.
  - 이번 제거를 이유로 새 Run Contract field나 checker enum을 추가하지 않는다.

**H5 Exit:** Adaptive가 삭제된 role을 dispatch/model-select하지 않고, implementation-only, verification-only, verification-disabled, preparation-only 경로가 각 기존 권한을 보존한다.

### H6 — Evaluation harness를 실제 3-turn provenance로 재구성

대상:

- `evaluation/ready-verification/calibrate.py`
- `evaluation/ready-verification/completion.py`
- `evaluation/ready-verification/inspect_run.py`
- `evaluation/ready-verification/README.md`
- `tests/test_ready_agent_capture.py`
- `tests/test_ready_completion_calibration.py`

#### H6-A. `calibrate.py::run_preparation`

- [ ] **H6.1** common prompt에서 `ready-ticket-plan`과 `plan.md`, `review.md` 두 reference만 읽게 한다.
- [ ] **H6.2** 정상 role sequence를 정확히 다음으로 바꾼다.

```text
planner
  → reviewer
  → lead
```

- [ ] **H6.3** `heuristic` invocation을 삭제한다.
- [ ] **H6.4** Heuristic disposition만을 위한 unconditional `revision` invocation을 삭제한다.
- [ ] **H6.5** Planner의 session file을 보존한다.
- [ ] **H6.6** Reviewer는 Planner session을 resume하지 않는 별도 invocation으로 유지한다.
- [ ] **H6.7** Reviewer input을 다음으로 연결한다.
  - exact original Ticket/Spec/Behavior/UI
  - current Plan bytes
  - Planner terminal
  - Planner raw events/primary evidence
  - direct repository/runtime evidence
- [ ] **H6.8** Reviewer만 exact outside-root `prepare/plan-review.json`을 쓴다.
- [ ] **H6.9** `review_origin.evidence_reference`를 reviewer의 actual `events.jsonl`로 둔다.
- [ ] **H6.10** Lead는 original Planner session을 resume한다.
- [ ] **H6.11** Lead input은 actual review artifact, reviewer raw evidence, Planner evidence다.
- [ ] **H6.12** Lead가 review JSON이나 Plan을 수정하지 못하게 한다.
- [ ] **H6.13** `review_before_lead`, reviewed product snapshot과 review unchanged check를 새 control flow에서도 항상 명시적으로 초기화하고 검증한다.
- [ ] **H6.14** role result list에는 실제 실행된 `planner`, `reviewer`, `lead`만 남긴다.
- [ ] **H6.15** reviewer가 `REVISE | EVIDENCE_NEEDED`를 반환하면 그것을 actual preparation result로 보존하고 `COMPLETE`로 승격하지 않는다.
- [ ] **H6.16** fixed normal path 안에 새 자동 retry/revision controller를 만들지 않는다.
- [ ] **H6.17** 향후 실제 revision 평가가 필요하면 reviewer result가 요구할 때만 Planner를 resume하여 method/evidence를 바꾸고, 별도 fresh reviewer invocation을 거치게 한다. 동일 unresolved issue의 자동 재제출은 금지한다.

#### H6-B. Completion/inspection/docs

- [ ] **H6.18** `completion.py`의 exact preparation role set을 `{"planner", "reviewer", "lead"}`로 바꾼다.
- [ ] **H6.19** 각 role의 clean transport, model completion, actual model match 검사는 유지한다.
- [ ] **H6.20** full current ADMIT, protected-change 없음, candidate core currentness 검사는 유지한다.
- [ ] **H6.21** 단순 role 이름 집합이나 fake JSON만으로 setup 성공이 되지 않게 한다.
- [ ] **H6.22** `inspect_run.py` stage choices에서 `prepare/heuristic`을 제거한다.
- [ ] **H6.23** stage choices를 최소 `plan`, `prepare/planner`, `prepare/reviewer`, `prepare/lead`, `implement`, `verify`로 맞춘다.
- [ ] **H6.24** evaluation README의 5-turn/3-logical-role 설명을 3-turn/2-substantive-role + lead fan-in으로 갱신한다.
- [ ] **H6.25** README에서 별도 invocation, writer session resume, reviewer JSON ownership, actual evidence/currentness 제한을 계속 설명한다.

#### H6-C. Evaluation regressions

- [ ] **H6.26** `tests/test_ready_agent_capture.py`의 obsolete `Heuristic result` intermediate 예시를 실제 존재하는 intermediate reviewer result로 교체한다.
- [ ] **H6.27** quoted/conflicting/intermediate text를 canonical lead `COMPLETE`로 오인하지 않는 parser 보장을 유지한다.
- [ ] **H6.28** `tests/test_ready_completion_calibration.py`의 fake review/empty roles 거절 test를 유지한다.
- [ ] **H6.29** 가능하면 stale 5-role record가 새 setup으로 인정되지 않는 focused test를 추가한다.
- [ ] **H6.30** 실제 3-role record도 raw events, model completion, current full ADMIT 없이 성공하지 못한다는 검사를 유지/추가한다.
- [ ] **H6.31** 아래 semantic preparation cases를 삭제하거나 이름만 바꿔 무력화하지 않는다.
  - `prepare-simple`
  - `prepare-competing-cause`
  - `prepare-shared-order`
  - `prepare-irrelevant-counterexample`
  - `prepare-conditional-support`
  - `prepare-conditional-refutation`
  - `prepare-conditional-unavailable`
  - `prepare-evidence-reuse`
  - `prepare-feedback-loop`
- [ ] **H6.32** reviewer-only 구성에서 기대할 의미를 확인한다.
  - simple: 불필요한 확장 없이 ADMIT 가능
  - competing cause: ordinary entry bypass를 잡아 REVISE/EVIDENCE_NEEDED
  - shared order: label-only repair를 거절
  - irrelevant counterexample: Scope 밖 의무를 추가하지 않음
  - conditional support/refutation/unavailable: permitted work와 prohibited expansion 구분
  - evidence reuse: currentness를 확인한 재사용
  - feedback loop: shared parser group과 separate remote defect 모두 start scope/self-check에 포함
- [ ] **H6.33** unit/schema pass를 semantic detection 품질 증명으로 쓰지 않는다. 위 bounded model cases의 실제 raw evidence를 별도로 검토한다.

**H6 Exit:** normal preparation이 실제 3 invocations로 동작하고, reviewer가 약한 Plan을 독립적으로 거절할 수 있으며, fake provenance로 `COMPLETE`가 되지 않는다.

### H7 — 현재 Plan/review, 역사 문서, retired cleanup 분류

#### H7-A. Current project Plan

- [ ] **H7.1** `docs/planning/work/transition-baseline-protocol/plans/PLAN-001.md`가 실제 다음 implementation admission에 사용되는지 먼저 확인한다.
- [ ] **H7.2** 현재 소비할 Plan이면 owner가 line 158의 return route를 새 구조로 revise한다.
- [ ] **H7.3** Plan bytes를 바꾼 뒤 기존 review를 재사용하지 않는다. current independent reviewer가 새 bytes와 load-bearing premises를 다시 판단한다.
- [ ] **H7.4** 이미 종료된 evidence/history라면 당시 상태로 보존하고 current workflow navigation으로 재사용하지 않는다.
- [ ] **H7.5** 다른 프로젝트의 Plan/review를 전역 대량 rewrite하지 않는다. 다음 실제 소비 시 exact artifact 단위로 같은 규칙을 적용한다.

#### H7-B. Historical engineering docs

다음 파일은 과거 설계와 incident evidence이므로 기본적으로 수정하지 않는다.

- `docs/engineering/ready-runtime/2026-09-05-r0-r1-preparation.md`
- `docs/engineering/ready-runtime/2026-09-05-refactoring-roadmap.md`

- [ ] **H7.6** 역사 문서를 현재 구조였던 것처럼 재작성하지 않는다.
- [ ] **H7.7** current navigation 혼동이 실제로 확인될 때만 짧은 “historical” 표기를 별도 추가하고 원래 사실은 보존한다.

#### H7-C. Retired installation cleanup

다음은 제거 대상이 아니라 legacy 재유입/잔존 제거 기능이다.

- `scripts/sync_installed_iis.py`의 `CANDIDATE_RETIRED` 항목
- `host_links()`의 `skills/ready-ticket-heuristic-probe = None`
- `tests/test_ready_ticket_boundary_tools.py`의 migration/remove 복원 test

- [ ] **H7.8** 위 retired payload rejection과 host-link cleanup을 삭제하지 않는다.
- [ ] **H7.9** candidate manifest에는 retired Probe payload가 계속 없어야 한다.
- [ ] **H7.10** upgrade 시 오래된 host link가 제거되고 `remove`/rollback에서 사용자 원래 entry가 보존되는 test를 유지한다.
- [ ] **H7.11** `scripts/check-ready-boundary-deps.py`에 전역 `heuristic` 단어 ban을 추가하지 않는다.
  - 이 도구는 retired runtime dependency scanner다.
  - active workflow 제거 완료는 bounded path search와 실제 behavior tests로 확인한다.

**H7 Exit:** current artifact는 owner/currentness 경계에서 처리되고, history와 retirement 기능은 의미를 잃지 않는다.

### H8 — 파일별 최종 action matrix

#### 반드시 수정

- [ ] `README.md`
- [ ] `companion-skills/ready-ticket-plan/SKILL.md`
- [ ] `companion-skills/ready-ticket-plan/agents/openai.yaml`
- [ ] `companion-skills/ready-ticket-plan/references/plan.md`
- [ ] `companion-skills/ready-ticket-plan/references/review.md`
- [ ] `companion-skills/ready-ticket-implement/SKILL.md`
- [ ] `companion-skills/ready-ticket-implement/agents/openai.yaml`
- [ ] `companion-skills/ready-ticket-implement/references/implement.md`
- [ ] `companion-skills/ready-ticket-verify/references/verify.md`
- [ ] `delivery-tools/ready-ticket/README.md`
- [ ] `delivery-tools/ready-ticket/src/plan-binding.js`
- [ ] `delivery-tools/ready-ticket/tests/helpers.js`
- [ ] `delivery-tools/ready-ticket/tests/authority-plan.test.js`
- [ ] `evaluation/ready-verification/README.md`
- [ ] `evaluation/ready-verification/calibrate.py`
- [ ] `evaluation/ready-verification/completion.py`
- [ ] `evaluation/ready-verification/inspect_run.py`
- [ ] `iis-adaptive-planning/agents/openai.yaml`
- [ ] `iis-adaptive-planning/references/00-baseline-coexistence.md`
- [ ] `iis-adaptive-planning/references/06-verification-triage.md`
- [ ] `iis-adaptive-planning/references/07-terminal-report.md`
- [ ] `iis-adaptive-planning/references/08-delivery-continuation.md`
- [ ] `iis-adaptive-planning/references/09-run-contract.md`
- [ ] `iis-adaptive-planning/templates/ADAPTIVE-RUN-CONTRACT.template.md`
- [ ] `iis-workflow/SKILL.md`
- [ ] `tests/test_ready_agent_capture.py`
- [ ] `tests/test_ready_completion_calibration.py`

#### 삭제

- [ ] `companion-skills/ready-ticket-plan/references/heuristic.md`

#### test 보강을 위해 수정 권장

- [ ] `tests/test_ready_ticket_boundary_tools.py`
  - candidate release manifest에 `companion-skills/ready-ticket-plan/references/heuristic.md`가 없음을 targeted assertion으로 확인
  - retired Probe cleanup/restore test는 그대로 유지

#### 실제 소비 여부에 따라 조건부 수정

- [ ] `docs/planning/work/transition-baseline-protocol/plans/PLAN-001.md`

#### 원칙적으로 수정하지 않음

- [ ] `delivery-tools/ready-ticket/src/verification-binding.js`
- [ ] `evaluation/ready-verification/planning-cases.json`
- [ ] `scripts/sync_installed_iis.py`의 retired cleanup 항목
- [ ] `scripts/check-ready-boundary-deps.py`
- [ ] 역사 engineering docs 두 파일
- [ ] Ready verifier host terminal schema 및 finalizer contract

## 5. 테스트 및 관측 계획

### 5.1 빠른 구조/consumer 회귀

Repository Root에서:

```text
python3 -B -m unittest \
  tests.test_ready_agent_capture \
  tests.test_ready_completion_calibration \
  tests.test_adaptive_run_contract_check \
  tests.test_ready_ticket_boundary_tools
```

Ready boundary package에서:

```text
cd /home/user01/project/iis-skills/delivery-tools/ready-ticket
npm test
```

관측 기준:

- [ ] no-Heuristic `iis-plan-review/v1` fixture가 ADMIT
- [ ] missing reviewer origin은 stale
- [ ] stale Plan/Ticket/authority는 stale
- [ ] `REVISE`와 `EVIDENCE_NEEDED`는 not admitted
- [ ] ordinary implementation source change는 admission shape를 자동 stale하게 하지 않음
- [ ] verification binding/finalization tests에 회귀 없음
- [ ] parser가 intermediate/quoted/conflicting output을 lead completion으로 오인하지 않음
- [ ] fake role list/JSON으로 preparation setup 성공 불가

### 5.2 저장소 전체 회귀

```text
cd /home/user01/project/iis-skills
python3 -B run_tests.py
python3 -B scripts/check-ready-boundary-deps.py --root /home/user01/project/iis-skills
```

- [ ] 전체 Python unittest discovery 통과
- [ ] boundary dependency scan 통과
- [ ] scanner PASS를 별도 Heuristic 제거의 유일한 증거로 사용하지 않음

### 5.3 Bounded active-dependency search

아래 active 범위에서 삭제된 역할의 호출·field·model row·reference가 없어야 한다.

```text
companion-skills/ready-ticket-plan
companion-skills/ready-ticket-implement
delivery-tools/ready-ticket
evaluation/ready-verification
iis-adaptive-planning
iis-workflow/SKILL.md
README.md
```

남는 검색 결과는 각각 다음 중 하나로 설명되어야 한다.

- historical evidence
- retired payload rejection/host-link cleanup
- current-artifact migration note
- 이 engineering TODO
- 일반명사이며 active role dependency가 아닌 문맥

문자열 0건을 완료 기준으로 사용하지 않는다. active path에서 다음 유형이 0건인지 확인한다.

- [ ] `references/heuristic.md` link/load
- [ ] `review.heuristic` producer/consumer
- [ ] `planner -> heuristic` 또는 `Plan -> Heuristic` route
- [ ] Heuristic model selection
- [ ] fixed `prepare/heuristic` stage
- [ ] exact five-role completion requirement

### 5.4 Preparation semantic evaluation

실제 immutable evaluation payload와 별도 actor-visible neutral paths를 사용한다. 최소 비교 분모:

| Case | 기대되는 reviewer 책임 |
|---|---|
| `prepare-simple` | 충분한 bounded method를 과잉 확장 없이 ADMIT 가능 |
| `prepare-competing-cause` | passing helper test 뒤 ordinary-entry bypass 탐지 |
| `prepare-shared-order` | shared writer/reader 및 bypassed path 탐지 |
| `prepare-irrelevant-counterexample` | out-of-scope counterexample 기각 |
| conditional 3종 | support/refutation/unavailable에 따른 expansion gate 구분 |
| `prepare-evidence-reuse` | exact evidence currentness 확인과 합법적 재사용 |
| `prepare-feedback-loop` | related parser consumers와 separate remote defect 모두 accounting |

- [ ] 각 case에서 raw Planner/reviewer/lead events를 보존한다.
- [ ] reviewer decision과 rationale를 직접 검토한다.
- [ ] model clean exit나 JSON shape만으로 semantic 성공을 선언하지 않는다.
- [ ] no finding을 ADMIT 증거로 사용하지 않는다.
- [ ] 실제 호출 시간/토큰을 측정했다면 baseline과 동일한 조건에서만 보고한다.

### 5.5 Immutable candidate package

source/test가 모두 통과한 뒤 isolated store에만 candidate를 준비한다.

```text
python3 -B scripts/sync_installed_iis.py prepare \
  --source /home/user01/project/iis-skills \
  --store <isolated-store>

python3 -B scripts/sync_installed_iis.py check \
  --store <isolated-store> \
  --bundle <prepare가 반환한 bundle_id>
```

Candidate readback:

- [ ] family가 `ready-boundary-tools`
- [ ] required Plan/Implement/Verify skills와 boundary tools가 같은 manifest에 존재
- [ ] `companion-skills/ready-ticket-plan/references/heuristic.md`가 manifest에 없음
- [ ] `plan-binding.js`가 no-Heuristic review를 소비하는 새 bytes
- [ ] Plan/Implement/Adaptive prompts가 삭제된 role을 요청하지 않음
- [ ] Verify terminal/finalizer code는 의도하지 않은 변경이 없음
- [ ] retired Probe payload가 candidate에 없음
- [ ] prepare가 operating host pointer를 바꾸지 않음

## 6. Activation, currentness 및 rollback TODO

실제 operating install 전환은 source 구현 완료와 별도 operator action이다.

- [ ] **A1** exact candidate bundle ID와 source revision을 기록한다.
- [ ] **A2** active writer/reviewer/implementer/verifier/service가 quiescent인지 host evidence로 확인한다.
  - cancel receipt, job/session ID 또는 response loss만으로 settlement를 추론하지 않는다.
- [ ] **A3** current Plan/review를 소비 중인 actor가 있다면 해당 invocation을 먼저 settle하거나 old bundle에서 끝낸다.
- [ ] **A4** operator가 선택한 host에 기존 installer `activate --confirm-quiescent`를 사용한다.
- [ ] **A5** activation timeout/network failure가 나면 같은 activation을 blind retry하지 않는다.
  - `installed.json`, `current` pointer, managed links와 candidate ID를 read-only로 확인한다.
  - 반영/미반영이 확정된 뒤에만 다음 동작을 선택한다.
- [ ] **A6** fresh top-level host/session에서 실제 loaded skill와 boundary identity를 확인한다.
  - `prepare/check` 성공만으로 loaded identity를 주장하지 않는다.
  - 이전 대화에 이미 주입된 old skill text는 pointer 변경으로 사라지지 않으므로 fresh session이 필요하다.
- [ ] **A7** fresh session에서 최소 smoke를 확인한다.
  - Plan skill이 deleted reference를 요청하지 않음
  - reviewer JSON에 `heuristic` field가 없음
  - actual admission이 성공/거절 matrix를 따름
  - verification-only가 새 Plan을 요구하지 않음
- [ ] **A8** rollback이 필요하면 installer rollback을 사용한다.
  - rollback은 이전 release/link identity를 복원할 뿐 product/external effects를 되돌리지 않는다.
  - intervening user change가 있으면 덮어쓰지 않고 중단한다.

## 7. 위험과 차단 조건

| 위험 | 실제 실패 형태 | 예방/판별 |
|---|---|---|
| 독립 탐색 손실 | weak Plan이 writer diagnosis 그대로 ADMIT | Review에 original-contract-first/counterexample 책임 추가, semantic cases 실행 |
| producer/consumer 불일치 | 새 review가 old binder에서 `PLAN_REVIEW_STALE` | same immutable bundle cutover, fresh loaded identity 확인 |
| provenance 약화 | Heuristic 조건 제거하며 reviewer origin까지 제거 | binder test에서 reviewer/evidence 각각 누락 거절 |
| 고정 revision 제거 오해 | `REVISE` 자체나 Planner revision 능력까지 삭제 | one-shot normal path만 단순화, actual REVISE는 terminal로 보존 |
| material re-entry dead route | 구현 중 삭제 역할로 복귀하거나 old ADMIT 재사용 | 모든 Implement/Adaptive route를 revision→review→fresh actor로 동기화 |
| Verify 기능 손실 | 이름 제거하며 finding disposition/frontier 삭제 | 명칭만 수정, enums/Flow/AC/terminal/finalizer unchanged test |
| disabled path 회귀 | Verification no인데 verifier/done 실행 또는 review 미요구 | Adaptive stage matrix와 Run Contract tests |
| verification-only 회귀 | 이미 구현된 target에 새 Plan 강제 | Verify optional navigation/entry smoke |
| evaluation false positive | 3 role 이름만 맞춘 fake record가 COMPLETE | raw events/model/current review/protected snapshot 검사 유지 |
| current Plan hash drift | live bound Plan 대량 문자열 변경 | exact consumer 확인 후 owner revision + fresh review |
| legacy upgrade 회귀 | 오래된 Probe link가 host에 남음 | retired cleanup code와 migration/remove tests 유지 |
| 역사 왜곡 | 과거 incident/roadmap을 현재 구조로 rewrite | historical docs 보존 및 active dependency와 분리 |
| 부분 activation | skill은 새 shape, runtime은 old shape | candidate 한 개에 전체 변경 포함; source/installed in-place edit 금지 |

다음 중 하나면 implementation 완료가 아니라 **BLOCKED/PARTIAL**로 보고한다.

- 독립 reviewer invocation을 얻을 수 없음
- 저장소 밖 required consumer와 schema compatibility가 미결정
- current live Plan/review/worker settlement를 확인하지 못한 채 해당 artifact를 바꿔야 함
- no-Heuristic producer와 consumer를 같은 candidate로 패키징할 수 없음
- reviewer-origin 또는 stale/non-ADMIT protection이 회귀
- Verify machine terminal/finalizer contract에 의도하지 않은 변화가 발생
- semantic cases에서 competing-cause/shared-order/feedback-loop를 reviewer가 반복적으로 놓치고, method/evidence 변경 없이 shape만 통과

## 8. Definition of Done

### Preparation contract

- [ ] 별도 Heuristic reference 파일이 active payload에서 삭제됐다.
- [ ] Plan Skill이 Planner → independent reviewer → lead 구조만 설명한다.
- [ ] reviewer는 원계약과 primary evidence에서 counterexample을 직접 판단한다.
- [ ] fixed Heuristic/revision invocation이 없다.
- [ ] actual `REVISE/EVIDENCE_NEEDED`와 후속 Planner revision은 유지된다.

### Runtime admission

- [ ] 정상 no-Heuristic `iis-plan-review/v1`이 actual core admission을 통과한다.
- [ ] missing reviewer origin은 거절된다.
- [ ] stale Plan/Ticket/authority는 거절된다.
- [ ] `REVISE/EVIDENCE_NEEDED`는 admission을 얻지 못한다.
- [ ] conditions와 start scope validation이 유지된다.

### Implementation routing

- [ ] material method change가 dependent mutation을 중단한다.
- [ ] affected Plan revision과 current independent review가 필요하다.
- [ ] prior actor settlement 뒤 fresh actor가 새 admission으로 시작한다.
- [ ] local equivalent change와 product-authority return 경계가 유지된다.

### Verify

- [ ] 별도 Heuristic 단계처럼 보이는 active 명칭이 없다.
- [ ] integrated counterexample frontier와 finding dispositions가 유지된다.
- [ ] 모든 authored Flow/AC, target stability, cleanup, external-effect settlement가 유지된다.
- [ ] terminal machine fields, opaque handle와 `ready_finalize` semantics가 바뀌지 않았다.
- [ ] verification-only direct entry가 유지된다.

### Adaptive/workflow

- [ ] deleted role을 model-select/dispatch하지 않는다.
- [ ] preparation-only는 implementation/verdict/done 권한이 아니다.
- [ ] Implementation yes는 current independent review를 요구한다.
- [ ] Verification no는 final verifier/verdict/done를 만들지 않는다.
- [ ] READY_EXECUTION_PLANS는 모든 required Ticket의 actual current ADMIT와 lead terminal을 요구한다.

### Evaluation

- [ ] 정상 preparation이 planner/reviewer/lead 3 invocations다.
- [ ] exact three-role provenance와 current review가 없으면 setup 완료가 아니다.
- [ ] competing-cause/shared-order/conditional/feedback-loop cases가 decision-relevant 결과를 낸다.
- [ ] 호출 수 변화 외 시간·비용·품질 개선은 실제 측정 없이 주장하지 않는다.

### Bundle and rollout

- [ ] source 전체 Python tests와 Ready boundary Node tests가 통과한다.
- [ ] isolated candidate prepare/check가 통과한다.
- [ ] candidate active payload에 deleted reference/field/route/model row가 없다.
- [ ] retired Probe cleanup과 rollback support가 유지된다.
- [ ] operator-approved quiescent activation 후 fresh session에서 loaded identity와 smoke가 확인된다.
- [ ] 남은 `heuristic|휴리스틱` 검색 결과는 history, retirement, current-artifact note, 이 TODO 또는 비역할 일반명사로 각각 설명 가능하다.

## 9. 권장 commit 분할

부분 release를 허용한다는 뜻이 아니라 review와 rollback을 쉽게 하기 위한 source commit 구분이다.

1. **Commit A — Preparation contract + review schema**
   - Plan Skill/references/prompt
   - delete `heuristic.md`
   - `plan-binding.js`, fixtures, admission tests
2. **Commit B — Implementation/Verify/Adaptive routing**
   - material-method routes
   - Verify terminology-only change
   - Adaptive/router/template/default prompts
3. **Commit C — Evaluation harness**
   - 5 turns → 3 turns
   - role provenance, CLI choices, docs, parser/completion tests
4. **Commit D — Candidate/rollout assertions and current-artifact handling**
   - targeted installer test
   - conditional current Plan revision only when actually consumed
   - full regression evidence

각 commit 후 관련 focused tests를 실행하되, **배포 candidate는 A–D 전체가 포함된 하나의 immutable bundle**이어야 한다.

## 10. 구현 owner가 최종 보고할 형식

```text
IIS HEURISTIC REMOVAL IMPLEMENTATION RESULT

Repository Root: /home/user01/project/iis-skills
Baseline: main@fed5ed51ee0795f26b0c3392ff230554a7c1bc13 | <actual updated baseline>
Changed files: <exact list>
Deleted files:
- companion-skills/ready-ticket-plan/references/heuristic.md
Review schema: iis-plan-review/v1, heuristic field not produced/required
Preparation path: planner -> reviewer -> lead
Material-method re-entry: Plan revision -> independent review -> fresh actor
Verification machine contract changed: no
Current Plan handling: unchanged historical | revised with fresh review | blocked with exact reason
Tests:
- Ready boundary npm test: <actual result>
- Python full suite: <actual result>
- dependency scan: <actual result>
- preparation semantic cases: <actual cases/results/limits>
Candidate bundle: <bundle id | not prepared>
Activation: NOT PERFORMED | <actual operator-approved result>
Known limitations: None | <exact evidence/currentness/external-consumer limit>
Completion: COMPLETE | PARTIAL | BLOCKED
```

`COMPLETE`는 이 문서의 Definition of Done 전체가 actual evidence로 닫힌 경우에만 사용한다. 문자열 제거, unit tests, candidate prepare 또는 activation 중 하나만 성공한 것을 전체 완료로 확대하지 않는다.
