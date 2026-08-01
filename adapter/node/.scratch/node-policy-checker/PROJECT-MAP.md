# Node/TypeScript 자동 품질 Gate

Status: approved
Owner: user01
Project-Root: /home/user01/project/iis-skills/adapter/node
Initiative-Slug: node-policy-checker

## Product Outcome

코딩 지식이 없는 사용자도 원하는 행동과 보존해야 할 결과만 설명하면, LLM이 성급하게 코드를 쓰지 못하고 Node/TypeScript 변경을 승인된 checklist 전체에 대해 필요한 깊이로 자동 검사, 수정, 재검사하도록 한다.

## Product Boundary

이 이니셔티브는 Node/TypeScript 저장소를 대상으로 변경 전 입장 심사, 작성 후 코드 및 리뷰 품질 판정, 실행 및 변이 기반 테스트 충분성 판정, LLM 자동 수정과 CI 소비 흐름을 제공한다. 사용자가 레이어, SSOT, 에러 경계, mock 경계를 직접 설계하는 것은 요구하지 않으며, 검사기가 변경 전 저장소와 승인된 제품 의도에서 이를 근거 기반으로 추론하고 고정한다. 다른 언어 지원, 제품 코드의 직접 구현, 배포 승인, 근거 없는 의미 추측은 범위 밖이다.

## Reference Interpretation

사용자가 승인한 a-1~a-4, b-1~b-5, c-1~c-5, d-1~d-3, e-1~e-4 checklist가 제품 범위의 기준이다. 기존 Verification Lead 언어 Adapter는 격리와 증거 설계의 참고 자료일 뿐이며, 호환성이나 기능 parity 요구사항은 아니다.

## MVP Cut

- WP-001
- WP-002

비개발 사용자가 행동 의도만 제공하면 LLM이 변경 전 근거를 확보한 뒤에만 코드를 쓸 수 있고, 작성된 코드가 자동 코드 및 리뷰 품질 Gate를 통과해야 완료될 수 있다.

## Work Packages

### WP-001: 자동 변경 입장 심사

Package-Status: ready-for-matt
Matt-Brief: ./matt-briefs/WP-001.md

#### Outcome

비개발 사용자와 LLM 운영자는 수동 아키텍처 설정 없이 변경 전에 기존 실행 경로, 책임 소유자, 재사용 후보와 위험을 근거로 확인하고, 성급한 쓰기를 차단하는 자동 입장 판정을 받을 수 있다.

#### Includes

- a-1의 모듈 및 레이어 경계, a-2의 기계적 의존성 정책, a-3의 SSOT, a-4의 디렉터리 위계를 변경 전 저장소에서 자동 발견하고 근거와 함께 고정한다.
- b-4의 빈 입력, null, 경계값, 동시성, 실패 경로, side effect 테스트 의무를 코드 작성 전에 도출한다.
- b-5의 새 function, helper, type, shape 생성 전에 기존 재사용 후보를 검색하고 생성 필요성을 판정한다.
- 사용자는 기술 구조 대신 원하는 행동, 보존할 행동, 실패 시 관측 결과만 제공한다.
- 필수 근거가 완전할 때만 Write Permit을 발급하고 판단 불가는 `INCONCLUSIVE`로 차단한다.

#### Excludes

- 작성된 코드의 정적 및 AI 의미 품질 판정은 WP-002가 소유한다.
- 테스트 실행, 변이, edge case 및 side effect 증명은 WP-003이 소유한다.
- LLM 수정 반복과 CI 결과 소비 lifecycle은 WP-004가 소유한다.

#### Depends On

None

#### Why This Is One Package

기존 구조 조사, 재사용 탐색, 변경 위험 판정, 테스트 의무 도출은 모두 코드 쓰기 허용 여부라는 하나의 관측 가능한 입장 판정으로 함께 수용된다.

#### Why It Is Separate

코드 작성 전 권한 통제는 작성된 결과의 품질 판정이나 테스트 실효성 판정과 다른 lifecycle과 실패 시점을 가지므로 독립적으로 계획하고 수용할 수 있다.

#### Decisions Reserved For Matt

- 현재 상태 검사와 변경 세션에서 각각 어떤 최소 근거가 입장 판정을 완성하는지 정한다.
- 기술 지식이 없는 사용자에게 보여줄 입장 요약과 필요한 행동 질문의 범위를 정한다.
- 자동 허용, 차단, 판단 불가의 사용자 관측 의미와 다시 시도하는 조건을 정한다.

