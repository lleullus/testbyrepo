# IIS Model Selection Guide — 2026-09-09

이 문서는 현재 IIS 역할별 모델·effort 선택을 위한 운영 가이드다.

역할 정합성 교정: 2026-09-13. 기존 모델·effort 및 수치 자료는 재평가·재산정하지 않았다.

단순 벤치마크 1위 모델을 모든 역할에 배치하지 않는다. **현재 IIS의 책임 분리, 작업 난이도, failure cost, 모델군별 실패 패턴, 비용을 함께 보고 최소 충분 모델을 고르는 것**이 목적이다.

---

## 1. 현재 역할 구조

실행 준비의 책임은 [scope-plan](companion-skills/scope-plan/SKILL.md)을 따른다. 아래는 모델 수나 추가 invocation을 정하는 고정 roster가 아니다. Main은 현재 요청의 owner이며, 사용자가 지정한 model/effort/mode가 이 가이드의 추천보다 우선한다.

```text
Main request owner
  -> Preparation Lead
  -> Grounded Planner
  -> Independent Plan Reviewer
  -> Lead fan-in
  -> Implementation Worker (구현이 허용된 경우)
  -> Final Verifier (검증이 허용된 경우)
  -> Coverage (정상 검증 후 caller가 요청한 경우)
```

역할 의미는 다음과 같다.

| 역할 | 현재 책임 |
|---|---|
| **Main** | 현재 요청의 범위·routing·전체 완료 판단을 소유한다. |
| **Preparation Lead / Lead fan-in** | Scope와 역할을 조율하고 독립 Plan Review의 귀속·currentness·완료 범위를 확인한다. fan-in은 방법 작성이나 재판정이 아니다. |
| **Grounded Planner** | 원계약·현재 근거에서 실행 방법을 작성하고 material method revision을 소유한다. |
| **Independent Plan Reviewer** | 원계약·현재 primary evidence와 bounded counterpath를 직접 확인해 exact `start_scope`의 `ADMIT / REVISE / EVIDENCE_NEEDED`를 판정한다. |
| **Adversarial Challenger** | 현재 IIS의 명시적 opt-in이 활성화된 경우에만 candidate의 전제·누락·counterexample·trade-off를 read-only로 공격한다. 실행 준비의 필수 중간 단계가 아니다. |
| **Implementation Worker** | 이미 review된 방법을 bounded하게 실행하고 self-check/readback을 닫는다. 중요한 방법 변경은 스스로 재설계하지 않고 upstream으로 반환한다. |
| **Final Verifier** | 구현 후 fresh evidence, Acceptance adjudication과 semantic verdict를 소유한다. 성공 후 독립 읽기전용 Coverage, 귀속·currentness 확인 및 일반 파일 도구를 통한 Scope 완료 기록은 Main이 기존 계약에 따라 맡는다. |

Writer와 Reviewer의 invocation은 분리한다. 하나의 사용자 선택이 두 역할을 포괄할 수 있으며 Lead fan-in은 새 모델 선택 행을 만들지 않는다.

### 가장 중요한 구조 변화

Implementation Worker는 더 이상 broad diagnosis·architecture·root-cause 탐색의 주 소유자가 아니다.

다음이 material하게 바뀌면 구현 모델을 올려서 해결하지 않는다.

- cause
- owner
- interface
- persistence
- external effect
- authoritative readback

이 경우:

```text
Implementation의 material method change
  -> affected Plan revision (Planner)
  -> current independent review
  -> 해당 Scope의 current ADMIT
  -> fresh implementation actor
```

을 따른다. 이전 worker/process가 실제로 종료된 뒤에만 새 구현자를 시작하며, 제품 의미 변경은 원래 planning authority로 반환한다.

---
## 2. 후보 모델

현재 운영 후보는 13개 구성이다.

- Astra: Medium / High / XHigh / Max
- Sol: Medium / High / XHigh / Max
- Terra: XHigh / Max
- Luna: XHigh / Max
- Gemini 3.8 Flash: High

### 고정 운영 제약

