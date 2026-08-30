---
name: ready-ticket-implement
description: "Implement one existing IIS Ready Ticket and perform implementer self-check. Use for exact Ready Ticket delivery. Execution defaults to DIRECT; SUBAGENT execution is supported only when the current user explicitly selects it and is mandatory checkpointed execution. This skill never performs or adjudicates the separate verification authority."
---

# Ready Ticket Implement

## 목적과 권위

이 스킬은 IIS Planning이 만든 하나의 Ready Ticket을 그 Ticket이 승인한 제품 자체에 구현한다. IIS Planning을 재개하거나 Ticket 의미를 다시 계획하지 않는다.

구현 worker는 구현과 구현자 self-check를 소유한다. Separate heuristic-probe authority의 finding/exploration과 Separate verification authority의 실행 여부, AC verdict, whole-Ticket verdict와 terminal `done` 전이는 소유하지 않는다.

실제 작업 전에 [references/implement.md](references/implement.md)를 전부 읽는다.

## 입력

- Ticket: `<TICKET_PATH>`
- Project Root: `<PROJECT_ROOT>`
- 추가 사용자 지시: `<ADDITIONAL_USER_INSTRUCTIONS>`

## 실행 topology

Top-level 기본 실행 모드는 `DIRECT`다.

- `DIRECT`: 현재 Main이 implementation worker 역할을 직접 수행한다.
- `SUBAGENT`: 현재 사용자가 이 exact implementation stage에 `SUBAGENT`를 명시한 경우에만 Outer Main이 exact Ticket 하나를 정확히 한 명의 implementation worker에게 할당한다.
- 모델 capability, 작업 난도, 비용 또는 worker availability만으로 mode를 바꾸지 않는다. 실패를 `DIRECT`로 자동 대체하지 않는다.
- Outer Main은 exact Ticket, Project Root, 추가 사용자 지시와 `Delegated Worker: yes`를 worker assignment에 포함한다. `Delegated Worker: yes`를 받은 worker는 이 스킬을 다시 위임하지 않고 implementation core를 직접 수행한다.
- 한 Ticket을 여러 worker로 분할하지 않으며 detached worker, background delivery queue, polling controller 또는 persistent execution scheduler를 만들지 않는다.
- 필요한 child/checkpoint/terminal capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 보고한다.

`SUBAGENT`에서 Outer Main은 assignment, checkpoint continuation (`CONTINUE | STEER | STOP`)과 terminal fan-in만 소유하며 source implementation을 중복 수행하지 않는다.

## Ready Ticket 상태 게이트

- 시작 정상 상태는 exact `ready`다.
- `done`이면 재구현하지 않는다.
- `draft` 또는 `blocked`이면 구현을 시작하지 않는다.
- 이 스킬은 Ticket status를 `done`으로 바꾸지 않는다. 정상 구현 입력인 `ready`는 구현 완료 후에도 그대로 유지한다.

## Ready runtime guard

이 스킬을 읽은 execution은 내부 Ready runtime을 사용한다. runtime은 제품 의미를 판정하지 않고 authority currentness와 관찰·mutation의 실행 규율만 강제한다.

- `DIRECT`: source/config mutation 전에 exact Ticket과 Project Root로 `ready_guard begin_direct`를 완료한다.
- `SUBAGENT`: Outer Main이 exact Ticket과 Project Root로 `ready_guard assign_subagent`를 실행하고, 지정된 한 child가 받은 assignment로 `ready_guard begin_delegated`를 완료한다.
- runtime은 exact Ticket status/validator와 적용되는 Parent Spec·Behavior/UI Authority를 직접 bind한다. worker가 digest나 revision을 제출해 대신 증명하지 않는다.
- Project Root confinement, protected authority write, duplicate observation, broad rescan, mutation revision/current evidence, bounded retry, operation serialization과 managed local service lifecycle은 runtime 책임이다.
- native Bash가 구조적으로 read-only인지 확정되지 않으면 shell 문자열을 추측하지 않고 structured `ready_argv`를 사용한다.
- terminal 결과 전에 runtime도 `complete` 또는 `block`으로 닫는다. runtime state/tool 이름은 caller-facing result의 새 필수 필드가 아니다.

### Zero-Mock Delivery 불변조건

구현, self-check와 completion evidence는 실제 production code path와 실제 dependency/readback만 사용한다. mock/fake/stub 구현, patching API, HTTP/database/provider interception, in-memory fake repository, mock-mode 환경변수와 가짜 응답을 acceptance evidence로 사용하지 않는다.

