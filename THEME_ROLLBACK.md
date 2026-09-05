# ttyd 테마 변경 및 즉시 원복 가이드 (THEME_ROLLBACK.md)

이 문서는 ttyd 웹 터미널의 **VS Code Light Modern** 테마 적용 내역 및 다크 테마로의 **즉시 무중단 원복 방법**을 설명합니다.

---

## 1. 1초 즉시 원복 (무중단, 쉘/OMP 세션 유지)

ttyd 데몬 재시작 없이 브라우저 새로고침만으로 즉시 기존 다크 테마로 되돌릴 수 있습니다.

```bash
# 다크 테마 백업본으로 복원
cp -p ~/.local/share/webterm/index.html.backup-dark-theme ~/.local/share/webterm/index.html
```
- 복원 후 열려있는 브라우저 창을 **새로고침(F5 또는 Ctrl+R)** 하면 즉시 다크 테마가 적용됩니다.
- 실행 중인 ttyd 프로세스 및 터미널 작업 세션은 전혀 끊기지 않습니다.

---

## 2. 다시 VS Code Light Modern 테마로 복원하려면

다크 테마로 원복한 뒤 다시 라이트 모던 테마를 적용하고 싶을 때:

```bash
# 라이트 모던 빌드본으로 복원
cp -p /home/user01/project/webterm/ttyd-1.7.7/staging/index.html ~/.local/share/webterm/index.html
```

---

## 3. 소스코드 레벨 원복 (git revert 및 재빌드)

소스코드(`html/src/components/app.tsx`, `html/src/style/index.scss`)까지 완전히 이전 상태로 되돌리려면:

```bash
cd /home/user01/project/webterm/ttyd-1.7.7

# 1. git 변경 사항 되돌리기 (커밋 revert 또는 checkout)
git revert HEAD --no-edit

# 2. 프론트엔드 재빌드
cd html && yarn build

# 3. 배포 파일 교체
cp dist/inline.html ~/.local/share/webterm/index.html
```

---

## 4. 백업 파일 및 해시 정보

- **기존 다크 테마 백업 파일**:
  - `~/.local/share/webterm/index.html.backup-dark-theme`
  - `~/.local/share/webterm/index.html.backup-dark-theme-20260905`
  - SHA-256: `97711f1863e2e2098fad22dad44396f374ccf785b08c32788cec295b84a4ed54`

- **새 Light Modern 배포 파일**:
  - `~/.local/share/webterm/index.html`
  - `~/project/webterm/ttyd-1.7.7/staging/index.html`
  - `~/project/webterm/ttyd-1.7.7/html/dist/inline.html`
  - SHA-256: `cf16ad0d239f6ee6fdf3621b54a19b61ef32349e6897a14f41197769360ca8cc`
