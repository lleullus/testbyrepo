---
title: "Understand Anything - 코드베이스 지식 그래프 사례"
status: draft
date: 2026-06-16
source: "https://github.com/Egonex-AI/Understand-Anything"
---

## Oracle 분석 요약

`Understand Anything`는 **정적 분석 + LLM 의미 분석**으로 코드베이스를 지식 그래프로 만들고, 탐색 UI, 검색, 온보딩, 도메인 뷰, diff 영향 분석까지 제공하는 도구다.

핵심은 "그래프를 보여주는 것"이 아니라 **대형 코드베이스를 읽는 방식을 구조화하는 것**이다.

## 1. 프로젝트가 실제로 하는 일

- 프로젝트를 스캔해서 파일, 함수, 클래스, 의존성, 도메인 흐름을 그래프로 만든다.
- 결과물은 `.understand-anything/knowledge-graph.json`에 저장된다.
- `/understand-dashboard`로 시각 그래프를 탐색한다.
- `/understand-diff`로 변경 영향 범위를 확인한다.
- `/understand-domain`으로 비즈니스 도메인, 흐름, 단계를 뽑아낸다.
- `/understand-chat`, `/understand-explain`, `/understand-onboard`, `/understand-knowledge` 같은 명령으로 학습/질의/탐색 흐름을 분리한다.
- `/understand --auto-update`로 커밋 시 그래프를 갱신할 수 있다.
- `--language`로 그래프 요약과 UI를 다국어로 생성할 수 있다.

## 2. 아키텍처

### 분석 엔진의 핵심 구조

- **Tree-sitter**: import/export, 함수/클래스 정의, call site, 상속 같은 구조적 사실을 결정적으로 추출한다.
- **LLM**: 구조를 읽고 plain-English 요약, 태그, 레이어, 비즈니스 도메인 매핑, guided tour를 만든다.

이 분리는 중요하다.

- 구조 사실은 반복 가능한 정적 분석이 맡는다.
- 의미 해석은 LLM이 맡는다.
- 그래서 그래프는 재현 가능하면서도, 사람에게 설명 가능한 형태가 된다.

### 파이프라인 역할

- `project-scanner`: 파일 탐색, 언어/프레임워크 감지
- `file-analyzer`: 함수/클래스/import/edge 추출
- `architecture-analyzer`: 아키텍처 레이어 식별
- `tour-builder`: guided tour 생성
- `graph-reviewer`: 그래프 완결성과 참조 무결성 검증
- `domain-analyzer`: 도메인/흐름/단계 추출
- `article-analyzer`: 위키/지식베이스 문서의 엔터티/관계 추출

## 3. 저장소와 운영 방식

- pnpm workspace 기반 monorepo다.
- `understand-anything-plugin/`에 플러그인, core, dashboard, skills, agents가 들어간다.
- `packages/core`는 분석 엔진, 영속화, 검색, 스키마, fingerprint, staleness 등을 담당한다.
- `packages/dashboard`는 React + TypeScript 대시보드다.
- 대시보드는 graph-first 레이아웃을 쓰고, info/files 중심으로 탐색한다.
- source viewer는 별도의 파일 패널/모달로 띄우는 구조다.
- 결과는 코드나 문서가 아니라 **재사용 가능한 산출물**로 취급된다.

### 핵심 사용 흐름

1. 설치한다.
2. `/understand`로 그래프를 만든다.
3. `/understand-dashboard`로 구조를 읽는다.
4. `/understand-diff`로 변경 영향을 본다.
5. 필요하면 `/understand-domain`, `/understand-chat`, `/understand-explain`으로 더 좁혀 들어간다.

### 플랫폼 지원

- Claude Code
- Codex
- OpenCode
- Cursor
- Copilot
- Gemini CLI
- Vibe CLI
- Trae
- Kiro
- 기타 다수

즉, 이 프로젝트는 특정 IDE 기능이 아니라 **플랫폼 공통의 코드 이해 계층**을 노린다.

## 4. 프로젝트 99에 가져올 인사이트

### 4.1 코드 이해는 문서가 아니라 산출물이어야 한다

가장 중요한 교훈은 코드베이스 이해를 설명문으로만 두지 않는다는 점이다.
그래프, 요약, guided tour, diff 영향 분석을 **생성 가능한 산출물**로 만든다.

프로젝트 99에도 같은 원칙을 적용할 수 있다.

- 명세 문서를 사람이 수동으로 쓰는 것과
- LLM이 읽을 수 있는 구조화 산출물을 남기는 것은

