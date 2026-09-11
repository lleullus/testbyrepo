# Adaptive Planning Trace

Planning-Slug: webterm-session-reconnect-grace
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Status: active

## Material Decisions

### 001 — Run Contract Closure and Delivery Model Selection
Provenance: USER_EXPLICIT
Authority: Mandate Revision 1
Evidence: /tmp/WEBTERM_ADAPTIVE_RUN_CONTRACT.md, /tmp/WEBTERM_INVESTIGATION_AND_AUDIT_REPORT.md, INV-001.md
Decision: Run Contract를 CLOSED로 확정. Required Named Items 6개 항목(9시간 유예, PTY continuous drain 단일 큐, foreground PGID SIGWINCH, terminal.reset 경계 분리, Anti-Bloat 가드레일 축소, 단일 바이트열 릴리즈)을 필수 완료 집합(EXACT_REQUIRED_SET)으로 고정하고, 구현 및 검증 모델로 opencodex-gpt5.6-luna-max를 확정, 준비 단계 모델로 휴리스틱(Luna Max) 및 플랜 리뷰어(Oracle Browser Slot 3)를 지정.
Reason: 사용자의 명시적 지시("휴리스틱 루나 맥스 플랜 리뷰어 오라클 브라우저 3번 슬롯... 워커 루나 맥스, 검증 루나 맥스 그리고 넉 ㅏ아우터 메인으로 루프 책임 골 아웃컴 집중해서 시작해")에 따라 모델 및 역할을 직접 바인딩함.
Affected canonical artifacts: None
Re-entry / next leaf: Scope Shaper