- acceptance test는 `ready_argv acceptance`로 실행하며 `provenance_kind`를 정확히 `LOCAL_PATH`, `LOCAL_SQLITE`, `EXTERNAL_HTTP_PROVIDER` 중 하나로 지정한다. resolved argv에서 계산한 실제 selected test roots와 `evidence_paths`는 exact canonical set으로 일치해야 하며 ambiguous/unsupported selector는 fail-closed한다. package runner는 original/resolved argv와 `package.json`을 fingerprint하고 exact adjacent `pre<name>`/`post<name>` lifecycle hook이 configured이면 실행 전에 차단한다. clean local PASS는 command, production/evidence import closure, actual dependency/config, authoritative readback, runner config와 current mutation revision의 fingerprint 및 `mock_taint: false` provenance를 남기며, JS/TS taint 검사는 global/member/destructuring/alias flow를 따른다. 일반 Bash나 `ready_argv mutate`로 acceptance runner를 우회하지 않는다.
- 임시 디렉터리, 격리된 실제 DB/container, 실제 schema/persistence와 입력용 seed data는 허용한다.
- 현재 runtime은 `EXTERNAL_HTTP_PROVIDER` 실행과 readback의 correlation을 지원하지 않으므로 command/readback argv를 실행하지 않고 acceptance를 `INCONCLUSIVE`로 기록한다. 구현은 mock으로 대체하지 않고 `Completion: BLOCKED`로 닫는다.
- `Completion: COMPLETE`에는 non-empty acceptance provenance denominator가 필요하고 그 모든 entry가 clean/current여야 한다. 일반 read-only observation은 이를 대체하지 않으며, runtime이 mock-taint violation을 기록했거나 전체 fingerprint가 `ready_guard complete`에서 current 상태로 재검증되지 않으면 COMPLETE 진입을 허용하지 않는다.

## 제품 의미 해석

구현 시작 전 한 문장으로 `이번 Ticket이 실제 제품에 추가하거나 변경하는 observable product outcome`을 고정한다. 제품 의미는 다음 authority에 계속 속한다.

1. 현재의 명시적 사용자 지시
2. Ticket 전체
3. Parent Spec
4. Behavior Authorities
5. 승인된 Design/UI Authority
6. Implementation Constraints와 References
7. 현재 repository/runtime의 직접 관찰 사실

Ticket은 이번 구현 경계, Parent Spec은 상위 결과, Behavior Authority는 identity·ownership·ordering·lifecycle 의미, Design/UI Authority는 사용자-visible 구조와 상호작용을 소유한다. References와 repository/runtime는 evidence/context이지 새 제품 권위가 아니다.

구현 편의, 기존 구조, 최소 변경 또는 test 편의를 이유로 승인된 결과를 축소·대체하지 않는다. Scope/Non-Goals 밖 제품 surface나 lifecycle guarantee를 만들지 않는다. 실질적 authority 충돌로 faithful direction을 확정할 수 없으면 `Completion: BLOCKED`로 닫는다.

## Verification-flow 해석과 self-check

각 authored Verification flow의 Parent outcome/AC/Behavior authority mapping, initial state, trigger, acceptance boundary, expected observable result, authoritative readback, decision boundary, disposition, authored independent-verification requirement, acceptance surface, external condition과 적용되는 ordering/interruption/persistence/external-effect/UI 경계를 그대로 사용한다.

Verification flow를 임의의 1:1 파일 작업으로 바꾸지 않는다. 구현 change와 self-check evidence를 각 flow에 연결하고, acceptance boundary와 authoritative readback으로 current product 결과를 확인한다. Authored independent-verification requirement가 있으면 원문 의미와 관련 implementation/self-check evidence를 final handoff에 보존하되 충족 여부는 판정하지 않는다.

## Checkpoint와 종료

`SUBAGENT` worker는 contract preflight 뒤 첫 source-file 변경 전에 `IMPLEMENTATION HANDOFF REPORT`를 `PRE_ACTION` checkpoint로 direct parent에게 반환하고 Parent decision 전 `FIRST_SOURCE_FILE_CHANGE`로 넘어가지 않는다. `DIRECT`에는 Parent checkpoint가 없다.

구현 방향, authority 해석, change surface 또는 evidence 전략이 material하게 바뀌는 경우에만 `IMPLEMENTATION TURN REPORT`를 `MATERIAL_TURN` checkpoint로 반환한다. 정상 진행, 일시적 test failure, 스타일 또는 단순 리팩터링은 periodic progress checkpoint 사유가 아니다.

`SUBAGENT`에서 PRE_ACTION 이후 runtime이 exact Ticket 또는 적용되는 canonical Parent Spec/Behavior/UI Authority drift를 감지하거나 authoritative readback이 unavailable/non-attributable해지거나 substitution을 요구하면 worker의 materiality threshold를 적용하지 않는다. 기존 `MATERIAL_TURN`을 반환하고 release 전 변경된 방향에 의존하는 mutation을 하지 않는다. `DIRECT`에서는 Parent checkpoint 없이 current authority/readback을 직접 재확인한다.

`IMPLEMENT` 완료에는 Ticket Scope/Non-Goals 보존, 모든 authored Verification-flow obligation에 연결된 current self-check evidence, unresolved authority conflict/material blocker 부재, authored independent-verification requirement evidence 보존, decision-critical source/diff/artifact/command/runtime behavior의 직접 확인이 필요하다.

`Completion: COMPLETE`여도 exact Ticket의 `Status: ready`는 유지한다. 구현 target/checkpoint와 self-check evidence를 separate heuristic-probe authority와 separate verification authority에 넘길 navigation handoff로 보존하며 이후 probe, verification 또는 IIS planning continuation을 자동 실행하지 않는다.