- 사용자 지정 model/effort/mode는 이 문서의 추천보다 우선하며, 추천 자체는 consent가 아니다.
- Challenger는 optional이며 adversarial consensus가 명시적으로 활성화된 경우에만 적용한다.
- Implementation은 **Luna Max를 기본값**으로 본다. 모델 상향은 예외 조건으로만 한다.
- Astra Max는 일반 preset에 자동 포함하지 않는다.

---
## 3. 벤치마크 해석

이번 가이드는 Artificial Analysis v4.3 세대 공개 데이터를 기준으로 한다.

### Core score에 사용하는 지표

13개 후보의 effort별 데이터를 같은 조건으로 비교할 수 있는 지표만 본점수에 사용한다.

| 지표 | 이 가이드에서의 의미 |
|---|---|
| **AutomationBench-AA** | guardrail을 지키며 정해진 목표 상태를 만드는 agent execution 능력 |
| **Terminal-Bench v4.0** | 매우 어려운 terminal task에서 long-horizon closure를 끝까지 해내는 hard-tail 능력 |
| **SciCode** | effort별로 비교 가능한 coding-oriented capability proxy |
| **AA-Omniscience** | 사실 정확성·불확실성 대응의 보조 proxy |
| **AA-Briefcase Elo** | 근거 통합·분석·rubric fulfillment의 보조 proxy |
| **AA-LCR** | 긴 문맥에서 요구와 정보를 유지·종합하는 보조 proxy |

### 정규화

Omniscience는 원래 `-100 ~ +100`이므로 다른 0~100형 지표와 직접 더하지 않는다.

```text
Omniscience normalized = (Omniscience + 100) / 2
```

Briefcase는 현재 공개 Elo를 AA index 방식으로 정규화한다.

```text
Briefcase normalized = (Elo - 500) / 20
```

### Terminal-Bench v4.0 주의

Terminal v4는 일상적 구현의 평균 난이도를 대표하는 benchmark로 취급하지 않는다.

- frontier 모델 구별력을 위해 hard-tail을 강하게 포함한다.
- strict final verification 때문에 추가 search/retry/repair budget이 크게 보상될 수 있다.
- `max` effort가 유리하게 보이는 workload 특성이 있다.
- 따라서 routine Implementation에서 높은 비중으로 사용하면 Max/hard-debugging 모델을 과대평가할 수 있다.

기존 산정에서 Terminal v4 비중은 다음과 같다.

- Planner / Challenger / Plan Reviewer: **0%**
- Implementation / Final Verifier: **10%**

---
## 4. 역할별 benchmark 조합

아래 가중치와 §7 점수는 **2026-09-09 산정값**이다. `Plan Reviewer` 수치는 종전 Plan Verifier 산정을 보존했을 뿐, 현행 직접 조사·판정 능력을 검증한 값은 아니다.

| 역할 | Automation | Terminal v4 | SciCode | Omni norm | Briefcase norm | LCR |
|---|---:|---:|---:|---:|---:|---:|
| **Planner** | 15% | 0% | 15% | 15% | **35%** | 20% |
| **Adversarial Challenger** | 0% | 0% | 15% | 20% | **40%** | 25% |
| **Plan Reviewer** | 10% | 0% | 15% | 20% | **35%** | 20% |
| **Implementation Worker** | **25%** | **10%** | **50%** | 0% | 0% | 15% |
| **Final Verifier** | 10% | **10%** | 20% | 20% | **30%** | 10% |

### 4.1 Grounded Planner

중심 능력:

- Planner: 현재 product/code 구조 이해, 근거와 contract 통합
- Planner: owner/interface/effect/readback 방법 작성과 material revision
- long context에서 해당 책임과 원권위 유지

Terminal hard-tail 완주 능력은 직접적인 주 평가 대상이 아니다.

### 4.2 Adversarial Challenger

중심 능력:

- counterexample
- unsupported assumption 공격
- purpose failure 식별
- 장문 candidate/authority 비교
- material objection과 non-material objection 구별

실행 성능보다 reasoning·evidence integration을 더 크게 본다.

### 4.3 Independent Plan Reviewer

