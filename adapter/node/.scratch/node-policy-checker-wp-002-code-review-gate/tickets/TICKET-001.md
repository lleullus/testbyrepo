# TICKET-001: 빠른 확정 규칙 진단

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/iis-skills/adapter/node
Worker:
UI: no

## Goal

작성된 Node/TypeScript 변경에서 기계적으로 확정할 수 있는 품질 문제를 빠르게 확인하되, 제한된 진단 결과를 최종 완료 승인으로 오해하지 않게 한다.

## Acceptance Criteria

- AST 및 lint로 확정 가능한 b-1~b-3, c-1~c-5, d-1~d-3 규칙을 빠르게 진단한다.
- 빈 catch, 3단계 이상의 중첩, 함수 및 파일 크기, complexity와 max-depth를 기계적으로 판정한다.
- 기계적으로 확인 가능한 죽은 코드, 주석 처리 코드, re-export, fan-in 및 fan-out 집중을 판정한다.
- TypeScript strict 상태, `as any`, `as unknown as`, JavaScript JSDoc 의무, 순환 의존성과 고정된 경계 위반을 판정한다.
- 수치형 품질 상한은 검사기의 안전 기본값을 사용하고 저장소의 기존 기준이 더 엄격할 때만 그 기준으로 강화한다.
- 현재 코드 분포, 변경된 코드 또는 더 느슨한 저장소 설정으로 안전 기본 상한을 약화하지 않는다.
- 확정 규칙을 실행하거나 판정할 능력이 부족하면 누락을 성공으로 표시하지 않고 `INCONCLUSIVE`로 구분한다.
- 빠른 진단 결과는 작업 완료를 승인하는 최종 `PASS`로 사용할 수 없다는 점이 명확히 관측된다.
- 진단 전후 대상 제품 소스는 동일하다.

## Scope

- Node/TypeScript 변경에 대한 AST 및 lint 기반 빠른 확정 규칙 진단
- 안전 기본 상한과 더 엄격한 저장소 규칙의 적용
- 확정 규칙의 발견 위치와 제한된 진단 상태
- 최종 완료 verdict와 구별되는 빠른 진단 결과

## Non-Goals

- 무의미한 fallback, 의미 중복, 숨은 결합과 암묵 계약에 대한 AI 의미 판정은 이 Ticket의 범위가 아니다.
- b-1~b-3, c-1~c-5, d-1~d-3 전체에 대한 최종 완료 Gate는 이 Ticket의 범위가 아니다.
- 테스트 실행, 변이 검사, edge case와 side effect 증명은 이 Ticket의 범위가 아니다.
- LLM 자동 수정, CI 소비, 배포 승인과 제품 기능 코드 수정은 이 Ticket의 범위가 아니다.
- Node/TypeScript 이외 언어는 이 Ticket의 범위가 아니다.

## Blockers

None

## Verification

- 각 확정 규칙의 명확한 통과 및 위반 사례가 빠른 진단에서 올바르게 구분되는지 확인한다.
- 검사기 안전 기본 상한이 적용되고 더 엄격한 저장소 규칙은 강화되지만 느슨한 규칙은 기본 상한을 약화하지 않는지 확인한다.
- 필요한 확정 검사 능력이 없거나 실행되지 않은 경우 성공이 아닌 `INCONCLUSIVE`로 표시되는지 확인한다.
- 빠른 진단 결과가 최종 완료 `PASS`로 소비될 수 없으며 결과에서 제한된 범위가 드러나는지 확인한다.
- 진단 전후 대상 제품 소스가 동일한지 확인한다.

## References

- ../SPEC.md
