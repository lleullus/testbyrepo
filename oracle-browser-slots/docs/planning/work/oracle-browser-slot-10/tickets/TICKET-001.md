# Oracle Browser Managed Slot 10 제공

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/oracle/oracle-browser-slots
Worker:
UI: no

## Goal

슬롯 10을 기존 슬롯 1~5를 보존하는 독립된 추가 관리 슬롯으로 end-to-end 제공한다.

## Acceptance Criteria

- 관리 슬롯 식별과 준비 및 상태 조회에서 슬롯 10은 승인된 관리 슬롯 behavior에 따라 지원되고, 슬롯 6~9 및 그 밖의 ID는 관리 슬롯으로 허용되지 않는다.
- 슬롯 10은 기본 endpoint `127.0.0.1:19231`과 기본 프로필 `slot-10`을 사용하며, 기존 슬롯 1~5와 독립된 준비, 상태, 단일 점유, 중복 방지 및 실행 결과 경계를 가진다.
- 슬롯 10은 기본/standard/medium에서 `(1, 2, 3, 4, 5, 10)`, light/instant/low 및 heavy/extra-high/pro에서 `(1, 2, 10)`, extended/high에서 `(3, 4, 5, 1, 2, 10)`의 호환 후보 순서를 따른다.
- 슬롯 10에서 시작된 managed session의 followup은 슬롯 10만 사용하고, 점유 시 슬롯 10만 기다리며, unavailable이면 다른 슬롯 fallback 없이 복구 가능한 실패를 반환한다.
- 슬롯 10의 로그인 성공은 계정 신원, 구독, 모델 권한 또는 workspace 권한을 증명하지 않으며 해당 운영 적합성은 운영자 책임으로 남는다.
- 슬롯 10 추가는 기존 슬롯 1~5의 capability와 각 호환 후보 내 상대 순서를 변경하지 않는다.

## Scope

- Oracle Browser 관리 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 managed followup 원 슬롯 연속성

## Non-Goals

- 슬롯 6~9 또는 그 밖의 새 관리 슬롯 ID 추가
- 슬롯별 계정 신원 식별 또는 비교
- 계정 구독, 모델 권한 또는 workspace 권한 자동 검증
- managed followup의 다른 슬롯 fallback
- 기존 슬롯 1~5의 capability 또는 호환 후보 내 상대 순서 변경
- UI 변경

## Blockers

None

## Verification

- 슬롯 10의 준비와 상태 조회를 관찰하고, 지원되지 않는 슬롯 ID가 계속 거부되며 슬롯 10의 성공 또는 실패가 기존 슬롯 상태를 변경하지 않는지 확인한다.
- 슬롯 10을 각 호환 capability의 초기 managed 실행 및 자동 배정에서 관찰하고, 승인된 후보 순서와 기존 슬롯 상대 순서가 유지되는지 확인한다.
- 슬롯 10에서 시작된 managed session을 대상으로 슬롯 가용, 점유 및 unavailable 조건의 followup 결과를 관찰해 원 슬롯 연속성, 해당 슬롯 대기 및 fallback 없는 복구 가능한 실패를 확인한다.
- 슬롯 10에서 동시 점유와 중복 요청 조건을 관찰해 단일 점유 및 중복 방지 경계를 확인한다.
- 로그인된 슬롯 10의 준비 및 실행 결과를 관찰해 로그인 성공과 계정 신원, 구독, 모델 권한 및 workspace 권한의 운영자 책임이 구분되는지 확인한다.

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성

## References

- ../SPEC.md