중심 능력:

- 원래 Thesis/Scope와 현재 product path·primary evidence 직접 확인
- Planner diagnosis에 종속되지 않은 load-bearing dependency와 bounded counterpath 판단
- 확인된 모순·미확인 근거·제안된 방법을 구별하여 false ADMIT과 불필요한 거절 억제
- exact start scope와 conditional first work의 관측·의존 작업 제한·반환 경계 판단

Plan 작성·수정이나 최종 제품 판정은 담당하지 않는다.

### 4.4 Implementation Worker

중심 능력:

- 이미 ADMIT된 방법의 정확한 실행
- code change
- 목표 상태 생성
- guardrail 준수
- tests/runtime/readback
- Scope/Plan의 긴 문맥 유지

---
현재 basket:

```text
50% SciCode
25% AutomationBench-AA
15% LCR
10% Terminal v4
```

Implementation의 default는 **Luna Max**다.

### 4.5 Final Verifier

중심 능력:

- semantic preflight
- nearest nonconforming state
- discriminating observation
- sensitivity activation
- fresh attributable evidence
- `SATISFIED / CONTRADICTED / INCONCLUSIVE`
- false PASS 억제

Verifier가 어려운 구현을 대신 해결하는 역할은 아니므로 Terminal은 10%만 반영한다.

---


## 5. 보조 coding benchmark

다음 지표는 역할 적합성이 높지만 현재 13개 effort 전체를 동일 조건으로 채우지 못하므로 본점수에 추정 삽입하지 않는다.

| 지표 | 주 용도 | 현재 처리 |
|---|---|---|
| **SWE-Bench Pro** | 실제 repository implementation | family-level sanity check |
| **DeepSWE** | coding-agent implementation | effort coverage가 있는 모델만 overlay |
| **SWE-Atlas Codebase QnA** | repo 이해·경로·원인 조사 | Planner/Plan Reviewer/Final Verifier overlay |
| **SWE-Atlas Test Writing** | 정상/비정상 구현을 구별하는 검증 설계 | Final Verifier overlay |

현재 공개 SWE-Bench Pro family-level 참고값:

| Family | SWE-Bench Pro |
|---|---:|
| Sol | 64.6% |
| Terra | 63.4% |
| Luna | 62.7% |
| Gemini 3.8 Flash | 61.6% |

이 결과는 일반 repository coding에서 family 간 기본 capability가 크게 상향평준화되어 있음을 시사한다.

Terminal v4의 큰 격차는 이를 routine coding 우위로 직접 해석하지 않고 **hard-tail robustness**로 해석한다.

Astra Medium/High/XHigh의 동일 조건 modern coding suite 행이나 전체 후보의 Test Writing 행이 확보되기 전까지 빈 값을 다른 effort/family 점수로 복제하지 않는다.

---

## 6. 비용 정책

Luna Max를 역할 성능 100, 비용 1로 둔다.

```text
P = Luna Max=100으로 정규화한 역할 성능지수
C = adjusted task cost / Luna Max task cost
V = P / C
F = 0.8 * P + 0.2 * V
```

즉 **성능 80% + 가성비 20%**다.

`P >= 100`은 상대 비교 필터일 뿐 IIS 역할 sufficiency 합격선이 아니다.

### Sol 가격

Sol은 현재 프로모션 가격을 사용하지 않는다.

비할인 list-price 기준을 반영한다.

- input: $5
- cached input: $0.50
- output: $30

AA task cost와 output token 정보가 공개 화면에서 반올림되어 있으므로 Sol task cost는 근사 복원값이다.

### 비용계수

| 구성 | Luna Max 대비 C |
|---|---:|
| Luna XHigh | 0.50× |
| **Luna Max** | **1.00×** |
| Terra XHigh | 3.50× |
| Sol Medium | 3.69× |
| Sol High | 5.99× |
| Gemini 3.8 Flash High | 6.89× |
| Terra Max | 7.78× |
| Astra Medium | 8.56× |
| Sol XHigh | 8.75× |
| Astra High | 9.56× |
| Astra XHigh | 12.83× |
| Sol Max | 14.63× |
| Astra Max | 18.11× |

