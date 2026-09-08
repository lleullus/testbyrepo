# IIS Model Selection Guide — v4.3

작성 기준: 2026-09-08  
계산 원본: `/tmp/IIS_v43_13Model_Top8.xlsx`

이 문서는 IIS 역할별 모델·effort 선택을 위한 운영 가이드다. 단순 벤치마크 순위표가 아니라, **어떤 역할에서 어떤 모델을 기본값으로 쓰고 언제 상향·하향할지**를 결정하는 용도로 사용한다.

---

## 1. 평가 기준

Artificial Analysis v4.3 세대 데이터로 통일했다.

- `τ³-Banking` 대신 **AutomationBench-AA**
- `Terminal-Bench v2.1` 대신 **Terminal-Bench v4.0**
- **AA-Omniscience**
- **AA-Briefcase rubric pass rate**
- **AA-LCR v1.1**
- 현재 AA v4.3 **cost per Intelligence Index task**

후보는 다음 13개 구성이다.

- Astra: Medium / High / XHigh / Max
- Sol: Medium / High / XHigh / Max
- Terra: XHigh / Max
- Luna: XHigh / Max
- Gemini 3.8 Flash: High

### 역할별 성능 바스켓

| 역할 | Automation | Terminal v4 | Omniscience | Briefcase rubric | LCR |
|---|---:|---:|---:|---:|---:|
| Outer Main | 40% | 0% | 20% | 30% | 10% |
| Challenger | 25% | 10% | 25% | 40% | 0% |
| Implementation | 20% | 60% | 10% | 10% | 0% |
| Heuristic Prober | 30% | 60% | 10% | 0% | 0% |
| Verifier | 30% | 30% | 35% | 0% | 5% |

### 최종 점수

Luna Max를 역할 성능 100, 비용 1로 둔다.

```text
P = Luna Max=100으로 정규화한 역할 성능지수
C = 해당 구성 AA v4.3 task cost / Luna Max task cost
V = P / C
Final = 0.8 * P + 0.2 * V
```

`P >= 100` 필터는 **상대 비교용 필터일 뿐, 실제 IIS skill sufficiency 합격선이 아니다.** Luna Max가 100인 것은 기준점이기 때문이지, 모든 IIS 역할에 충분하다는 증거가 아니다.

---

## 2. 비용계수

| 구성 | Luna Max 대비 비용계수 |
|---|---:|
| Luna XHigh | 0.48× |
| Luna Max | 1.00× |
| Sol Medium | 2.83× |
| Terra XHigh | 3.54× |
| Sol High | 4.53× |
| Sol XHigh | 6.64× |
| Gemini 3.8 Flash High | 6.97× |
| Terra Max | 7.84× |
| Astra Medium | 8.64× |
| Astra High | 9.65× |
| Sol Max | 11.15× |
| Astra XHigh | 12.95× |
| Astra Max | 18.27× |

비용계수는 실제 IIS ticket별 end-to-end 비용이 아니다. 재시도, 잘못된 완료 선언, 사람 검토, 외부 서비스 비용은 포함되지 않는다.

---

## 3. 비용 반영 최종 Top 8

### Outer Main

| 순위 | 구성 | 최종 점수 |
|---:|---|---:|
| 1 | Astra Max | 108.66 |
| 2 | Astra XHigh | 108.43 |
| 3 | Astra High | 108.04 |
| 4 | Astra Medium | 105.00 |
| 5 | Luna Max | 100.00 |
| 6 | Gemini 3.8 Flash High | 97.95 |
| 7 | Sol Max | 95.81 |
| 8 | Sol XHigh | 93.27 |

### Challenger

| 순위 | 구성 | 최종 점수 |
|---:|---|---:|
| 1 | Astra XHigh | 125.22 |
| 2 | Astra Max | 124.85 |
| 3 | Astra High | 123.45 |
| 4 | Astra Medium | 118.72 |
| 5 | Sol Max | 103.96 |
| 6 | Gemini 3.8 Flash High | 103.26 |
| 7 | Luna Max | 100.00 |
| 8 | Sol XHigh | 99.21 |

### Implementation