### WP-002: 자동 코드 및 리뷰 품질 판정

Package-Status: ready-for-matt
Matt-Brief: ./matt-briefs/WP-002.md

#### Outcome

LLM이 작성한 Node/TypeScript 변경은 WP-001에서 고정한 근거와 정책에 대해 코드 및 리뷰 품질을 자동 판정받고, 모든 요청 검사를 통과하기 전에는 완료로 취급되지 않는다.

#### Includes

- b-1의 에러 삼킴과 무의미한 fallback, b-2의 과한 중첩, b-3의 함수 및 파일 크기 상한을 판정한다.
- c-1의 중복, 대체 누락, 죽은 코드, c-2의 조용한 에러 삼킴, c-3의 숨은 결합과 암묵 계약, c-4의 re-export, c-5의 fan-in 및 fan-out 집중을 판정한다.
- d-1의 strict 타입, 금지된 type assertion과 JavaScript JSDoc 의무, d-2의 순환 의존성과 경계 위반, d-3의 complexity, depth, 함수 크기 제한을 강제한다.
- 확정 가능한 항목은 기계 판정하고 의도와 의미가 필요한 항목은 근거가 연결된 AI 판정을 사용한다.
- 요청된 검사 하나라도 실행 또는 판정하지 못하면 `INCONCLUSIVE`로 실패하며, 변경된 코드로 정책을 다시 만들어 위반을 합법화하지 못한다.

#### Excludes

- 변경 전 Write Permit과 정책 고정은 WP-001이 소유한다.
- 테스트가 행동, edge case, 실패와 side effect를 실제로 검출하는지에 대한 실행 증명은 WP-003이 소유한다.
- 실패 결과를 소비해 LLM이 수정하고 CI가 최종 결과를 확인하는 lifecycle은 WP-004가 소유한다.

#### Depends On

- WP-001

#### Why This Is One Package

작성 후 source와 diff에 대한 정적 판정 및 AI 의미 판정은 하나의 품질 verdict와 동일한 완료 Gate로 사용자에게 관측된다.

#### Why It Is Separate

테스트 실행과 변이는 비용, 환경, 증거 의미가 다르고 별도로 확장하거나 보류할 수 있으며, LLM 운영 lifecycle도 판정 규칙 자체와 독립적으로 수용할 수 있다.

#### Decisions Reserved For Matt

- 사용자가 선택할 검사 깊이별 의무와 각 깊이에서 허용되지 않는 미검사 상태를 정한다.
- 기존 저장소의 선행 위반과 이번 변경에서 생긴 위반을 사용자에게 어떻게 구분하고 차단할지 정한다.
- AI 의미 판정의 근거 표시, 반증 가능성, 판정 충돌을 사용자에게 어떻게 보여줄지 정한다.

### WP-003: 실행 및 변이 기반 행동 증명

Package-Status: ready-for-matt
Matt-Brief: ./matt-briefs/WP-003.md

#### Outcome

사용자와 LLM은 변경된 행동, edge case, 실패 경로와 side effect가 테스트로 실제 검출되며 내부 구현 mock이나 테스트용 방어 코드가 품질을 가장하지 않는다는 자동 증명을 받을 수 있다.

#### Includes

- e-1의 문자열 또는 커버리지 수치가 아닌 관측 가능한 출력 행동 검증 여부를 실행 및 변이 결과로 판정한다.
- e-2의 mock이 자동 추론된 외부 경계에서만 사용되는지 판정하고 내부 구현 세부 mock을 차단한다.
- e-3의 빈 입력, 경계값, null, 실패 경로와 관련 edge case를 도출하고 테스트로 고정되었는지 실행 확인한다.
- e-4의 테스트 통과만을 위해 production code에 방어 코드가 추가되었는지 변경분, 실행 결과, 변이 생존 여부를 함께 판정한다.
- 테스트 실행 능력이나 필수 행동 증거가 부족하면 성공 대신 `INCONCLUSIVE`로 실패한다.

#### Excludes

- 변경 전 구조 및 테스트 의무 도출은 WP-001이 소유한다.
- source 및 diff의 코드와 리뷰 품질 판정은 WP-002가 소유한다.
- 검사 선택, 자동 수정 반복, CI 최종 소비 lifecycle은 WP-004가 소유한다.

