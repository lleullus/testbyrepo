# Adaptive Planning Mandate

Mode: IIS Adaptive Planning
Status: active
Revision: 1
Owner: user01
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Applies-To: webterm-session-reconnect-grace

## Desired Product Outcome

webterm(ttyd-1.7.7) 모바일 웹 터미널의 세션 재접속 대기 유예 시간(reconnect grace)을 기본 6시간(21,600초)에서 9시간(32,400초)으로 확장하고, 모바일 슬립/네트워크 단절 시에도 호스트 프로세스가 절대 block되지 않도록 PTY continuous drain을 확립하며, 버퍼 오버플로 후 재접속 시 foreground TUI에 정밀한 SIGWINCH 재그리기를 유발하여 모바일 터미널 개발 환경의 완전한 세션 연속성을 달성한다.

## Why / User Value

안드로이드 모바일 기기에서 장시간 화면 슬립, 네트워크 단절(지하철/이동), 배터리 절전 모드가 발생하더라도 호스트 워크스테이션에서 구동 중인 OMP subagent, 빌드, 장시간 테스트 작업이 중간에 얼어붙지 않고 끝까지 완주되어야 하며, 9시간 이내에 복귀했을 때 직전 작업 터미널 세션을 깨짐 없이 안정적으로 이어갈 수 있어야 한다.

## Decision Priorities

1. 호스트 프로세스 무단절(Non-blocking Execution): 브라우저의 전송 지연, 백그라운드 슬립, PAUSE 상태가 호스트 자식 프로세스(PTY read)를 절대 정지시키지 않는다.
2. 상태 정직성(State Truthfulness): 데이터 유실이 발생했을 때 가짜 복원으로 위장하지 않고, 단일 needs_redraw 플래그 및 foreground PGID SIGWINCH를 통해 실제 TUI 자체 재그리기를 유발한다.
3. 안티-블로트(Anti-Bloat): 복잡한 가상 가드레일(resumed-reset-v1, resetGate, terminal.reset)을 배제하고, 단일 8MB 바운디드 큐 및 단일 릴리즈 바이트열을 통해 최소한의 직접적 구현을 유지한다.
4. 안전한 원자적 릴리즈: 3중 드리프트 상태를 해소하고, 실행 중인 deleted 바이너리 보존 및 단 1회 계획된 서비스 교체로 런타임 안정성을 보장한다.

## Hard Constraints

- Tailscale Funnel 설정(/terminal -> 127.0.0.1:7683)을 수정하거나 재설정하지 않는다.
- session.sh는 접속마다 독립적인 신규 로그인 셸(/bin/bash -l)을 기동하며, tmux나 세션 공유를 강제하지 않는다.
- 세션 재접속 유예 기본값은 9시간(32,400초)이며, TTYD_RECONNECT_GRACE 환경변수의 허용 범위는 1~32400초이다.
- WebSocket 5초 핑 주기 / 30초 유예 정책을 준수한다.
- 릴리즈 시 정확히 동일한 단일 바이트열(RC_TTYD, RC_HTML)을 스테이징(7684) 검증 후 프로덕션(7683)에 원자적으로 승격한다.

## Non-Goals

- WebSocket ping/pong 하트비트 주기 변경
- xterm 프론트엔드 모바일 툴바 레이아웃 또는 UI 테마 재설계
- Sixel 그래픽 지원 기능 복원
- tmux 기반 세션 영속화 도구 재도입

## Delegated Planning Authority

- 세션 유예 시간 및 PTY continuous drain 단일 큐 설계를 위한 Increment 범위 조정 및 재구성
- 미커밋 WIP의 가상 가드레일(resumed-reset-v1, resetGate) 제거 및 needs_redraw 단일화
- 준비 단계(ready-ticket-plan)의 실행 계획 수립 및 리뷰어 위임 관리

## Continuation Authority

MANDATE_OUTCOME

Meaning: maximum authorized success-continuation ceiling after a delivered current Increment, not the terminal condition of every invocation.

## Return-to-User Boundary

- 호스트 프로세스 무단절 원칙과 상충되는 버퍼링 정책 변경이 필요한 경우
- Tailscale Funnel 라우팅 또는 포트 변경이 불가피한 경우
- 릴리즈 시퀀스 중 복구 불가능한 서비스 중단 위험이 식별된 경우

## Source User Authority

사용자 명령: "기본 대기 시간 6시간인거 9시간으로 늘리려고해 -> 위 내용 기반으로 iis 사전조사 진행해", "휴리스틱 루나 맥스 플랜 리뷰어 오라클 브라우저 3번 슬롯 팔로우업 코덱스프로모드로 진행할 수 있게 함, 워커 루나 맥스, 검증 루나 맥스 그리고 넉 ㅏ아우터 메인으로 루프 책임 골 아웃컴 집중해서 시작해"

## Notes

- This Mandate delegates IIS planning judgment only; it does not make Adaptive Planning the implementation or verification authority.
- Continuation Authority is the maximum success-continuation ceiling. The invocation-local Adaptive Run Contract defines the actual Run Completion Boundary and Completion Predicate.
- Explicit Adaptive activation separately supplies Outer Main's default current-Increment implementation/verification handoff unless the user opts out.
- A Run Completion Boundary broader than this ceiling requires an explicit current Mandate revision/adoption before mutation; never silently stop early or expand authority.
- Neither the Mandate nor Adaptive activation authorizes deployment, credentials, production/shared external mutation, destructive action, worker selection, or adversarial-consensus activation.
- Canonical IIS artifacts remain governed by current Baseline schemas and validators.
