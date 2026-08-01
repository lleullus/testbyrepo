# <제목>

Status: draft
Owner: <사용자 또는 지정된 planning owner>

승인은 사용자 또는 명시된 planning owner가 확인하고, 제품 결정이 모두 해소된 뒤에만 `Status: approved`로 바꾼다. 이 파일은 복사해 직접 편집하는 Markdown 문서이며 별도 metadata나 도구가 필요 없다.

## Problem

해결할 문제와 영향을 받는 대상을 간결하게 적는다. 해결 방법을 먼저 결정하지 않는다.

## Desired Outcome

완료 시 관찰할 수 있는 결과를 적는다.

## Requirements

완료 시 관찰되어야 할 동작, 보존할 기존 동작과 승인된 제품 결정을
적는다. 예상 원인이나 구현 방법은 적지 않는다.

## Non-Goals

이번 범위에서 명시적으로 하지 않을 일을 적는다.

## Implementation Constraints

사용자가 의도적으로 고정한 제품·운영 경계, 외부 호환 계약,
보안·배포 invariant와 변경 허용 범위를 적는다. 예상 파일, 모듈,
endpoint, abstraction, 구현 순서와 test seam은 그 자체가 승인된
요구사항이 아닌 한 적지 않는다.

## Verification Expectations

완료 시 안정적인 제품·시스템 경계에서 무엇이 관찰되어야 하는지
적는다. 내부 테스트 파일, mock, collaborator 또는 test seam은
미리 고정하지 않는다.

## UI / UX

UI 작업이 아니면 `Not applicable`이라고 적는다. Prototype은 검토 자료일 뿐 권위가 아니다. 사용자 또는 명시된 planning owner가 채택한 결정만 여기에 반영한다.

## Open Questions

아직 결정되지 않은 제품·Scope·경계 또는 실현 가능성 결정을 적는다.
어떤 내부 구현 방법이 최선인지 모르는 것만으로는 Open Question이 아니다.
`approved`로 바꾸기 전에는 모두 해소하고 `None`으로 정리한다.
