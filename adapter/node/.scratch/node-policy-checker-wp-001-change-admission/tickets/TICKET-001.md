# TICKET-001: 현재 구조 읽기 전용 진단

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/iis-skills/adapter/node
Worker:
UI: no

## Goal

변경을 시작하지 않고도 기존 Node/TypeScript 프로젝트의 구조와 품질 정책 근거를 안전하게 파악할 수 있게 한다.

## Acceptance Criteria

- 변경 요청이 없는 상태에서 현재 프로젝트의 구조, 모듈 및 레이어 경계, SSOT와 의존 방향을 진단할 수 있다.
- 진단 결과의 책임 소유자와 재사용 후보는 실제 저장소에서 관측된 근거와 연결된다.
- 진단 중 대상 제품 소스는 변경되지 않는다.
- LLM의 근거 없는 자기 진술은 진단 증거로 인정되지 않는다.
- 필수 근거가 부족하거나 판단할 수 없는 상태는 성공으로 표시되지 않고 `INCONCLUSIVE`로 구분된다.
- 기본 결과는 통과 여부, 관측된 책임과 주요 위험을 짧게 보여주며, 필요할 때 확인하는 상세 근거와 의미가 일치한다.

## Scope

- 기존 Node/TypeScript 프로젝트의 변경 없는 현재 상태 진단
- 현재 실행 경로, 책임 소유자, 경계, SSOT, 디렉터리 위계, 의존 방향과 재사용 후보에 대한 읽기 전용 관측
- `PASS`, `FAIL`, `INCONCLUSIVE` 진단 결과와 비기술적 요약 및 상세 근거

## Non-Goals

- 사용자 변경 요청에 대한 사전검사와 제품 코드 쓰기 허용은 이 Ticket의 범위가 아니다.
- 기존 구조가 없는 새 프로젝트의 최초 구조 선택은 이 Ticket의 범위가 아니다.
- 작성된 코드의 정적 검사 또는 AI 의미 품질 판정은 이 Ticket의 범위가 아니다.
- 테스트 실행, 변이 검사, edge case 실행과 side effect 증명은 이 Ticket의 범위가 아니다.
- LLM 자동 수정, CI 소비, 배포 승인과 제품 기능 코드 구현은 이 Ticket의 범위가 아니다.
- Node/TypeScript 이외 언어는 이 Ticket의 범위가 아니다.

## Blockers

None

## Verification

- 대표적인 기존 Node/TypeScript 프로젝트를 진단했을 때 현재 구조, 경계, SSOT, 의존 방향, 책임과 재사용 후보가 저장소 근거와 함께 관측되는지 확인한다.
- 진단 전후 대상 제품 소스가 동일하며 진단이 쓰기를 발생시키지 않았는지 확인한다.
- 필요한 저장소 근거가 없거나 서로 충돌하는 경우 성공이 아니라 `INCONCLUSIVE`가 되는지 확인한다.
- 짧은 기본 결과와 펼쳐 본 상세 근거의 판정, 책임, 위험이 서로 일치하는지 확인한다.

## References

- ../SPEC.md