비용계수는 실제 Scope end-to-end 비용이 아니다.

포함되지 않는 것:

- retry
- review round 수
- 잘못된 완료 선언 후 재작업
- 외부 서비스 비용
- 사람 검토
- adversarial consensus 활성 여부

---

## 7. 비용 20% 반영 Top 8

이 표는 참고용이다. **운영 기본 선택은 아래 난이도 프리셋을 우선한다.**

### 7.1 Planner

| 순위 | 구성 | P | C | F20 |
|---:|---|---:|---:|---:|
| 1 | **Luna Max** | 100.00 | 1.00× | **100.00** |
| 2 | Astra Max | 119.09 | 18.11× | 96.59 |
| 3 | Astra XHigh | 117.53 | 12.83× | 95.86 |
| 4 | Astra High | 116.09 | 9.56× | 95.30 |
| 5 | Astra Medium | 113.58 | 8.56× | 93.52 |
| 6 | Sol Max | 112.50 | 14.63× | 91.54 |
| 7 | Sol XHigh | 108.93 | 8.75× | 89.63 |
| 8 | Sol High | 106.66 | 5.99× | 88.89 |


### 7.2 Adversarial Challenger

| 순위 | 구성 | P | C | F20 |
|---:|---|---:|---:|---:|
| 1 | **Luna Max** | 100.00 | 1.00× | **100.00** |
| 2 | Astra Max | 116.96 | 18.11× | 94.86 |
| 3 | Astra XHigh | 115.49 | 12.83× | 94.19 |
| 4 | Astra High | 113.94 | 9.56× | 93.54 |
| 5 | Astra Medium | 111.73 | 8.56× | 92.00 |
| 6 | Sol Max | 111.61 | 14.63× | 90.81 |
| 7 | Sol XHigh | 109.06 | 8.75× | 89.74 |
| 8 | Sol High | 106.45 | 5.99× | 88.72 |

운영 preset에서는 model-family independence와 latency를 위해 Gemini High를 Challenger 기본값으로 사용한다.

### 7.3 Plan Reviewer — 기존 산정값

| 순위 | 구성 | P | C | F20 |
|---:|---|---:|---:|---:|
| 1 | **Luna Max** | 100.00 | 1.00× | **100.00** |
| 2 | Astra Max | 119.97 | 18.11× | 97.30 |
| 3 | Astra XHigh | 118.50 | 12.83× | 96.65 |
| 4 | Astra High | 117.10 | 9.56× | 96.13 |
| 5 | Astra Medium | 114.67 | 8.56× | 94.42 |
| 6 | Sol Max | 113.12 | 14.63× | 92.04 |
| 7 | Sol XHigh | 109.95 | 8.75× | 90.47 |
| 8 | Sol High | 107.62 | 5.99× | 89.69 |

### 7.4 Implementation Worker

| 순위 | 구성 | P | C | F20 |
|---:|---|---:|---:|---:|
| 1 | **Luna Max** | 100.00 | 1.00× | **100.00** |
| 2 | Astra XHigh | 117.73 | 12.83× | 96.02 |
| 3 | Astra Max | 118.29 | 18.11× | 95.94 |
| 4 | Astra High | 115.67 | 9.56× | 94.95 |
| 5 | Astra Medium | 112.85 | 8.56× | 92.92 |
| 6 | Sol Max | 112.76 | 14.63× | 91.75 |
| 7 | Terra Max | 109.66 | 7.78× | 90.55 |
| 8 | Gemini 3.8 Flash High | 108.16 | 6.89× | 89.67 |

**운영 기본값은 Luna Max다.**

### 7.5 Final Verifier

| 순위 | 구성 | P | C | F20 |
|---:|---|---:|---:|---:|
| 1 | **Astra Max** | 132.45 | 18.11× | **107.42** |
| 2 | Astra XHigh | 131.34 | 12.83× | 107.12 |
| 3 | Astra High | 128.57 | 9.56× | 105.55 |
| 4 | Astra Medium | 124.86 | 8.56× | 102.81 |
| 5 | Luna Max | 100.00 | 1.00× | 100.00 |
| 6 | Sol Max | 120.52 | 14.63× | 98.06 |
| 7 | Sol XHigh | 114.35 | 8.75× | 94.09 |
| 8 | Sol High | 111.34 | 5.99× | 92.80 |