| 순위 | 구성 | 최종 점수 |
|---:|---|---:|
| 1 | Astra XHigh | 198.57 |
| 2 | Astra Max | 197.24 |
| 3 | Astra High | 188.23 |
| 4 | Astra Medium | 177.27 |
| 5 | Sol Max | 149.52 |
| 6 | Terra Max | 135.62 |
| 7 | Sol XHigh | 118.44 |
| 8 | Gemini 3.8 Flash High | 113.00 |

Luna Max는 이 역할에서 상대 필터를 통과하지만 상위 8개보다 최종 점수가 낮아 Top 8 밖이다.

### Heuristic Prober

| 순위 | 구성 | 최종 점수 |
|---:|---|---:|
| 1 | Astra XHigh | 193.98 |
| 2 | Astra Max | 193.19 |
| 3 | Astra High | 184.44 |
| 4 | Astra Medium | 174.41 |
| 5 | Sol Max | 148.24 |
| 6 | Terra Max | 137.31 |
| 7 | Sol XHigh | 117.36 |
| 8 | Gemini 3.8 Flash High | 113.36 |

### Verifier

| 순위 | 구성 | 최종 점수 |
|---:|---|---:|
| 1 | Astra XHigh | 142.44 |
| 2 | Astra Max | 142.23 |
| 3 | Astra High | 139.56 |
| 4 | Astra Medium | 135.15 |
| 5 | Sol Max | 118.20 |
| 6 | Gemini 3.8 Flash High | 109.17 |
| 7 | Terra Max | 107.74 |
| 8 | Sol XHigh | 106.50 |

---

## 4. 기본 선택 정책

점수 1위를 항상 기본값으로 쓰지 않는다. 특히 Max effort는 비용 증가가 크므로, **최종 점수 차이가 작으면 더 낮은 effort를 기본값으로 선택**한다.

### 권장 기본 배치

| IIS 역할 | 기본값 | 비용절감 | 상향 | 특수 상향 |
|---|---|---|---|---|
| Outer Main | **Astra High** | Astra Medium / Luna Max | Astra XHigh | Astra Max — automation-heavy에서만 |
| Challenger | **Astra High** | Astra Medium / Gemini High | Astra XHigh | Sol Max — 다른 모델군의 독립 공격이 필요할 때 |
| Implementation | **Astra High** | Luna Max / Sol XHigh / Gemini High | Astra XHigh | Sol Max — broad runtime/debugging, Astra Max는 일반적으로 비추천 |
| Heuristic Prober | **Astra High 또는 Sol Max** | Gemini High / Sol XHigh / Terra Max | Astra XHigh | Sol Max — broad runtime/debugging |
| Verifier | **Astra High** | Astra Medium / Gemini High | Astra XHigh | Astra Max는 High/XHigh 대비 근거가 약함 |

### 핵심 원칙

1. **Astra High는 전체적으로 가장 안정적인 premium 기본값**이다.
2. **Astra Medium은 일반 premium 가성비점**이다. High보다 약간 약하지만 Sol XHigh/Max와 비교해도 상당히 강하다.
3. **Astra XHigh는 실제 escalation tier**다. High에서 얻는 추가 이득이 작으면 기본값으로 쓰지 않는다.
4. **Astra Max는 대부분 자동 선택하지 않는다.** Outer의 Automation-heavy 사례처럼 Max가 실제로 더 나은 항목이 있을 때만 쓴다.
5. **Sol Max는 예외적으로 Max의 존재 이유가 분명하다.** Terminal v4에서 High/XHigh 대비 크게 상승하므로 broad execution/debugging에서는 단순 과추론으로 취급하면 안 된다.
6. **Terra Max는 XHigh보다 의미 있는 상승이 있다.** Terra를 쓴다면 대부분 Max를 검토한다.
7. **Luna Max는 ultra-budget 역할**이다. 싸다고 해서 복잡한 implementation/runtime closure에 충분하다고 가정하지 않는다.
8. **Gemini 3.8 Flash High는 중간 가격대 후보**다. Luna보다 execution/automation이 강하지만 Astra/Sol Max ceiling을 대체하지는 않는다.

---

## 5. Effort 선택 가이드

### Astra

#### Medium

사용:

- 일반 premium 작업
- 비용을 줄이고 싶지만 Luna/Sol보다 reasoning·contract reliability를 높이고 싶을 때
- routine planning / review / verifier 보조

장점:

- Sol XHigh/Max와 비교해도 강한 범용 성능
- High보다 저렴

주의:

- failure cost가 크거나 authority/verification 누락 위험이 크면 High로 올린다.

#### High

**기본 premium effort.**

사용:

- Outer Main
- 일반 Verifier
- 복잡한 Ready Ticket implementation
- 여러 authority와 flow를 동시에 추적해야 하는 작업

High가 기본인 이유는 Medium 대비 reliability gain이 아직 남아 있고, XHigh부터는 수익체감이 커지기 때문이다.

#### XHigh

사용:

- 매우 복잡한 implementation/runtime closure
- cross-boundary verification
- environment/state ambiguity가 큼
- 실패 비용이 높음

High와 점수 차이가 작은 역할에서는 자동 사용하지 않는다.

#### Max

사용:

- Automation-heavy workflow에서 Max의 직접 이득이 확인되는 경우
- XHigh 실패 후 마지막 escalation

일반 기본값으로 쓰지 않는다. Terminal v4에서는 XHigh가 Max보다 약간 높다.

---

### Sol

#### Medium

- 가장 저렴한 Sol premium 진입점
- 단순하지만 Luna보다 안정성을 높이고 싶은 경우

#### High

- 일반 execution의 비용절감 premium
- 요구사항 추적과 실행을 같이 해야 하지만 XHigh까지는 과한 경우

#### XHigh

- coding/runtime 중심의 균형점
- 복잡한 implementation에서 Luna/Gemini보다 강한 execution이 필요할 때

#### Max

**broad execution/debugging 전용 escalation tier.**

Terminal v4에서:

- High ≈ 20.7%
- XHigh ≈ 24.7%
- Max ≈ 39.9%

따라서 Sol Max는 단순히 마지막 몇 %를 쥐어짜는 설정이 아니다. 넓은 상태공간, 여러 service, root-cause investigation에서는 실제 성능 상승이 크다.

---

### Terra

#### XHigh

현재 공통 데이터에서는 애매하다. 비용이 Luna보다 높고, execution 성능도 Max 대비 크게 낮다.

#### Max

Terra를 선택해야 한다면 대부분 Max가 낫다.

Terminal v4에서 XHigh 약 10.1%, Max 약 35.4%로 차이가 매우 크다.

단, Astra Medium 또는 Sol 계열을 건너뛰고 Terra Max를 선택할 이유는 **특정 workload 실측에서 Terra가 유리할 때**여야 한다.

---

### Luna

#### XHigh

극단적 비용절감 모드. 성능 자체는 Luna Max보다 낮으므로 기본값으로 쓰지 않는다.

#### Max

**ultra-budget baseline.**

사용:

- 작은 bounded Ticket
- 실패 후 재시도가 쉬움
- acceptance/readback이 deterministic
- 오류가 발생해도 downstream 비용이 낮음

피해야 할 경우:

- 여러 Verification flow를 누락 없이 닫아야 함
- browser/provider/storage/runtime을 직접 검증해야 함
- 잘못된 완료 선언의 후속 비용이 큼
- broad debugging이 필요함

---

### Gemini 3.8 Flash High

포지션: **Luna와 premium 모델 사이의 mid-tier.**

현재 v4.3 기준:

- AutomationBench-AA 약 59.9%
- Terminal v4 약 19.7%
- Omniscience 29.55
- 비용 약 Luna Max의 6.97×

장점:

- Luna보다 execution/automation이 강함
- 빠른 출력 속도가 중요한 interactive workload에서 매력적
- Verifier/Challenger의 mid-tier 대안

약점:

- 현재 composite에서 Sol Max, Astra 계열의 execution ceiling보다 낮음
- Sol XHigh보다 비용이 약간 높은데 Implementation 점수는 낮음

선택 이유는 **중간 가격 + latency/throughput**이어야 하며, 순수 점수만 보면 Sol XHigh가 더 강한 경우가 많다.

---

## 6. 역할별 상세 선택 가이드

### 6.1 Outer Main

Outer Main은 IIS run 전체의 두 번째 planner가 아니라 thin orchestration owner다.

주요 요구:

- Run Contract carry-forward
- owner result routing
- completion reassessment
- authority/state drift 방지
- final fan-in

**기본: Astra High**

이유:

- Max 108.66, XHigh 108.43, High 108.04로 점수 차이가 매우 작다.
- High 비용계수 9.65×, XHigh 12.95×, Max 18.27×이므로 High가 practical knee다.

