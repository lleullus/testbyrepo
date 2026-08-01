# 빈 설정 화면 정보 계층 프로토타입 검토

상태: 실제 렌더링, 독립 검증, cleanup 완료 (비권위)
권위: 없음. 이 문서는 후보 비교와 실제 렌더링을 기록하며 채택된 UI/UX 결정의 권위는 `UX-REFERENCE.md`에만 있다.

## 질문

설정이 비어 있는 화면에서 안내문과 주요 설정 버튼 중 무엇을 먼저 보여줄지, 좁은 화면과 넓은 화면에서 확인한다.

## 비교 후보

- 후보 A: 주요 설정 버튼을 먼저 보여준다.
- 후보 B: 안내문을 먼저 보여준 뒤 단일 주요 설정 버튼을 보여준다.

## Throwaway prototype 정리

- 과거 source: `/home/user01/project/matt/verification/smoke-workspaces/flow-3/prototype-empty-settings-hierarchy/index.html` (삭제됨)
- 독립 Lead 최종 browser 검증 통과 뒤 prototype source, variants, fixed switcher와 빈 경로를 삭제했다. 제품 구현이나 새 framework, package, build tool, image asset, test framework는 만들지 않았다.
- 과거 route와 `/tmp/opencode/matt-gate1-flow3/` screenshot은 진단 실행 기록일 뿐이며, 현재 재실행 대상이나 권위 산출물이 아니다.
- 채택된 B 결정만 `UX-REFERENCE.md`, `SPEC.md`, `TICKET-001.md`에 남는다.

## 독립 Lead 결함 보완

- 독립 Lead는 테스트 사용자 언어가 한국어인데 source의 `<html lang="en">`과 모든 UI copy/label이 영어인 결함을 발견했다.
- source를 `<html lang="ko">`와 한국어 notice, 후보 label, heading, 설명, button, 단계 label로만 최소 수정했다. A/B/C 구조, route, switcher, URL query, keyboard, focus, responsive layout은 변경하지 않았다.

## 실제 비교 결과

- 후보 A (`A - 설정 버튼 우선`): 큰 제목 뒤 action panel에서 `작업 공간 설정`을 먼저 제시하고 그 뒤에 상세 안내를 둔다.
- 후보 B (`B - 안내 우선`): 제목과 설명으로 이루어진 전체 안내 영역을 먼저 제시한 뒤 단일 `설정 열기` 버튼을 둔다.
- 후보 C (`C - 단계 안내`): `01 준비`, `02 설정`, `03 검토` 단계와 `단계별 설정 시작`으로 구성한 단계형 후보다. A/B와 구조적으로 다르며 권위 후보가 아니다.
- `http://127.0.0.1:4173/?variant=A`, `?variant=B`, `?variant=C`를 실제 정적 서버에서 렌더링했다.
- 390x844와 1440x1000에서 각 label, 안내문/버튼 순서, fixed switcher를 확인했다. 여섯 렌더 모두 horizontal/vertical overflow와 주요 action/switcher overlap이 없었다.
- A는 action panel 전체가 상세 안내보다 먼저, B는 heading과 설명으로 이루어진 guidance block 전체가 단일 action보다 먼저, C는 단계 navigation과 단계형 action으로 표시됨을 실제 layout에서 확인했다. B의 paragraph 단독 top 좌표를 action보다 앞이라고 요구하지 않았다.
- 실제 `다음 후보` 버튼 전환은 A에서 B URL과 `B - 안내 우선` label로, 실제 right-arrow keyboard 전환은 B에서 C URL과 `C - 단계 안내` label로 갱신했다. 별도 확인에서 left/right keyboard는 B -> A -> B로 갱신했고 focused switcher button의 outline은 3px이었다.
- 진단용 screenshot은 `/tmp/opencode/matt-gate1-flow3/variant-{A,B,C}-{390x844,1440x1000}.png`에만 저장했다. 저장소 image evidence는 만들지 않았다.

## 사용자 채택

테스트 사용자는 실제 렌더링 관찰 후 후보 B를 명시적으로 채택했다.

## 비채택 및 정리

후보 A와 후보 C는 채택되지 않았으며 Spec 또는 Ticket의 권위 있는 요구사항으로 사용하지 않는다. prototype code는 삭제됐고 후보 B의 채택 결정만 권위 문서에 남는다.
