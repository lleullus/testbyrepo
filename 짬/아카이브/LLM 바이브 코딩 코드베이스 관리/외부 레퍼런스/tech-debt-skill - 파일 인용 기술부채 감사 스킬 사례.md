---
title: "tech-debt-skill - 파일 인용 기술부채 감사 스킬 사례"
status: draft
date: 2026-06-17
source: "https://github.com/ksimback/tech-debt-skill"
---

## 한 줄 요약

`tech-debt-skill`은 코드베이스 전체를 대상으로, `file:line` 근거가 붙은 기술부채 감사 문서를 생성하는 Claude Code Skill이다.

이 저장소의 핵심은 “무엇이 나쁜가”를 일반론으로 말하는 게 아니라, **무엇이 실제로 문제인지, 어디에 있는지, 얼마나 중요한지, 얼마나 고치기 쉬운지**를 증거 기반으로 남기는 데 있다.

## 이 스킬이 해결하는 문제

일반적인 LLM 코드 리뷰는 잘못된 방향으로 흐르기 쉽다.

- 코드 전체를 읽지 않은 상태에서 먼저 결론을 낸다.
- generic best practices를 실제 코드에 덧씌운다.
- “전반적으로 구조가 좋다” 같은 무의미한 칭찬으로 끝난다.
- 정작 고쳐야 할 지점은 근거 없이 뭉개진다.

`tech-debt-skill`은 그 실패를 막기 위해 설계되었다.

- 판단 전에 저장소를 먼저 이해한다.
- 모든 finding에 `file:line`을 요구한다.
- “나빠 보이지만 사실 괜찮은 것”을 반드시 기록한다.
- 한 번 끝나는 리뷰가 아니라 반복 추적 가능한 자산으로 남긴다.

## 저장소 성격

이 저장소는 애플리케이션이 아니라 **단일 Claude Code Skill 정의**다.

- 파일 수가 매우 적다.
- 핵심은 `README.md`와 `SKILL.md`다.
- `/tech-debt-audit` 하나로 호출된다.
- 결과물은 `TECH_DEBT_AUDIT.md`다.

즉, 이 저장소는 코드가 아니라 **코드 감사 프로토콜 자체**를 배포하는 저장소다.

## 프로토콜 구조

### 메타데이터

`SKILL.md`는 이 스킬을 다음처럼 정의한다.

- 이름: `tech-debt-audit`
- 사용 방식: user-invoked
- 자동 호출: 금지
- 역할: 전체 저장소의 기술부채 감사

이 구조는 중요하다. 이 스킬은 모델이 임의로 발동하는 보조 기능이 아니라, 사용자가 명시적으로 호출하는 **책임 있는 감사 절차**다.

### Phase 1: Orient

가장 중요한 단계다. 여기서 판단을 보류하고, 먼저 저장소의 실제 형태를 이해한다.

해야 할 일:

