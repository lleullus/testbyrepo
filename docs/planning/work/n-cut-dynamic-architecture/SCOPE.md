# Scope: N-Cut Dynamic Architecture and Cutover

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md sha256:d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md sha256:59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51

## Outcome

BLOCK-10, BLOCK-11, BLOCK-12를 통해 라이브 모델 결속, 한 줄 LLM 콘티 초안 생성, 단일 정수 슬롯 분할 및 컷 로컬 말풍선 좌표계가 모두 확립되었다. 그러나 데이터베이스 스키마(`schema.sql`), 백엔드 검증(`store.py`, `composition_service.py`, `server.py`), 프론트엔드 계약(`contracts.ts`)에는 여전히 '정확히 5컷(exactly five cuts)'이라는 인위적이고 경직된 고정 제약이 하드코딩되어 있다. 이로 인해 4컷 만화, 6컷 만화, 또는 8컷 이상 등 가변 N컷 웹툰을 생성하지 못하는 제품 결손이 남아있다.

이 Scope는 `BASELINE-003`의 마지막 전이 블록인 `BLOCK-13`을 선택한다.
1. SQLite DDL 및 스키마 검증에서 `cut_id BETWEEN 1 AND 5`와 `cuts` 테이블의 불변 5개 행 강제 트리거를 해제하고, 임의의 양수 컷 수($N \ge 1$)를 지원하도록 스키마 v7로 마이그레이션한다.
2. `store.py`, `composition_service.py`, `server.py`, `delivery.py` 및 프론트엔드 `contracts.ts`, `studio.ts`에서 하드코딩된 `[1, 2, 3, 4, 5]` 및 `len(cuts) == 5` 가정을 제거하고, 프로젝트에 등록된 활성 컷 집합(Active Cut Set, $N \ge 1$)을 기반으로 동적 컷 생애주기(생성, 인텐트 수정, 개별 생성, 조판, 릴리즈)를 수행하도록 일반화한다.
3. 4대 인과 불변식(Monotonic Sequence CAS, STOP Pre-commit Lockout, Atomic Approval Revocation, Destination Content Readback)을 $N$컷 전체에 대해 100% 보존하며, 활성 컷 전체가 Current일 때만 릴리즈를 허용하는 All-or-Nothing 완결성 게이트를 $N$컷으로 온전히 전환(Cutover)한다.

포함: SQLite schema v7 및 v6→v7 migration, `store.py`의 $N \ge 1$ 컷 생성/관리/검증 일반화, `composition_service.py`의 $N$컷 렌더링/머티리얼라이즈, `server.py`의 동적 컷 DTO/엔드포인트 지원, 프론트엔드 튜플 고정 해제, N컷 완결 릴리즈 및 4대 불변식 회귀 검증.

제외: 컷 간 무한 동적 드래그 앤 드롭 재정렬 애니메이션 전용 프레임워크(Phase 2 UX 고도화), 외부 유료 블로거 계정 실발행.

## Acceptance

### A. SQLite Schema v7 및 N >= 1 지원
SQLite `cuts`, `cut_intents`, `generation_jobs`, `artifact_cuts`의 `CHECK(cut_id BETWEEN 1 AND 5)` 제약이 `CHECK(cut_id >= 1)`로 완화된다. 프로젝트 생성 시 또는 베이스라인 설정 시 지정된 $N \ge 1$(예: 3컷, 4컷, 6컷)개의 컷이 정상 초기화 및 관리된다. 기존 v6 데이터베이스는 안전하게 v7으로 무손실 마이그레이션된다.

### B. 백엔드 서비스 및 API의 동적 N컷 일반화
`store.py`, `composition_service.py`, `server.py`가 고정 길이 5개 튜플에 의존하지 않고, 등록된 활성 컷 목록(`cuts`)의 실제 개수 $N$에 맞춰 스냅샷 조회, 베이스라인 승인, 컷별 인텐트 수용, 조판 렌더링을 일관되게 수행한다.

### C. 프론트엔드 N컷 지원 및 스튜디오 UI 연동
프론트엔드 `contracts.ts`와 `studio.ts`가 $N$개의 컷 배열을 유연하게 수용하며 유효성 검사를 통과한다. 스튜디오 화면(CutRail, CompositionCanvas 등)에서 지정된 $N$개의 컷 카드와 슬롯이 1px의 오차도 없이 비례적으로 정상 렌더링된다.

### D. All-or-Nothing 완결 릴리즈 정합성 보존
$N$개 컷 중 단 1개라도 미실현(Unrealized) 또는 Stale 상태일 경우, Review Materialization 및 릴리즈 승인(`export-png`, `blogger`)은 기존과 동일하게 엄격히 차단된다. $N$개 컷이 모두 Current 상태가 되었을 때만 정상 조판 아티팩트가 생성되고 릴리즈 승인이 발급된다.

### E. 4대 인과 불변식 및 프로덕션 컷오버 완성
임의의 $N \ge 1$ 환경에서도 Monotonic Sequence CAS, STOP 사전 커밋 차단, 조판/인텐트 변경 시 원자적 승인 철회, 릴리즈 목적지 해시 Readback 검증이 결점 없이 보존됨을 실측으로 증명한다.

## Non-Goals

- 복잡한 타임라인 기반 프레임 애니메이션
- 외부 배포처 추가

## Open Decisions

None