Astra Max와 XHigh의 차이는 매우 작으므로 Max를 자동 기본값으로 사용하지 않는다.

---

## 8. 난이도별 운영 프리셋

단순 Top 8 순위보다 이 표를 우선한다. 기존 공통 행의 모델·effort는 Planner 추천으로 보존한다. 현재 세션과 사용자 선택은 바꾸지 않으며, 실제 선택은 현재 IIS request contract와 각 role contract를 따른다.

### P0 — Lean / Routine

작고 strongly bounded하며 deterministic readback이고 실패 후 재실행·복구가 쉬운 작업.

| 역할 | 모델 |
|---|---|
| Planner | **Luna Max** |
| Challenger* | Gemini 3.8 Flash High |
| Plan Reviewer | Gemini 3.8 Flash High |
| Implementation | **Luna Max** |
| Final Verifier | Gemini 3.8 Flash High |

특징:

- Astra 없이 시작한다.
- 구현과 Planner는 Luna.
- reasoning/verification은 Gemini.

### P1 — Non-Astra Standard

일반적인 기본 non-Astra 운영형.

| 역할 | 모델 |
|---|---|
| Planner | **Sol High** |
| Challenger* | Gemini 3.8 Flash High |
| Plan Reviewer | Gemini 3.8 Flash High |
| Implementation | **Luna Max** |
| Final Verifier | Gemini 3.8 Flash High |

사용 조건:

- 여러 파일 또는 한두 runtime surface
- planning ambiguity는 크지 않음
- Luna-only보다 조사/판정 여유가 필요
- Astra premium까지는 필요 없음

### P2 — Hybrid Value

planning/verification의 failure cost가 의미 있게 커지는 중상 난이도.

| 역할 | 모델 |
|---|---|
| Planner | **Astra Medium** |
| Challenger* | Gemini 3.8 Flash High |
| Plan Reviewer | Astra Medium |
| Implementation | **Luna Max** |
| Final Verifier | Astra High |

특징:

- Astra는 실행 방법 준비와 검증에 먼저 투입한다.
- Implementation은 여전히 Luna Max다.

### P3 — High Reliability

multi-service/state, 중요한 persistence/readback, false ADMIT/PASS 비용이 높은 작업.

| 역할 | 모델 |
|---|---|
| Planner | **Astra High** |
| Challenger* | Gemini 3.8 Flash High |
| Plan Reviewer | Astra High |
| Implementation | **Luna Max** |
| Final Verifier | Astra XHigh |

특징:

- 계획·착수 검증·최종 검증을 premium으로 올린다.
- Challenger는 Gemini를 유지해 Astra monoculture를 줄인다.
- Implementation은 plan이 current한 한 Luna Max를 유지한다.

### P4 — Critical / Astra-heavy

cross-authority, shared/external effect, 복구가 어렵고 false completion 허용도가 매우 낮은 작업.

| 역할 | 모델 |
|---|---|
| Planner | **Astra XHigh** |
| Challenger* | Gemini 3.8 Flash High |
| Plan Reviewer | Astra XHigh |
| Implementation | **Astra Medium** |
| Final Verifier | Astra XHigh |

특징:

- Astra-dominant ceiling.
- Implementation까지 XHigh로 올리지 않는다.
- XHigh compute는 Plan/Plan Review/final verification에 우선 사용한다.

`* Challenger`는 adversarial consensus가 활성화된 경우에만 존재한다.

---

## 9. 역할별 escalation ladder