상향:

- 긴 workflow, 상태 전이가 많음 → XHigh
- Automation-heavy, Max의 추가 automation 성능이 중요한 경우 → Max

비용절감:

- 잘 구조화된 짧은 run → Astra Medium
- 매우 단순하고 재시도가 쉬운 orchestration → Luna Max

---

### 6.2 Adversarial Challenger

**기본: Astra High**

Top score는 XHigh지만, direct effort-matched adversarial benchmark가 없다. 따라서 1~2점 차이를 실제 반례 발견률 차이로 해석하지 않는다.

추천:

- 일반: Astra High
- 저비용 premium: Astra Medium
- 복잡한 cross-file/cross-authority attack: Astra XHigh
- 모델 다양성이 필요함: Sol Max 또는 Gemini High를 독립 challenger로 사용

피해야 할 패턴:

- Astra Max를 단순히 "가장 어려운 challenge"라는 이유만으로 사용
- review precision 하나만 보고 verifier/challenger 적합성을 추론

---

### 6.3 Implementation

현재 implementation skill은 단순 coding이 아니다. 구현자가 Ticket 범위 안에서:

- observable product outcome 해석
- 모든 authored Verification flow에 change/self-check 연결
- unit/integration/E2E/build/type/lint
- runtime/browser/provider/CLI/storage 직접 관찰
- authoritative readback
- decision-critical source/diff/artifact/command/runtime behavior 확인

까지 닫아야 한다.

**기본: Astra High**

이유:

- v4.3 composite 188.23으로 매우 높음
- XHigh 198.57 대비 성능 차이는 있지만 비용은 9.65× vs 12.95×
- Terminal v4에서도 54.0%로 강함

상향:

- 복잡한 runtime/evidence closure → Astra XHigh
- broad debugging / 여러 service / root-cause → Sol Max

비용절감:

- 쉬운 bounded Ticket → Luna Max
- 중간 tier → Sol XHigh 또는 Gemini High

중요:

**Luna Max의 낮은 비용은 sufficiency 증거가 아니다.**

---

### 6.4 Heuristic Prober

Probe는 자유 fuzzing이 아니라 Ticket-anchored false-completion path를 실제로 실행하고 최소 trigger로 줄이는 역할이다.

선택 기준을 두 갈래로 나눈다.

#### Reasoning-heavy probe

- 환경 규칙 자체가 불명확
- 여러 authority/flow를 동시에 해석
- false-completion path를 새로 구성

→ **Astra High / XHigh**

#### Execution-heavy probe

- cache/auth/network/provider/service boundary
- 반복 runtime execution
- broad root-cause investigation

→ **Sol Max**

비용절감:

- Terra Max / Sol XHigh / Gemini High

Luna Max는 정말 작은 deterministic probe에 한정한다.

---

### 6.5 Verifier

Verifier는 단순 bug finder가 아니라 evidence adjudicator다.

주요 요구:

- semantic contract preflight
- nearest nonconforming state
- discriminating observation
- sensitivity activation
- SATISFIED / CONTRADICTED / INCONCLUSIVE
- false PASS 억제

**기본: Astra High**

이유:

- XHigh 142.44, Max 142.23, High 139.56으로 상위 effort 간 차이가 작음
- High가 훨씬 저렴
- Omniscience/calibration 계열 신호가 강함

상향:

- 복잡한 cross-boundary verification → Astra XHigh
- 실행 surface가 매우 넓음 → Sol Max

중간 tier:

- Gemini High

주의:

Omniscience는 factual QA calibration이며 실제 IIS false-PASS율을 직접 측정하지 않는다.

---

## 7. 권장 escalation ladder

### 일반 reasoning / authority / verification

```text
Luna Max
  ↓ 충분하지 않음
Astra Medium
  ↓ 실패 비용이 높음 / authority 복잡
Astra High
  ↓ ambiguity 또는 cross-boundary가 큼
Astra XHigh
  ↓ 특별한 Automation-heavy 필요가 입증됨
Astra Max
```

### implementation / runtime execution

```text
Luna Max
  ↓ 쉬운 Ticket보다 복잡
Sol High / Gemini High
  ↓ repo/runtime complexity 증가
Sol XHigh
  ↓ broad debugging / multi-service / root-cause
Sol Max
  ↓ 최고 품질이 필요하고 비용 허용
Astra High / XHigh
```

