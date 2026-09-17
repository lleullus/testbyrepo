# Scope: Live Model Repair and Sparse Baseline Approval

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md sha256:d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md sha256:59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51

## Outcome

현재 시스템의 기본 이미지 모델은 `generation.py`에 연결되지 않은 `nano-banana-pro`로 고정되어 있어 실제 이미지 생성이 시작부터 실패하거나 잘못된 엔드포인트로 향할 수 있다. 또한 `store.py:126`의 엄격한 유효성 검사로 인해 베이스라인 승인(`POST /api/baselines`) 시 컷 프롬프트 중 하나라도 비어 있으면 HTTP 400 Bad Request(`Intent prompt must be a non-empty string`)가 발생하여 전체 베이스라인 승인이 거절된다. 이로 인해 사용자가 아직 프롬프트가 준비되지 않은 컷 때문에 다른 준비된 단일 컷조차 탐색 생성하지 못하는 워크플로 차단이 발생한다.

이 Scope는 `BASELINE-003`의 `BLOCK-10`을 선택한다.
기본 이미지 생성 모델을 현재 로컬에서 동작 중인 live 모델인 `oauth/gpt-image-2.5-flare`로 교체하고, `nano-banana-pro`의 기본 및 폴백 사용을 배제한다.
베이스라인 승인 트랜잭션에서 빈 프롬프트(`""` 또는 공백)를 포함하는 sparse intent를 정상 수용하며, HTTP 400 오류를 발생시키지 않는다. 빈 프롬프트 컷에 대해서는 지능형 기본 프롬프트(예: `f"{source_brief} - 컷 {cut_id} ({role}: {beat})"`) 또는 규정된 기본 대체 텍스트를 할당하여 저장한다.
동시에 엄격한 비어있지 않은 유효 프롬프트 검증은 **실제 해당 컷의 생성 작업을 큐에 등록하는 시점(`enqueue_generation_jobs`)**으로 이전하여, 프롬프트가 완전히 빈 컷에 대한 잘못된 생성을 안전하게 차단한다.
이로써 사용자는 모든 컷을 선입력하지 않고도 유효한 프롬프트를 가진 단일 컷부터 독립적으로 탐색 생성할 수 있으며, 기존 4대 인과 불변식(Monotonic Sequence CAS, STOP Pre-commit Lockout, Atomic Approval Revocation, Destination Content Readback)은 손상 없이 완벽히 보존된다.

포함: `generation.py` 기본 모델 및 fallback 설정, `store.py`의 `approve_baseline` 및 `_parse_structured_intent` 빈 프롬프트 수용 로직, `enqueue_generation_jobs`의 effective prompt 비어있지 않음 검증 가드, 관련 단위/회귀 테스트, 프론트엔드 베이스라인 제출 오류 처리 완화.

제외: `POST /api/baselines/generate-draft` 엔드포인트 및 OpenCodex 연동(`BLOCK-11`), 동적 캔버스 및 컷 로컬 말풍선 좌표계(`BLOCK-12`), 임의 N컷 스키마 전환(`BLOCK-13`), 외부 블로거 계정 실발행.

## Acceptance

### A. Live Image Model Default 결속
`generation.py`의 `default_provider_factory` 및 관련 생성 서비스에서 기본 모델이 live 모델인 `oauth/gpt-image-2.5-flare`로 동작한다. 연결되지 않은 `nano-banana-pro`로의 묵시적 폴백이나 기본 할당이 완전히 제거된다. 실제 ima2 CLI 호출 인자 및 worker 생성 로그에서 올바른 모델명이 전달됨을 검증한다.

### B. Sparse Baseline Approval 허용 (빈 프롬프트 400 제거)
`POST /api/baselines`를 통해 컷 프롬프트가 빈 문자열(`""`)이거나 공백으로만 이루어진 sparse intent 요청을 제출했을 때, HTTP 400 `ValidationError`가 발생하지 않고 HTTP 200/승인 완료 상태로 전이된다. 승인된 스냅샷의 해당 컷 intent에는 지능형 기본 프롬프트 또는 기본 fallback 텍스트가 올바르게 보존·반환된다.

### C. 단일 컷 탐색 생성 및 미준비 컷 격리
5개 컷 중 컷 1에만 명시적 유효 프롬프트가 있고 나머지 컷의 프롬프트가 비어있거나 기본 상태일 때, 컷 1에 대한 생성 작업(`POST /api/generation/jobs`)이 정상 등록 및 실행된다. 다른 컷이 미완성 상태라는 이유로 컷 1의 생성이 차단되지 않는다. 컷 1의 생성이 완료되면 컷 1만 `Current` 상태로 갱신되고, 나머지 컷은 `Stale` 또는 미실현 상태를 정직하게 유지한다.

### D. Enqueue 시점의 엄격한 유효 프롬프트 검증
지능형 기본 프롬프트 대체 후에도 유효한 텍스트가 전혀 없거나 빈 문자열인 컷에 대해 직접 생성을 시도할 경우, `enqueue_generation_jobs` 단계에서 명확한 유효성 오류(Validation/Prerequisite Error)로 거절되어 큐 진입 및 낭비성 워커 호출이 방지된다.

### E. 4대 인과 불변식 및 전체 완결 릴리즈 보존
단일 컷 탐색 생성 중에도 Monotonic Sequence CAS, STOP 사전 커밋 차단, 승인 철회는 완벽히 유지된다. 단 1개 컷이라도 미실현 상태(Unrealized)이거나 최신 의도와 불일치(Stale)할 경우 최종 Review Materialize 승인 및 릴리즈(`export-png`, `blogger`)는 기존과 동일하게 원천 차단된다.

## Non-Goals

- OpenCodex LLM 호출 및 초안 생성 API (`BLOCK-11`)
- 1024 고정 너비 외 동적 캔버스 높이 계산 및 컷 로컬 말풍선 (`BLOCK-12`)
- SQLite `cuts` 테이블 DDL 변경 및 임의 N컷 확장 (`BLOCK-13`)
- 외부 블로거 실발행 계정 인증

## Open Decisions

None