| 역할 | 기본 escalation |
|---|---|
| **Planner** | `Luna Max -> Sol High -> Astra Medium -> Astra High -> Astra XHigh` |
| **Challenger** | `Gemini 3.8 Flash High` 유지가 기본 |
| **Plan Reviewer** | `Gemini High -> Astra Medium -> Astra High -> Astra XHigh` |
| **Implementation** | **`Luna Max` 기본 고정**; 예외만 `Terra Max` 또는 `Astra Medium` |
| **Final Verifier** | `Gemini High -> Astra High -> Astra XHigh` |

### Implementation escalation은 특별 취급

#### Execution-heavy override -> Terra Max

다음이 모두 성립할 때 고려한다.

- Plan은 current하고 ADMIT도 유효함
- product meaning / owner / interface ambiguity 없음
- 실제 terminal/runtime execution 자체가 길고 까다로움
- Luna가 plan을 오해한 것이 아니라 bounded execution을 반복적으로 못 닫음

이 경우:

```text
Luna Max -> Terra Max
```

Terra Max는 일반 plan/verifier 후보가 아니라 execution specialist override다.

#### High-consequence implementation -> Astra Medium

다음에 사용한다.

- 구현 실수 blast radius가 큼
- rollback/rework 비용이 큼
- 실행 자체의 reliability를 높일 가치가 큼

```text
Luna Max -> Astra Medium
```

#### Plan drift -> Implementation 상향 금지

다음은 model escalation 문제가 아니다.

- cause 변경
- owner 변경
- interface 변경
- persistence 변경
- effect 경계 변경
- readback 변경

이 경우 반드시 upstream으로 반환한다.

---

## 10. 모델군별 현재 포지션

### Luna Max

**기본 bounded executor.**

주 용도:

- routine Implementation
- Lean Planner
- deterministic하고 실패 복구 쉬운 작업

일반 coding capability가 상향평준화된 현재 세대에서는 낮은 비용이 매우 큰 장점이다.

### Gemini 3.8 Flash High

**빠른 independent reasoning / verification mid-tier.**

주 용도:

- Challenger
- low/mid Plan Reviewer
- low/mid Final Verifier

제약:

사용자 지정 model/effort/mode는 이 추천보다 우선한다.

### Sol High

**non-Astra balanced entry.**

주 용도:

- P1 Planner
- 저중난도 independent execution/reasoning

### Terra Max

**execution-heavy Implementation override.**

특징:

- Terminal v4에서 XHigh 대비 큰 Max cliff
- 일반 planning/reasoning proxy는 약함
- 이미 plan이 닫힌 bounded runtime execution에서만 강점을 사용

Terra XHigh는 현재 roster에서 우선순위가 낮다.

### Astra Medium

**value premium planning/verification + high-consequence implementation.**

- P2 Planner/Plan Review
- Implementation reliability override

### Astra High

**default premium planner/verifier.**

- P3 Planner/Plan Review
- P2 Final Verify
- failure cost가 높은 reasoning/authority 작업

### Astra XHigh

**critical reasoning / verification ceiling.**

- cross-authority
- ambiguity
- false completion 비용이 큼
- P4 core

### Astra Max

**special override only.**

일반 preset에는 넣지 않는다.

사용 근거가 필요한 경우:

- Automation-heavy workload에서 직접적인 추가 이득이 확인됨
- XHigh 실패 후 더 큰 search budget이 실제로 도움이 될 합리적 근거가 있음

`Max`라는 이름만으로 자동 선택하지 않는다.

---

## 11. 빠른 선택표

| 상황 | 선택 |
|---|---|
| 일반 기본 운영 | **P1 Non-Astra Standard** |
| 매우 작고 bounded | P0 Lean |
| planning/verification 신뢰도가 중요해짐 | P2 Hybrid Value |
| multi-service/state + 높은 재작업 비용 | P3 High Reliability |
| false completion 허용도 매우 낮음 | P4 Critical |
| 일반 Implementation | **Luna Max** |
| 실행만 유난히 까다로운 Implementation | Terra Max override |
| high-consequence Implementation | Astra Medium override |
| critical verification | Astra XHigh |

---

## 12. 점수 해석 금지사항

다음처럼 해석하지 않는다.