실제 점수상 Astra High가 Sol 계열보다 높으므로, 조직이 vendor/latency 특성을 고려하지 않는다면 premium implementation에서 Astra High를 먼저 검토한다.

### heuristic probing

```text
작고 deterministic → Luna Max
중간 실행 → Gemini High / Sol XHigh / Terra Max
broad execution → Sol Max
reasoning-heavy / environment ambiguity → Astra High / XHigh
```

---

## 8. 빠른 결정표

| 상황 | 추천 |
|---|---|
| 비용이 최우선, 실패 복구 쉬움 | Luna Max |
| Luna보다 강한 중간 tier + 빠른 응답 | Gemini 3.8 Flash High |
| 일반 premium reasoning | Astra Medium |
| 실패 비용 높은 일반 premium | Astra High |
| 고난도 authority/verification | Astra XHigh |
| 일반 coding/runtime premium | Sol XHigh 또는 Astra High |
| broad runtime/debugging | Sol Max |
| Terra 사용이 필요한 환경 | Terra Max |
| Astra Max | 특별한 근거가 있을 때만 |

---

## 9. 모델군별 한 줄 요약

- **Astra Medium:** 일반 premium 가성비점.
- **Astra High:** IIS 전체에서 가장 안전한 기본 premium.
- **Astra XHigh:** 실제 고난도 escalation.
- **Astra Max:** 대부분 기본값으로 불필요, Automation-heavy 특수 상향.
- **Sol Medium:** 저가 Sol 진입점.
- **Sol High:** 일반 execution 비용절감형.
- **Sol XHigh:** coding/runtime 균형점.
- **Sol Max:** broad execution/debugging에서 의미 있는 Max.
- **Terra XHigh:** 현재 포지션이 약함.
- **Terra Max:** Terra를 쓴다면 대부분 이쪽.
- **Luna XHigh:** 극단적 절감 모드.
- **Luna Max:** ultra-budget baseline, adequacy 보장은 아님.
- **Gemini 3.8 Flash High:** 빠른 mid-tier, Luna와 premium 사이의 bridge.

---

## 10. 점수 해석 시 금지사항

다음처럼 해석하지 않는다.

1. `P >= 100` → "IIS skill을 충분히 수행한다".
2. 최종점수 198 → "Luna보다 실제 성공률이 98% 높다".
3. Max → "항상 해당 모델의 최고 설정".
4. Omniscience → 실제 verifier false-PASS율.
5. Terminal v4 → repository implementation 전체 품질.
6. 비용계수 → 실제 end-to-end 운영비.
7. Top 1 → 무조건 기본값.

이 점수는 **현재 공개 proxy와 80/20 비용 정책을 결합한 의사결정 지수**다.

---

## 11. 운영 검증 우선순위

향후 실제 IIS ticket 로그를 모으면 공개 benchmark보다 다음 지표를 우선한다.

### Implementation

- first-pass `Completion: COMPLETE` 비율
- 후속 Probe/Verifier에서 발견된 구현 결함률
- runtime evidence 누락률
- 재작업 횟수
- total API + runtime cost per verified Ticket

### Challenger

- material objection recall
- non-material objection rate
- 실제 candidate 수정으로 이어진 objection 비율

### Probe

- unique material finding rate
- minimal trigger 도달률
- cleanup 실패율
- verifier가 재현한 finding 비율

### Verifier

- false PASS
- false FAIL
- INCONCLUSIVE 적정성
- flow 누락률
- stale/unattributable evidence 사용률

이 실측이 충분히 쌓이면 AA 기반 가중치는 보조 자료로 낮추고, IIS 자체 데이터를 주 평가 기준으로 전환한다.

---

## 12. 현재 권장 roster

최소한의 모델 수로 운영한다면:

```text
Luna Max                 : ultra-budget
Gemini 3.8 Flash High    : fast mid-tier
Astra Medium             : value premium
Astra High               : default premium
Astra XHigh              : reasoning ceiling
Sol XHigh                : execution premium
Sol Max                  : broad runtime/debugging escalation
```

선택적으로:

```text
Terra Max                : workload-specific alternative
Astra Max                : special Automation-heavy escalation
```

이 구성이라면 대부분의 IIS 역할과 escalation 경로를 커버할 수 있다.
