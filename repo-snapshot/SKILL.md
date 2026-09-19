---
name: repo-snapshot
description: >
  Use when the user asks for repo-snapshot, 레포 스냅샷, Git 검토용 레포 복사,
  or wants a full working-tree Git snapshot pushed to the shared snapshot
  repository. This is an independent Git utility and does not depend on Oracle.
---

# Repo Snapshot Skill

작업 중인 Git 레포의 **full 스냅샷**을 별도 원격 저장소에 push한다.
이 스킬은 Oracle과 독립된 Git 유틸리티다. 호환성을 위해 Oracle 요청에 바로
사용할 수 있는 `oracle-prompt.md`도 함께 생성한다.

## Command

```bash
bash /home/user01/.codex/skills/repo-snapshot/repo-snapshot.sh [SOURCE_PATH] [--task "검토 요청"] [--slug NAME]
```

- `SOURCE_PATH` 생략 시 현재 디렉터리의 git root 사용
- `--slug` 생략 시 레포 디렉터리명으로 `snapshot/<slug>` 생성
- `--task`는 `oracle-prompt.md`에 포함

## Remote

- 저장소: `https://github.com/lleullus/testbyrepo`
- `main`: placeholder만 유지
- 레포별 브랜치: `snapshot/<repo-slug>`
- 같은 slug 재실행 시 fast-forward일 때만 해당 브랜치를 갱신하며, 분기/재작성 상황은 충돌로 반환
- 검토에는 브랜치 URL보다 **commit SHA URL** 사용

## Auth

- 토큰 파일: `/home/user01/.config/repo-snapshot/token` (mode 600, Git 저장소 외부)
- 환경변수 우선:
  - `REPO_SNAPSHOT_TOKEN_FILE`
  - `REPO_SNAPSHOT_REMOTE`
  - `REPO_SNAPSHOT_WEB`
  - `REPO_SNAPSHOT_BASE`
- 토큰을 SKILL.md, 프롬프트, `snapshot.json`, git remote config에 쓰지 않는다
- 토큰을 통합 스킬 Git 저장소 안에 복사하거나 커밋하지 않는다
- push URL에만 일회성으로 사용한다

## Behavior

1. 원본 레포를 실행별 `/tmp/oracle-snapshots/<slug>.run.*/repo`에 full 복사 (`.git` 포함, 제외 없음)
2. uncommitted/untracked 변경이 있으면 복사본에만 임시 커밋
3. 복사본 `origin`을 snapshot 원격으로 교체
4. 원본에는 절대 push하지 않음
5. 원격에 `main`이 없으면 placeholder README로 `main` 생성
6. `snapshot/<slug>`에 force 없이 push하며 non-fast-forward는 거부
7. 메타데이터 기록

## Local Layout

```text
/tmp/oracle-snapshots/<slug>.run.<unique>/
├── repo/
├── snapshot.json
└── oracle-prompt.md
```

`/tmp/oracle-snapshots` 상위 경로는 기존 호출자 호환을 위해 유지하되 각 실행은 독립 디렉터리를 사용하며,
Oracle 의존성을 뜻하지 않는다.

## Output

`snapshot.json` 예:

```json
{
  "snapshotUrl": "https://github.com/lleullus/testbyrepo",
  "commitUrl": "https://github.com/lleullus/testbyrepo/commit/<sha>",
  "commitSha": "<sha>",
  "branch": "snapshot/<slug>",
  "branchUrl": "https://github.com/lleullus/testbyrepo/tree/snapshot/<slug>",
  "sourcePath": "/path/to/original",
  "sourceHead": "<original-head>",
  "sourceBranch": "<original-branch>",
  "createdAt": "ISO-8601",
  "status": "published"
}
```

`oracle-prompt.md`는 Oracle을 사용할 때 그대로 붙여 넣을 수 있는 선택적 문구다.

## Agent Rules

- 사용자가 `repo-snapshot` / `레포 스냅샷`을 요청하면 이 스크립트를 실행한다
- 실행 후 commit URL, `snapshot.json`, `oracle-prompt.md` 경로를 알려준다
- Oracle 호출은 사용자가 요청하기 전까지 하지 않는다
- 원본 레포에서 `git push`하지 않는다
- 토큰 파일 내용을 출력하거나 채팅에 반복하지 않는다


이 도구는 IIS 내부 fixed artifact store가 아니다. Product Thesis/Scope/Assurance의 executor-owned snapshot 확보에는 `iis_artifacts`를 사용하며, 별도 Git snapshot 생성은 사용자가 명시적으로 요청한 경우에만 이 스킬이 수행한다.