같지 않다.

### 4.2 구조와 의미를 분리해야 한다

이 repo는 구조 사실과 의미 해석을 분리한다.
이건 99번 프로젝트에서 특히 중요하다.

- 구조: 모듈 경계, 파일 의존성, 호출 관계, 변경 범위
- 의미: 도메인 약속, 안전 경계, 운영 규칙, 검증의 우선순위

즉, `01. 컨텍스트 맵과 도메인 안전 경계`는 구조와 경계를 맡고, `03. LLM 친화적 코드베이스 기준`은 사람이 이해하기 쉬운 운영 조건을 맡아야 한다.

### 4.3 변경 전에 영향 범위를 보여줘야 한다

`/understand-diff` 같은 흐름은 작업 전에 blast radius를 드러내는 사고방식이다.

99번 프로젝트에서도 이 방향이 유효하다.

- 변경 의도
- 직접 수정 범위
- downstream behavior
- 다시 검증할 invariant

이 4개를 먼저 선언하면, `03. LLM 친화적 코드베이스 기준`의 검증 체계와 바로 연결된다.

### 4.4 LLM 산출물도 검토해야 한다

`graph-reviewer`는 단순 출력이 아니라 **완결성/참조 무결성 검토**를 둔다.
이건 중요한 패턴이다.

LLM이 만든 결과라도 다음이 필요하다.

- 누락 검사
- 참조 무결성
- 중복/충돌 검사
- 스키마 적합성
- 재생성 가능성

99번 프로젝트에서는 "LLM이 정리한 문서"를 그냥 설명으로 끝내지 말고, 검증 가능한 구조로 취급해야 한다.

### 4.5 코드베이스 이해는 UI 문제이기도 하다

이 repo는 graph-first 대시보드, files 패널, source viewer, persona-adaptive UI를 제공한다.
즉, 이해를 돕는 것은 분석만이 아니라 **표현 방식**이다.

99번 프로젝트에서 의미 있는 질문은 이거다.

- LLM이 읽기 쉬운 문서는 어떤 형태인가
- 사람이 빠르게 훑을 수 있는 구조는 어떤가
- 큰 코드베이스를 이해하는 데 필요한 기본 UI는 무엇인가

## 5. 프로젝트 99에 적용할 때의 해석

이 repo를 그대로 복제하면 안 된다.
대신 아래처럼 해석하는 게 맞다.

- `Understand Anything`은 **외부 사례**다.
- 99번 프로젝트의 본문은 여전히 `01. 컨텍스트 맵과 도메인 안전 경계`, `02. 작업 프로토콜`, `03. LLM 친화적 코드베이스 기준`이 주도한다.
- 이 노트는 그 본문을 보강하는 **레퍼런스 증거**다.
- 그래프는 source of truth가 아니라, source of truth를 읽기 쉽게 만드는 계층이다.

특히 다음 원칙은 유지해야 한다.

- 구조 맵보다 도메인 불변식이 우선이다.
- 자동 생성 문서보다 검증 규칙이 우선이다.
- 탐색 UI보다 경계/책임 정의가 우선이다.
- 편한 요약보다 재현 가능한 근거가 우선이다.

## 6. 배치 원칙

이 분석은 아래처럼 배치하는 것이 가장 좋다.

### 지금 위치

- `외부 레퍼런스/Understand Anything - 코드베이스 지식 그래프 사례.md`

### 연결할 문서

- `00. LLM 바이브 코딩 코드베이스 관리 홈`
- `01. 컨텍스트 맵과 도메인 안전 경계`
- `02. 작업 프로토콜`
- `03. LLM 친화적 코드베이스 기준`

### 문서 역할

- `00`: 링크 허브
- `01`: 구조와 경계
- `02`: 작업 루프와 실행 흐름
- `03`: LLM 친화적 운영 기준
- `04`: 외부 사례 증거와 분석 메모

## 7. 최종 판단

`Understand Anything`은 99번 프로젝트에 다음 메시지를 준다.

- 코드베이스 이해는 감상이 아니라 시스템이다.
- 시스템은 그래프, 검색, 검토, 영향 분석, 온보딩 흐름으로 구성된다.
- 그러나 그 위에도 여전히 경계, 불변식, 검증 규칙이 우선이다.
- 그래서 이 사례는 99번의 대체물이 아니라, 99번이 추구하는 문서/운영 체계를 보강하는 참고 사례다.