#### Depends On

- WP-002

#### Why This Is One Package

행동 테스트, edge case, mock 경계, side effect, 변이 생존 판정은 모두 테스트가 실제 결함을 잡는지라는 하나의 실행 증명 결과로 함께 수용된다.

#### Why It Is Separate

실제 명령 실행과 변이 검사는 정적 및 의미 판정보다 비용과 환경 실패 정책이 다르며, 코드 품질 Gate와 별도로 출시하거나 검사 깊이를 확장할 수 있다.

#### Decisions Reserved For Matt

- 기본 검사와 심층 검사에서 요구할 실행, 변이, edge case 증명의 범위를 정한다.
- 생성된 일회성 probe와 저장소에 남는 회귀 테스트가 각각 어떤 완료 증거가 되는지 정한다.
- 테스트를 실행할 수 없거나 변이가 적용되지 않는 프로젝트에서 사용자에게 제공할 실패 및 재시도 경험을 정한다.

### WP-004: LLM 자동 운영 및 수정 Loop

Package-Status: ready-for-matt
Matt-Brief: ./matt-briefs/WP-004.md

#### Outcome

LLM은 입장 심사부터 코드 품질 판정과 행동 증명까지 빠뜨리지 않고 실행하며, 고정된 정책 아래 실패를 자동 수정하고 재검사하여 CI가 신뢰할 수 있는 최종 결과를 남긴다.

#### Includes

- LLM이 WP-001의 입장 심사, WP-002의 코드 및 리뷰 판정, WP-003의 행동 증명을 선택된 검사 깊이에 맞춰 자동 호출한다.
- 수정 반복 동안 최초 정책, baseline, Write Permit과 검사 의무를 유지하고 재생성으로 실패를 회피하지 못하게 한다.
- `FAIL`과 `INCONCLUSIVE`의 근거를 LLM 수정 입력으로 제공하고 동일한 의무에 대해 재검사한다.
- 무한 수정, 동일 실패 반복, 환경 미충족에 대한 종료 결과를 사용자에게 명확히 제공한다.
- CI는 정확한 source와 고정 정책에 묶인 최종 `PASS`만 성공으로 소비하고, 사용자는 비기술적 최종 요약을 받는다.

#### Excludes

- 개별 설계, 코드, 리뷰 및 테스트 검사 규칙의 제품 의미는 WP-001, WP-002, WP-003이 각각 소유한다.
- LLM이 수행할 실제 제품 기능 구현과 배포는 이 이니셔티브의 범위 밖이다.
- Node/TypeScript 이외 언어의 자동 운영은 후속 이니셔티브다.

#### Depends On

- WP-003

#### Why This Is One Package

검사 호출, 실패 전달, 수정 반복, 종료, CI 소비는 사용자가 수동 개입 없이 하나의 품질 확인 lifecycle을 끝내는 단일 운영 결과다.

#### Why It Is Separate

자동 운영은 이미 존재하는 판정 결과를 누가 언제 반복하고 소비하는지에 관한 별도 lifecycle이며, 개별 검사 제품 계약을 바꾸지 않고 독립적으로 계획할 수 있다.

#### Decisions Reserved For Matt

- 사용자가 요청할 수 있는 검사 깊이와 자동 수정 반복의 기본 및 최대 범위를 정한다.
- 동일 실패, 새로운 실패, 환경 실패, 정책 충돌에서 각각 언제 중단하고 무엇을 사용자에게 보여줄지 정한다.
- CI와 대화형 LLM 사용에서 최종 결과의 신선도와 재사용 가능성을 어떻게 경험하게 할지 정한다.

## Dependency Map

- WP-001: None
- WP-002: WP-001
- WP-003: WP-002
- WP-004: WP-003

## Deferred Capabilities

- Python, Go와 그 밖의 언어에 대한 동일 품질 Gate 확장
- 자연어 설계서와 작업 지시문 자체의 독립적인 품질 판정
- 검사기가 제품 코드를 직접 구현하거나 배포를 승인하는 기능

## Initiative-Level Open Questions

None

## Matt Handoff Queue

- ./matt-briefs/WP-001.md
- ./matt-briefs/WP-002.md
- ./matt-briefs/WP-003.md
- ./matt-briefs/WP-004.md
