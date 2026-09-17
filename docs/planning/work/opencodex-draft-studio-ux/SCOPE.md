# Scope: OpenCodex Draft Generation and One-Click Studio UX

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md sha256:d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md sha256:59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51

## Outcome

BLOCK-10을 통해 라이브 이미지 생성 모델 결속과 sparse/empty prompt 수용이 완료되었으나, 사용자가 의미 있는 스토리보드와 연출 프롬프트를 구성하려면 여전히 5개 컷의 역할, 비트, 대사, 프롬프트를 일일이 손으로 구상하고 입력해야 하는 큰 인지적·조작적 부담이 존재한다. 과거 `comic` 시스템에는 로컬 OpenCodex LLM(`http://127.0.0.1:10100/v1`)을 통해 한 줄 주제에서 콘티 전체를 자동 기획하는 파이프라인이 있었으나, `comic_new`에는 해당 기능이 전무하여 사용 편의성이 극도로 저하되어 있다.

이 Scope는 `BASELINE-003`의 `BLOCK-11`을 선택한다.
로컬 OpenCodex 서비스(`http://127.0.0.1:10100/v1`)와 통신하는 비동기 LLM 클라이언트와 웹툰 스토리보드 기획 프롬프트를 `comic_new`에 도입하고, 신규 엔드포인트 `POST /api/baselines/generate-draft`를 제공한다.
해당 엔드포인트는 사용자의 짧은 주제(topic) 또는 시놉시스를 받아, 각 컷의 역할(`role`), 연출 비트(`beat`), 대사(`dialogue`), 상세 이미지 생성 프롬프트(`prompt`)를 일관된 서사 흐름으로 자동 생성하여 반환한다. LLM 호출은 Gemini를 우선으로 하고 실패 시 Luna로 자동 폴백하는 체인을 적용하며, 구조화된 JSON 파싱 및 유효성 검증을 거친다.
프론트엔드 `RebaselineDialog.vue`를 전면 개편하여, 21개 입력칸을 기본 강제 노출하는 대신 상단에 [주제/시놉시스 입력]과 **[AI 콘티 자동 생성]** 버튼을 배치한다. 사용자가 한 줄만 입력하고 생성 버튼을 누르면 모든 컷의 기획 내용이 즉시 채워져 단 한 번의 [승인] 클릭으로 베이스라인을 통과할 수 있게 한다.
OpenCodex 서비스가 오프라인이거나 응답에 실패할 경우 사용자에게 명확하고 정직한 오류 메시지를 제공하며, 기존 수동 입력 및 기본값 수용 경로로 자연스럽게 복귀할 수 있도록 보장한다.

포함: `src/comic_new/llm/` 모듈 (OpenCodexClient, fallback 체인, 시스템 프롬프트 및 스키마 검증), `POST /api/baselines/generate-draft` FastAPI 엔드포인트 및 DTO 계약, `RebaselineDialog.vue`의 한 줄 기획 UI 및 자동 채움 로직, 관련 단위/회귀 테스트.

제외: 1024 고정 폭 외 동적 캔버스 높이 및 컷 로컬 말풍선 좌표계(`BLOCK-12`), 임의 N컷 스키마 및 컷 동적 추가/삭제/재정렬(`BLOCK-13`), ima2 이미지 생성 알고리즘 변경.

## Acceptance

### A. OpenCodex LLM 통합 및 자동 폴백 체인
로컬 OpenCodex(`http://127.0.0.1:10100/v1`)와 통신하여 웹툰 스토리보드를 기획하는 모듈이 동작한다. 1차 모델(예: Gemini) 호출 실패(타임아웃, 5xx 등) 시 2차 모델(예: Luna)로의 자동 폴백이 매끄럽게 수행되며, 최종 출력은 컷별 `role`, `beat`, `dialogue`, `prompt`를 포함하는 정형화된 데이터 구조로 검증된다.

### B. POST /api/baselines/generate-draft API 계약
유효한 `topic`(또는 `synopsis`)을 담은 요청을 보냈을 때, HTTP 200과 함께 각 컷(1~5)의 완성도 높은 비트와 상세 이미지 생성 프롬프트, 대사가 포함된 초안 객체를 반환한다. 주제가 비어있거나 공백뿐인 경우 명확한 HTTP 400 Validation Error를 반환하며, 와이어 스키마 형식 오류는 HTTP 422를 반환한다.

### C. OpenCodex 장애 시의 정직한 실패 및 수동 입력 보존
OpenCodex 서비스가 다운되었거나 타임아웃/오류가 발생했을 때, 서버는 HTTP 502/503과 함께 원인을 설명하는 정직한 오류 응답을 반환하며 전체 애플리케이션이나 DB가 크래시되지 않는다. 프론트엔드는 토스트 및 대화상자에 안내를 표시하고, 사용자가 기존에 작성 중이던 입력값이나 수동 편집 상태를 손상 없이 보존한다.

### D. 프론트엔드 One-Click Studio UX
`RebaselineDialog.vue` 진입 시 한 줄 주제 입력창과 [AI 콘티 자동 생성] 액션이 최우선으로 안내된다. 생성 완료 시 각 컷 필드가 즉시 채워져 사용자가 세부 수정하거나 그대로 즉시 [승인]할 수 있으며, 승인 성공 시 대화상자가 닫히고 5개 컷 모두 `intelligent_default`, `llm_draft` 또는 `user` 프롬프트로 스튜디오에 반영된다.

### E. 4대 인과 불변식 보존
초안 생성 API 호출 및 결과 적용은 기존 베이스라인 트랜잭션의 Monotonic Sequence CAS, STOP 사전 커밋 차단, 승인 철회, 릴리즈 정본 검증 계약을 전혀 약화시키지 않는다.

## Non-Goals

- 동적 캔버스 높이 계산 및 컷 로컬 말풍선 좌표계 (`BLOCK-12`)
- SQLite DDL 변경 및 N컷 동적 관리 (`BLOCK-13`)
- 외부 상용 LLM API 직접 결제 및 신규 자격증명 등록

## Open Decisions

None
