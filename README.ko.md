# OMP용 Lumin Repo Lens

[`annyeong844/lumin-repo-lens`](https://github.com/annyeong844/lumin-repo-lens)
`0.9.0-beta.93`을 OMP에 맞게 완전히 포팅한 배포본입니다. 기준 upstream
커밋은 `f7a9cee61d49e06a8350cd125a6b0641a64a59c0`입니다.

TypeScript/JavaScript 저장소를 스캔해 중복 구조, 미사용 export, 순환 의존성,
topology, barrel, 네이밍 drift, 쓰기 이후 새로 생긴 type escape를 실제
증거로 보여줍니다. 분석 엔진은 그대로 보존하고 Claude 전용 연동부만 OMP
이벤트와 확장 모듈로 교체했습니다.

## OMP에 설치

```bash
git clone --branch snapshot/lumin-repo-lens-omp --single-branch \
  https://github.com/lleullus/testbyrepo.git lumin-repo-lens-omp
cd lumin-repo-lens-omp
omp plugin link .
```

확장 모듈을 불러오려면 OMP를 다시 시작하세요. 명령과 skill만 갱신할 때는
`/reload-plugins`를 사용할 수 있습니다.

로컬 marketplace 방식도 지원합니다.

```text
/marketplace add /absolute/path/to/lumin-repo-lens-omp
/marketplace install lumin-repo-lens@lumin-repo-lens-omp-marketplace
```

첫 점검:

```text
/lumin-repo-lens:full
```

코드 변경 전후:

```text
/lumin-repo-lens:pre-write
# 코드 변경
/lumin-repo-lens:post-write
```

## 포팅 범위

- upstream의 모든 audit profile과 evidence producer
- 3개 skill 전체
- 9개 namespaced slash command 전체
- OMP `write`/`edit` 실행 직전 preimage 저장
- 실행 후 type-escape delta 확인과 reminder 전달
- OMP turn 직전 reminder 주입
- `AUDIT_ACK <event-id> intentional|fixed|noted` 처리
- `.omp-plugin/marketplace.json`과 `omp.extensions`
- Node/Bun 테스트와 실제 임시 TS 저장소 smoke test

세부 대응표는 [OMP_PORT.md](./OMP_PORT.md)에 있습니다.

## 요구사항

- TypeScript extension을 지원하는 OMP
- Node.js `^20.19.0` 또는 `>=22.12.0`
- TypeScript/JavaScript 저장소와 monorepo에 가장 적합

## 라이선스

MIT. 원본 구현과 저작자 표시는 `annyeong844`에 그대로 귀속되며, 이
브랜치는 OMP 호스트 연동 포트를 추가합니다.