- README 읽기
- manifest 읽기 (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`)
- `/docs`, `/adr` 같은 아키텍처 문서 읽기
- 디렉터리 구조 파악
- entry point, hot path, cold corner 식별
- 최근 git churn 파악
- 큰 파일과 자주 바뀐 파일의 교집합 찾기
- 1~2문단짜리 architecture mental model 작성

핵심은 이거다.

> 구조를 이해하기 전에 비판하지 말 것.

프로젝트 99에서도 이 규칙이 그대로 필요하다. LLM이 코드를 조금 읽고 바로 리팩터링 제안하는 습관을 끊어야 한다.

### Phase 2: Audit

이 단계는 9개 차원으로 기술부채를 조사한다.

1. Architectural decay
2. Consistency rot
3. Type & contract debt
4. Test debt
5. Dependency & config debt
6. Performance & resource hygiene
7. Error handling & observability
8. Security hygiene
9. Documentation drift

특징은 두 가지다.

- `rg`, `ast-grep`, 언어별 도구로 실제 증거를 찾는다.
- 모든 finding에 `file:line`을 붙인다.

즉, 이 스킬은 감상문이 아니라 **증거 기반 감사**다.

### Phase 3: Deliverable

결과는 `TECH_DEBT_AUDIT.md`에 쓴다.

필수 섹션:

- Executive summary
- Architectural mental model
- Findings table
- Top 5
- Quick wins
- Things that look bad but are actually fine
- Open questions for the maintainer

이 구조는 관리하기 좋다.

- 요약은 우선순위를 보여준다.
- mental model은 시스템 이해를 공유한다.
- findings table은 backlog로 바뀐다.
- Top 5는 실제 행동 순서를 만든다.
- quick wins는 바로 처리할 것을 분리한다.
- fine-but-weird 섹션은 과잉 리팩터링을 막는다.
- open questions는 불확실성을 허세로 덮지 않는다.

## 이 스킬이 유용한 이유

### 1. 판단 전에 방향을 만든다

Phase 1이 강제된다는 점이 핵심이다.
많은 LLM 결과물은 “읽은 척”은 하지만 실제 mental model이 없다.

이 스킬은 다음 순서를 지킨다.

- 읽기
- 구조화
- churn 확인
- hotspot 확인
- mental model 작성
- 그 다음에야 판단

프로젝트 99에서 이건 매우 중요한 원칙이다.
`01. 컨텍스트 맵과 도메인 안전 경계`나 `02. 작업 프로토콜`의 앞단에 넣을 수 있다.

### 2. finding을 반증 가능하게 만든다

`file:line`은 단순 출처 표기가 아니다.
이건 다음을 가능하게 한다.

- 사람이 실제 라인을 열어 검증
- finding을 이슈/PR로 변환
- 다음 감사에서 해결 여부 추적
- 근거 없는 일반론 차단

99번 프로젝트에서는 기술부채뿐 아니라 구조 문제, 테스트 부채, 문서 drift에도 이 원칙을 걸어야 한다.

### 3. “나빠 보이지만 괜찮은 것”을 반드시 남긴다

이 섹션은 실무적으로 아주 중요하다.

왜냐하면 LLM은 종종 복잡해 보이는 코드를 무조건 나쁜 것으로 판단하기 때문이다.
그러나 실제로는 ordering guarantee, compatibility, data invariant, legacy contract 때문에 유지되어야 하는 복잡성이 있다.

이 스킬은 그 가능성을 문서 구조에 강제로 넣는다.

### 4. 반복 실행을 전제로 한다

이 스킬은 1회성 진단이 아니라 living document를 만든다.
기존 감사 문서를 읽고, 해결된 것은 `RESOLVED`, 새 것은 `NEW`로 남긴다.

이건 프로젝트 99에도 잘 맞는다.
문서가 “한 번 읽고 끝나는 설명”이 아니라, **진행 중인 관리 기록**이 되어야 한다.

## 프로젝트 99에 가져올 핵심 인사이트

### 1. Orientation gate는 필수다

프로젝트 99에서 어떤 분석이나 리팩터링도 먼저 아래를 거쳐야 한다.

- manifest
- entry point
- hot path
- current docs
- module boundary
- churn hotspot
- large-file hotspot
- mental model

이건 단순한 사전 조사 단계가 아니라, **판단 권한을 얻기 위한 조건**이다.

### 2. 기술부채는 범주가 아니라 증거로 판단해야 한다

좋은 분류만으로는 부족하다.
중요한 건 “어디에, 왜, 얼마나”다.

그래서 99번 프로젝트에는 이런 필드가 필요하다.

- file:line
- severity
- effort
- status
- owner / follow-up
- changed_since
- evidence_type

### 3. 감상 대신 감사 문서를 남겨야 한다

프로젝트 99는 LLM 친화적 코드베이스 관리가 목표다.
그러면 LLM의 판단도 관리 가능한 산출물이 되어야 한다.

이 스킬이 보여주는 방식은 다음과 같다.

- 문제를 찾는다
- 근거를 단다
- 우선순위를 매긴다
- 조치 가능하게 만든다
- 반복 검증 가능하게 남긴다

### 4. “좋아 보이는 정리”보다 “정확한 불편함”이 중요하다

이 스킬은 보기 좋은 요약보다 실제 debt hotspot을 찾아낸다.
프로젝트 99도 같아야 한다.

- 예쁘지만 비어 있는 문서
- 넓지만 근거 없는 설명
- 리팩터링 같은 말만 있고 action이 없는 텍스트

이런 것보다, 실제 파일/라인과 연결된 불편한 사실이 훨씬 중요하다.

## 프로젝트 99에 맞는 추가 확장점

이 스킬을 그대로 따라가기보다, 99번 프로젝트는 아래 차원을 더 붙이는 게 좋다.

### 추가할 audit 차원

- Prompt / instruction drift
- Tool-call boundary debt
- Context-map drift
- Spec-to-test gap
- Exception / bypass debt
- Fixture determinism debt

### 추가할 lifecycle

- `NEW`
- `ACTIVE`
- `RESOLVED`
- `STALE`
- `ACCEPTED_DEBT`
- `NEEDS_OWNER_INPUT`

### 추가할 저장 필드

```md
repo:
audit_id:
commit_sha:
scope:
generated_at:
mode: first-run | repeat-run
baseline_audit:
```

이렇게 하면 99번 프로젝트는 단순 기술부채 체크리스트가 아니라, **지속적으로 갱신되는 검증 가능한 레지스터**를 갖게 된다.

## “Looks bad but is actually fine”를 99번식으로 쓰는 법

이 섹션은 프로젝트 99에서 따로 강조할 가치가 있다.

추천 포맷:

```md
| File:Line | Looks bad because | Actually fine because | Do not change unless |
|---|---|---|---|
```

이렇게 쓰면 다음이 가능하다.

- 복잡성의 이유를 기록
- 보존해야 할 계약을 명시
- 무분별한 simplification 방지
- LLM이 과잉 리팩터링하는 것 방지

## 99번 문서 체계에서 어디에 둘까

이 분석은 외부 사례이므로, 본문 문서보다 **레퍼런스 + 운영 규칙**의 성격이 강하다.

추천 배치:

- `외부 레퍼런스/tech-debt-skill - 파일 인용 기술부채 감사 스킬 사례.md`
- `08. 반복 감사와 기술부채 레지스터.md`를 별도 핵심 문서로 추가
- `02. 작업 프로토콜`에 실행 시점을 연결
- `01. 컨텍스트 맵과 도메인 안전 경계`에 orientation gate를 연결
- `01. 실행 가능한 명세.md`에 finding→검증 전환 규칙을 연결

즉, 이 스킬은 99번에서 “참고 자료”이면서 동시에 “운영 프로토콜의 원형”이다.

## 최종 판단

이 저장소의 핵심 가치는 다음 한 문장으로 정리된다.

> LLM이 기술부채를 말하려면, 먼저 저장소를 이해하고, 근거를 달고, 예외를 기록하고, 반복 추적 가능하게 남겨야 한다.

프로젝트 99에는 이 원칙을 거의 그대로 가져가되, 기술부채뿐 아니라 **명세, 경계, fixture, tool boundary, prompt drift**까지 확장하면 된다.
