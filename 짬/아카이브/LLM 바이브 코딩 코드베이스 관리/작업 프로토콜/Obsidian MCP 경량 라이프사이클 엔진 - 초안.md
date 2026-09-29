---
title: Obsidian MCP 경량 라이프사이클 엔진 - 초안
status: draft
role: memo
date: 2026-06-17
tags:
  - llm
  - obsidian-mcp
  - lifecycle
  - draft-skeleton
related:
  - "[[짬/아카이브/LLM 바이브 코딩 코드베이스 관리/작업 프로토콜/개요|02. 작업 프로토콜]]"
  - "[[옵시디언 위키 컨텍스트 인덱스 전략|옵시디언 위키 컨텍스트 인덱스 전략]]"
  - "[[04. 도입과 운영 프로토콜|04. 도입과 운영 프로토콜]]"
  - "[[oracle-plan-review - 요구사항 구조화와 Dryforge Bridge Packet 스킬 사례|oracle-plan-review 사례]]"
  - "[[oneshot - 실행 계약과 Guarded Execution Pack 스킬 사례|oneshot 사례]]"
  - "[[tech-debt-skill - 파일 인용 기술부채 감사 스킬 사례|tech-debt-skill 사례]]"
---

## 0. 이 노트의 역할

이 노트는 외부 도구의 구조를 그대로 가져오는 문서가 아니다.

목적은 Obsidian의 프로젝트 노트와 컨텍스트를 받아, 구현 에이전트에게 넘기기 전에 한 번 얇게 구조화하는 최소 골격을 잡는 것이다.

완성된 프레임워크가 아니라 초안이며, 과도한 ceremony 대신 handoff 직전의 최소 정리 절차만 다룬다.

## 1. 입력: Obsidian project note / context

입력은 코드 자체가 아니라 다음과 같은 Obsidian 문맥이다.

- 프로젝트 노트
- 관련 context index
- touched context / touched modules
- 금지 영역과 required checks
- 현재 명확한 것과 아직 모르는 것

여기서 중요한 점은 Obsidian을 진실의 원천으로 두지 않는 것이다.
코드, 테스트, 스키마가 fact이고, Obsidian은 context routing과 의미 압축 계층이다.

## 2. 최소 흐름

```text
Context 선택
-> 요구사항 구조화
-> 최소 slice 선택
-> handoff prompt seed 작성
-> 구현 에이전트 전달
-> 결과와 evidence를 Obsidian에 되돌림
```

이 흐름은 기존 `Research -> Plan -> Small diff -> Run checks -> Review -> Merge`를 대체하지 않는다.
복잡하거나 모호해서 바로 `Plan`으로 가기 어려운 작업에서 앞단 보조 루프로 사용한다.

## 3. 요구사항 구조화에서 가져올 것

외부 레퍼런스에서 가져올 핵심은 요구사항을 바로 구현 지시로 보내지 않는 태도다.

여기서는 다음 정도만 고정한다.

- 사용자가 실제로 원하는 결과
- 이번 요청에서 확인 가능한 성공 신호
- 이번 턴에서 다루지 않을 것
- 아직 owner 판단이 필요한 것

지금 단계에서 파일명, 함수명, DTO, 테스트 shape까지 정하지는 않는다.

## 4. 최소 slice에서 고정할 것

구현 에이전트로 넘기기 전 최소한 아래만 정리한다.

- 이번 slice의 목표
- in scope
- out of scope
- deferred
- unknown / needs owner

핵심은 한 번에 전체를 해결하려 하지 않고, 검토 가능한 최소 단위로 줄이는 것이다.

## 5. handoff prompt에 담을 것

handoff는 긴 프롬프트가 아니라 작은 계약에 가깝다.

최소 포함 항목:

- 목표
- 참조해야 할 Obsidian 노트
- 이번 slice 범위
- 제외 범위
- 필요한 검증 기대치
- 결과를 다시 남겨야 할 위치

즉, 프롬프트를 잘 쓰는 것보다 무엇을 넘기고 무엇을 넘기지 않을지를 먼저 고정한다.

## 6. 구현 에이전트에게 넘기기 전 중단 조건

다음 중 하나라도 해당하면 바로 handoff 하지 않는다.

- source note가 불분명함
- 필요한 context link가 비어 있음
- in scope / out of scope 구분이 없음
- 성공 신호가 너무 추상적임
- 모르는 것을 아는 척 메우고 있음

이 단계의 목적은 승인 절차를 늘리는 것이 아니라, 잘못된 시작을 줄이는 것이다.

## 7. 구현 후 Obsidian에 되돌릴 것

구현 이후에는 최소한 다음을 남긴다.

- 무엇을 바꿨는지
- 어떤 evidence를 확인했는지
- 아직 주장하지 않는 것은 무엇인지
- 새로 발견한 context gap이 있는지
- 후속 slice가 필요한지

핵심은 실행 결과가 프롬프트나 세션 안에서만 끝나지 않고, 다시 Obsidian 문맥으로 환류되는 것이다.

## 8. 지금은 하지 않을 것

지금 초안에서는 다음을 만들지 않는다.

- full lifecycle framework
- O1/O2 같은 gate taxonomy
- `.oracle`, `.dryforge`, `.oneshot` 구조 복제
- validator / fixture / registry
- closure matrix
- 상세 상태 머신
- 별도 대형 감사 체계

지금 필요한 것은 거대한 운영체계가 아니라, 큰 요청을 실행 전에 한 번 얇게 줄이고 실행 후 결과를 다시 연결하는 최소 뼈대다.