1. `P >= 100` -> IIS 역할을 충분히 수행한다.
2. F20 1위 -> 무조건 기본 모델이다.
3. Luna가 F20 1위 -> raw capability도 가장 높다.
4. Terminal v4 점수 차이 -> 일상 coding 성공률 차이.
5. Terra Max Terminal v4 jump -> Terra가 일반적으로 Sol보다 좋은 reasoning 모델이다.
6. Max -> 같은 family에서 항상 더 좋은 quality tier.
7. Omniscience -> 실제 IIS false-PASS율.
8. Briefcase -> 실제 Plan Reviewer 정확도.
9. 비용계수 -> 실제 end-to-end Scope 비용.
10. SWE-Pro family score -> 모든 effort의 SWE-Pro 점수.

---

## 13. 향후 IIS 실측이 우선할 지표

공개 benchmark보다 IIS 자체 로그가 충분히 쌓이면 다음을 우선한다.

### Planner

- plan review에서 발견된 material method defect
- implementation material-turn으로 되돌아온 계획 오류율
- 불필요한 complexity / overplanning 비율

### Challenger

- material objection recall
- non-material objection rate
- 실제 candidate 수정으로 이어진 objection 비율

### Plan Reviewer

- false ADMIT
- false REVISE
- EVIDENCE_NEEDED 적정성
- 준비 시점에 판단할 수 있었는데 구현 착수 후 드러난 계획 결함률

### Implementation

- first-pass `Completion: COMPLETE`
- plan drift가 아닌 순수 implementation defect율
- runtime/readback 누락률
- 재작업 횟수
- verified Scope당 실제 총비용

### Final Verifier

- false PASS
- false FAIL
- INCONCLUSIVE 적정성
- authored Flow 누락률
- stale/unattributable evidence 사용률
- verifier가 발견한 material post-implementation counterpath 비율

실측이 충분해지면 공개 benchmark 가중치는 보조 자료로 낮추고 IIS 자체 데이터를 주 평가 기준으로 전환한다.

---

## 14. 역할별 참고 구성

```text
Luna Max                 : default Implementation / lean execution
Gemini 3.8 Flash High    : Challenger / low-mid verification
Sol High                 : non-Astra Planner
Terra Max                : execution-heavy Implementation override
Astra Medium             : value premium planning/verification
Astra High               : default premium planning/verification
Astra XHigh              : critical ceiling
```

선택적:

```text
Astra Max                : Automation-heavy / special search-budget escalation
```

Terra XHigh, Sol Medium, Luna XHigh는 비용·역할 중복을 고려하면 기본 roster에서 우선순위가 낮다.

---

## 15. 데이터 갱신 원칙

가이드를 다음에 재계산할 때는:

1. 같은 세대의 benchmark 결과로 통일한다.
2. effort별 실제 공개값만 사용한다.
3. family-level SWE-Pro 값을 effort별로 복제하지 않는다.
4. missing Coding Agent / QnA / Test Writing 값을 추정으로 채우지 않는다.
5. Terminal v4는 hard-tail 지표로 해석한다.
6. Sol은 비할인 list price 기준을 유지한다.
7. 비용 정책은 `80% capability + 20% value`를 기본으로 한다.
8. 역할 topology가 바뀌면 benchmark weight보다 역할 정의를 먼저 갱신한다.

### 현재 주요 공개 source

- Artificial Analysis Intelligence Index v4.3: `https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3`
- AutomationBench-AA: `https://artificialanalysis.ai/evaluations/automationbench-aa`
- Terminal-Bench v4.0: `https://artificialanalysis.ai/evaluations/terminalbench-v4-0`
- Artificial Analysis Coding Agent Index: `https://artificialanalysis.ai/agents/coding-agents`
- Scale SWE Atlas QnA: `https://labs.scale.com/leaderboard/sweatlas-qna`
- Scale SWE Atlas Test Writing: `https://labs.scale.com/leaderboard/sweatlas-tw`
- OpenAI GPT-5.6 launch / family coding results: `https://openai.com/index/gpt-5-6/`

이 문서의 leaderboard는 **설명 자료**이고, 실제 모델 선택은 난이도 preset과 역할별 escalation rule을 우선한다.
