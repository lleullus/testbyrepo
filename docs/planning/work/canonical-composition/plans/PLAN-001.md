# PLAN-001 — BLOCK-03 Canonical Composition 실행 방법

Plan-Type: Scope execution method  
Project-Root: `/home/user01/project/comic_new`  
Scope: `/home/user01/project/comic_new/docs/planning/work/canonical-composition/SCOPE.md`  
Scope-SHA256: `1cd7faa9c19b1e102157ae18d806e1d905cdbc8000032e103c9ac6c83a43e8b5`  
Selected-Transition: `BASELINE-001 / BLOCK-03`  
Planner-Mode: `SUBAGENT`  
Planner-Model: `GPT-5.6 Sol High`

## 1. 권위, 현재성, 시작 범위

### 1.1 결속 원본과 선행 증거

- **[EXISTING] Product Authority** — `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md`, revision `THESIS-001`, SHA-256 `74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63`. 전체 원문에서 제품 목적, 5-Truth Chain, exactly-five 경계, INV-3/4/5/6/8, Canonical Review Artifact, downstream no-reflow 및 authoritative readback을 직접 확인했다.
- **[EXISTING] Scope** — 위 exact Scope는 `Schema: iis-scope/v1`, `Status: ready`, `Open Decisions: None`이다. canonical validator `/home/user01/.omp/agent/skills/scope-shaper/tools/validate_scope.py --json <absolute-scope>`의 계획 전 실제 결과가 exact Project Root, 위 Thesis와 아래 Transition 경로/digest 및 `status: ready`를 반환했다.
- **[EXISTING] Transition Authority** — `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md`, SHA-256 `5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c`, `Status: APPROVED`. 이 Plan은 `BLOCK-03`의 Entry, Required Construction Boundary, Exit 1–13, INV-3/4/5/6/8, PATH-5/7/11/13, Review Artifact Registration atomic boundary와 Safe Continuation/Safe Abort만 적용한다. `BLOCK-04/05`를 시작하지 않는다.
- **[EXISTING] 완료 선행 Scope** — BLOCK-01 Scope `/home/user01/project/comic_new/docs/planning/work/transactional-core/SCOPE.md`는 `Status: done`, SHA-256 `2ea75fa8ab21733b0baaf5f84d3505a2eec197e0d74dbd98cabfe9ad564f7a02`; BLOCK-02 Scope `/home/user01/project/comic_new/docs/planning/work/unified-generation/SCOPE.md`는 `Status: done`, SHA-256 `695beafd9a306c9426b7bb4a91004e5fb8b3efe174a9cb9afa6988d0b4dc316b`이다.
- **[EXISTING] BLOCK-02 handoff evidence** — verifier `/home/user01/tmp/comic-new-block02-verification-r3.md`, SHA-256 `1c2f3bd4abab70b0e8b9f59e28c00c6f1bb5d791350ab0176ef73d06579733ac`; Coverage `/home/user01/tmp/comic-new-block02-coverage.md`, SHA-256 `3e3790e5e0d18a002beb695f68f78617a3f60d01b92af2bd64e26617b9ab8e3e`. 두 원본은 BLOCK-02 A–G/Exit 1–16, 실제 local subprocess 경계, commit-time currency, STOP/restart, exact-five equality와 no-material-finding을 기록한다. 실제 ima2/provider 성공은 권한 경계상 `INCONCLUSIVE`이고 이 Plan은 이를 compositor 증거나 provider 성공으로 확장하지 않는다.
- **[EXISTING] Repository investigation** — 별도 immutable investigation artifact는 `None supplied`이다. 이 Plan의 코딩 근거는 §2에 적은 현재 source bytes 직접 판독이다.
- **[EXISTING] Material concurrency counterexample and current uncommitted evidence** — 현재 uncommitted `src/comic_new/composition.py` SHA-256 `5dee0c1a30a3f4e3b7501c819c9f7219069d49bdb0a5bcd9e3c2cf548d1402db`, `src/comic_new/composition_service.py` SHA-256 `d4135454b5dcaaecd817b0f72e1b7eac075d1cca98c30de7bfca9df04121b8b2` 및 `agent://ImplementGeminiBlock03`/`history://ImplementGeminiBlock03`는 수용된 구현이 아니라 방법을 반박·구체화하는 증거다. Main이 두 independent service와 실제 filesystem/SQLite registration을 barrier로 제어한 반례에서 A가 final 생성 후 registration 전에 멈추고 B가 shared final을 채택했으며, A의 attributable Conflict 뒤 fresh DB snapshot에 row가 없다는 이유로 A가 final을 삭제한 다음 B가 실제 registration을 commit했다. 최종 authoritative state는 `review_artifacts` row 1개, artifact file 0개, `registered_file_exists=false`였다. 이는 “fresh snapshot 후 owned final unlink”가 아직 DB row가 없는 경쟁자의 adoption을 관찰할 수 없는 TOCTOU임을 확정한다.
- **[EXISTING, STALE] Prior Plan Review** — `/home/user01/tmp/comic-new-block03-plan-review.json`, SHA-256 `481496f986c85485788a397e1548d35b704598e2f54926f3820560fc013faa2a`의 `ADMIT`은 이전 Plan SHA-256 `080b0c526dd243e7300985eafaf91ba2b3d696f89319c05f3c809e276fb5a358`에만 결속되며 위 반례와 이 개정 뒤에는 stale이다. 구현 재개 권위가 아니며, 새 review target은 Main 소유 `/home/user01/tmp/comic-new-block03-plan-review-r2.json`이다.

### 1.2 획득할 결과와 정확한 시작 범위

정확히 다섯 Current realization과 하나의 authoritative normalized composition을 읽어, 서버의 한 PIL 구현이 고정 canonical surface에 cut `1..5`, gap, bubble shape/geometry/text/typography를 전부 그린다. 결과는 완전한 PNG bytes 한 개이며, content hash로 안정된 `artifact_id`와 immutable path를 정하고 기존 `TransactionalStore.register_review_artifact(...)` transaction에 composition revision과 five-cut closure를 등록한다. review/export/release의 유일한 reader는 그 DB identity에서 artifact bytes를 읽고 검증하는 서비스여야 하며 별도 reflow/layout은 없다.

독립 Plan Review가 이 개정 Plan의 exact bytes를 새로 `ADMIT`하고 권위/currentness가 유지된 뒤에만 구현을 재개할 수 있다. 이전 review의 start scope는 이 개정에 권위를 주지 않는다. 새 review가 허용할 수 있는 범위는 기존 BLOCK-03 로컬 범위 안의 다음 correction 및 완결뿐이다.

1. canonical composition schema/parser와 단일 PIL renderer에서 JSON number/lowercase hash 및 exact-five closure validation을 엄격히 하는 일;
2. current snapshot → source byte 검증 → materialization → 기존 registration transaction → authoritative readback service에서 safe final retention, exclusive hard-link publication, exact duplicate convergence/currentness/reader closure를 구현하는 일;
3. 기존 `accept_composition` canonical clean cutover와 package export를 유지·수정하고, 현재 test callsite 및 BLOCK-03 회귀를 이 개정 계약과 맞추는 일;
4. 실제 local PIL/filesystem/SQLite에서 controlled concurrency 반례를 포함한 §7 self-check를 수행하는 일.

CLI 명령, UI, HTTP/SSE, ReviewModal, release authorization 실행, PNG export, Blogger, provider 호출은 시작 범위가 아니다.

### 1.3 보존/비범위

- existing exact-five cut identity, generation queue/runner, realization commit gate, SQLite authority와 `register_review_artifact`의 transaction 의미를 교체하지 않는다.
- schema v2의 `review_artifacts`/`artifact_cuts`를 그대로 사용한다. 새 ORM, renderer interface hierarchy, plugin, layout DSL, JSON/file authority, app lock 또는 migration을 추가하지 않는다.
- canonical source file을 수정·삭제·덮어쓰지 않는다. 4컷 preview, corrupt cut skip, font fallback, text truncation/auto-shrink로 성공을 꾸미지 않는다.
- 브라우저 projection과 downstream delivery는 이 Plan에서 구현하거나 실행하지 않는다. 이후 owner는 immutable artifact reader만 호출하고 조판을 복제하지 않는다.

## 2. Grounding ledger

### 2.1 EXISTING — admitted-method 시작 기준과 현재 반례/source evidence
아래 1–10은 uncommitted BLOCK-03 구현 전 current commit `6ad1a5d296ab54e62b68907fbad875a7802d4499`에서 직접 판독한 시작 기준이다. 이후 uncommitted 여섯 product/test path는 수용된 새 authority가 아니며, 이 개정은 사용자 지시로 허용된 현재 `composition.py`/`composition_service.py`와 §1.1 반례만 correction evidence로 사용한다.

1. `pyproject.toml:5-18`은 Python `>=3.10`, `Pillow>=10.0.0`, console entry `comic-new = comic_new.cli:main`, `schema.sql`/migration package data를 선언한다. SHA-256은 `260fe8888591e21700b84881f142ef275d9ece01e0a3eda70401526865c4cf55`이다.
2. `src/comic_new/schema.sql:26-38`의 `cuts`는 `desired_revision`, `realized_revision`, `realized_asset_id`, `realized_asset_path`, `realized_content_hash`를 소유한다. `:48-53`의 singleton `composition`은 `revision/state_json/updated_at`, `:102-115`의 `review_artifacts`/`artifact_cuts`는 `artifact_id`, unique `content_hash`, `composition_revision`과 five `(cut_id, realized_revision, asset_id)` closure를 소유한다. 현재 SHA-256은 `ec382f5131a0b6fbd0c49f46de08f73d52f41f929f5a1bc08db06737e32e8149`이다.
3. `src/comic_new/store.py:307-540`의 `snapshot()`은 한 DEFERRED read transaction에서 cut을 `cut_id` 순으로 읽고, 오직 non-null `desired_revision == realized_revision`으로 `CURRENT`와 exact-five `COMPLETE`를 계산한다. 같은 snapshot이 composition state/revision, realization path/hash/asset identity와 registered artifact closure를 분리해 반환한다.
4. `store.py:652-691`의 현 composition writer `accept_composition(expected_authority_revision, expected_composition_revision, state)`는 `BEGIN IMMEDIATE`, 두 revision compare-and-swap, composition `+1`, active authorization revoke, global authority `+1`을 한 transaction에 묶는다. 그러나 현재는 임의 dict/string을 JSON으로 저장하므로 BLOCK-03 canonical schema를 강제하지 않는다.
5. `store.py:988-1081`의 유일한 production realization writer `commit_candidate(...)`는 current desired revision을 commit 때 재검사하고 `assets/realizations/cut-<id>/rev-<revision>-<job>.png`로 immutable promotion한 뒤 `cuts.realized_*`를 쓴다. `src/comic_new/generation.py:791-824`가 Pillow decode/hash 후 이 writer를 호출하며, stale/cancelled/invalid candidate는 canonical realization을 쓰지 않는다. 두 파일 SHA-256은 각각 `c52da93571b35c0ec70b3a4bf20a940c144ae564db0480da6a002df55f1e1b14`, `a3fb34c3a503d42c819e27b2dd12471aff989671e8f3bb17600d79db281bcd91`이다.
6. `store.py:1242-1313`의 `register_review_artifact(...)`는 global CAS, current composition revision, 다섯 cut 각각의 current equality, supplied `(cut_id, realized_revision, asset_id)` closure 일치를 같은 transaction에서 검사한 뒤 두 artifact table과 global authority revision을 commit한다. 이 transaction과 public signature를 보존한다. 이 API는 bytes를 만들거나 path/hash를 다시 읽지 않으므로 compositor service가 그 전후 filesystem 경계를 책임져야 한다.
7. `store.py:1315-1385`의 `authorize_release`와 `:1387-1451`의 delivery start는 registered artifact의 composition/five-cut closure를 현재 state와 다시 대조한다. 이는 이후 BLOCK-05 reader이고 이 Plan의 writer가 아니다.
8. 현재 production artifact/composition callsite는 없다. `src/comic_new/cli.py:22-158`에는 init/snapshot/generation 명령만 있고 materialize 명령은 없다. `src/comic_new/__init__.py:3-49`는 store/generation surface만 export한다. SHA-256은 각각 `80bcec5656dac158f4cfeda9ad8463b32d3f403b53eaf0b78704dc6207cc8ae2`, `4206736b1d103e9bda30e7f65dc9f7974354ef7582248c0fb5a35f3031648f5c`이다.
9. 직접 metadata API를 호출하는 현재 callsite는 `tests/test_transactional_core.py:302-357,488-545,642-682`뿐이다. 이 중 arbitrary composition fixtures와 bytes 없는 artifact registration은 BLOCK-01 transaction 경계 회귀이지 BLOCK-03 pixel 성공 증거가 아니다. `tests/test_generation.py:147-222,289-369`은 실제 generated PNG path/decode/hash와 stale overwrite 방지를 관찰하므로 BLOCK-03 source fixture/readback 패턴으로 재사용한다.
10. 계획 시 host는 Python `3.12.3`, SQLite `3.45.1`, Pillow `12.2.0`, Pillow RAQM `True`다. `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf`는 readable하고 SHA-256 `acb6440a713d880a13a21b468ba7cd43f5a2b2934972e51be791c880730777b8`; Pillow로 `한글 漫画 ABC`를 실제 측정할 수 있었다. 이는 현재 계획 host의 시작 premise이지 다른 verifier/deploy host의 font 가용성 또는 cross-version byte identity 증거가 아니다.

11. 현재 uncommitted `composition.py:68-98,132-135,362-414`는 percentage에 numeric string을 받아 float로 바꾸고, uppercase font hash를 lowercase로 정규화하며, direct renderer가 cut revision/asset/hash를 required exact closure로 거절하지 않는다. 이는 §3.2/§4.1에서 입력 및 direct-render boundary를 더 엄격히 명시해야 하는 현재 source evidence다.
12. 현재 uncommitted `composition_service.py:217-230,257-284,324-345,361-366`는 hard-link 실패 시 `Path.replace` fallback을 두고, attributable registration failure에서 newly-created final을 삭제하며, duplicate registration branch를 `pass`로 통과하고, post-registration currentness를 “각 cut이 Current인가”만으로 보며, embedded metadata는 DB composition revision만 비교한다. Main의 barrier 반례는 그 cleanup이 실제 DB→missing bytes를 만든 것을 관찰했고 나머지 source reach는 exact convergence/currentness/readback 요구가 빠져 있음을 보여 준다. 이 current source는 완료/검증 증거가 아니며 §5–7 correction target만 정한다.

### 2.2 PROPOSED — 최소 변경 구조

1. `src/comic_new/composition.py` 하나가 canonical constants/schema normalization, percentage→pixel math, five-cut contain fitting, bubble/text rendering과 deterministic PNG encoding을 소유한다. generic renderer base class나 strategy registry는 없다.
2. `src/comic_new/composition_service.py` 하나가 `TransactionalStore`와 filesystem의 effect ordering, cleanup, registration/fresh readback 및 immutable artifact reader를 소유한다. `composition.py`는 store를 import하지 않아 `store.py`가 normalizer를 재사용해도 cycle이 없다.
3. `store.py.accept_composition`은 dict만 받고 `composition.normalize_state(...)` 결과를 canonical UTF-8 JSON(`sort_keys=True`, compact separators, no NaN/Infinity)으로 저장한다. 기존 CAS와 authorization revocation transaction은 그대로 둔다. raw invalid composition을 받아들이는 두 번째 writer는 남기지 않는다.
4. `__init__.py`는 `CompositionService`, `MaterializedArtifact`와 caller가 분기해야 하는 composition validation/materialization errors만 export한다. `cli.py`, `schema.sql`, migration, generation owner는 변경하지 않는다.
5. `tests/test_transactional_core.py`의 임의 composition fixture를 유효 canonical fixture로 이관하고, 신규 `tests/test_composition.py`에는 실제 Pillow bytes/SQLite/filesystem에서만 판별되는 exact-five/current/immutability/rollback/race 회귀를 둔다. mock renderer/store와 canned artifact bytes는 acceptance 증거가 아니다.

### 2.3 UNRESOLVED / evidence limits

- **제품 의미 미결정은 없음.** Scope와 Thesis의 Open Decisions는 `None`; §3–5의 surface 크기, fit, rounding, schema와 render 규칙은 이 Plan이 선택한 명시적 기술 방법이며 숨은 fallback/default가 아니다. 이를 사용자 선택으로 가장하지 않는다.
- **검증 host의 font/Pillow runtime은 조건부**다. 계획 host에서는 위 exact font/Pillow를 관찰했지만 구현/검증 시 동일 path/bytes 또는 caller가 명시한 다른 readable font bytes가 필요하다. font가 없거나 hash가 composition과 다르면 text boundary는 `INCONCLUSIVE`가 아니라 materialization의 명시적 실패이고, 환경 부재 시 verifier 전체 text 세부 판정만 `INCONCLUSIVE`로 보존한다.
- **Cross-runtime byte-for-byte 동일성은 주장하지 않는다.** 같은 normalized input, exact source/font bytes, renderer contract version 및 동일 Pillow/FreeType/RAQM runtime에서 deterministic output을 요구한다. 다른 Pillow/FreeType/RAQM 버전의 rasterization 동일성은 관찰되지 않았고 Scope도 이를 외부 약속으로 만들지 않는다. 생성된 artifact 자체의 bytes/hash는 runtime과 무관하게 이후 불변이어야 한다.
- ReviewModal, PNG/Blogger reader의 실제 integration은 BLOCK-04/05 소유다. BLOCK-03은 그들이 reflow 없이 호출할 identity→validated bytes reader를 제공하고 직접 UI/release 성공을 주장하지 않는다.

## 3. Canonical composition schema와 고정 renderer contract

### 3.1 Surface, cut order, gap, fit

- canonical surface는 **RGB 1024 × 7680 px**로 고정한다. 현재 유일한 generation path가 `generation.py:469-488`에서 각 realization을 `1024x1536`으로 요청하므로 gap 0일 때 다섯 source의 native 2:3 slot이 세로로 정확히 이어지는 가장 작은 grounded surface다. canvas/gap 배경은 opaque white다.
- fixed order는 DB `cut_id` 오름차순 `1,2,3,4,5`뿐이다. caller가 순서나 subset을 제공하지 않는다.
- `gap_px`는 authoritative state에 명시된 non-negative integer다. 숨은 default는 없다. `usable_height = 7680 - 4 * gap_px`이며 `usable_height >= 5`가 아니면 거절한다.
- cut `i`(zero-based)의 vertical slot은 `y0 = floor(i * usable_height / 5) + i * gap_px`, `y1 = floor((i+1) * usable_height / 5) + i * gap_px`로 정한다. 따라서 remainder pixel은 정수 경계식으로 한 번만 배분되고 다섯 slot + 네 gap이 정확히 7680 px를 덮는다.
- source는 orientation을 재해석하거나 crop하지 않고 slot 안에 **contain**한다. `scale = min(slot_width/source_width, slot_height/source_height)`; resized width/height는 positive half-up integer이고 LANCZOS 한 번으로 resize한 뒤 slot 중앙에 배치한다. 홀수 여백의 남는 1 px는 right/bottom에 둔다. 투명 source는 white에 합성한다. source 전체가 보존되며 cover/content crop, stretch, per-cut ad-hoc policy는 없다.

### 3.2 Authoritative state JSON

`composition.state_json`의 accepted v1 shape는 아래 하나다. 모든 필드는 명시적으로 필요하고 unknown key는 거절하여 renderer와 향후 browser projection이 같은 계약을 공유하게 한다.

```json
{
  "schema_version": 1,
  "gap_px": 24,
  "font_sha256": "<64 lowercase hex>",
  "bubbles": [
    {
      "bubble_id": "bubble-1",
      "cut_id": 1,
      "shape": "ellipse",
      "x_pct": 10.0,
      "y_pct": 4.0,
      "w_pct": 30.0,
      "h_pct": 8.0,
      "text": "대사",
      "font_size_pct": 2.4,
      "line_spacing_pct": 25.0,
      "text_align": "center",
      "text_rgba": "#000000FF",
      "fill_rgba": "#FFFFFFFF",
      "outline_rgba": "#000000FF",
      "outline_width_pct": 0.2,
      "padding_pct": 8.0
    }
  ]
}
```

- `bubble_id`는 state 안에서 non-empty unique string, `cut_id`는 `1..5`이며 association만 나타낸다. geometry 기준은 cut image나 viewport가 아니라 전체 canonical surface다. list order가 back-to-front paint order다.
- `shape`는 `ellipse` 또는 `rounded_rectangle` 두 값만 지원한다. ellipse는 pixel bounding box에 내접한다. rounded rectangle의 corner radius는 `min(pixel_width, pixel_height) / 8`을 half-up한 고정 renderer rule이다. tail, SVG path, plugin shape는 이 Scope에 없다.
- percentage 필드는 bool을 제외한 **JSON number**여야 하며 numeric string은 거절한다. 값은 finite이고 소수점 이하 최대 4자리다. `x_pct/y_pct >= 0`, `w_pct/h_pct > 0`, `x_pct+w_pct <= 100`, `y_pct+h_pct <= 100`; `font_size_pct > 0`, `outline_width_pct >= 0`, `0 <= padding_pct < 50`, `line_spacing_pct >= 0`를 강제한다. `font_sha256`은 입력 시점부터 exact `[0-9a-f]{64}`인 nonempty lowercase hex여야 하며 uppercase를 lowercase로 고쳐 받아들이지 않는다. RGBA는 exact `#RRGGBBAA`; align은 `left|center|right`다. normalize 후에도 모든 값은 explicit canonical keys로 남고 fallback style을 주입하지 않는다.
- geometry/text/style/gap을 고친다는 명분으로 renderer가 DB state를 수정하지 않는다. invalid accepted legacy state는 materialization에서 정직하게 실패하며, 사용자가 유효한 새 state를 `accept_composition`으로 수용해야 한다.

### 3.3 Percentage math와 rounding

모든 입력 number를 `Decimal(str(value))`로 바꾸어 binary-float 누적을 피한다. surface edge 변환은 `round_half_up(pct * axis_px / 100)` 하나만 사용한다. bubble은 `left = px(x_pct)`, `top = px(y_pct)`, `right = px(x_pct+w_pct)`, `bottom = px(y_pct+h_pct)`로 edge를 각각 계산한다. width/height를 별도로 반올림해 edge가 달라지는 두 번째 공식은 두지 않는다. 결과 box가 surface 안이고 positive pixel area인지 재확인한다.

동일 normalized state를 1024×7680 artifact와 임의 verification scale(예: 512×3840)에서 순수 geometry helper로 계산하면 각 edge의 `pixel/axis` 비율이 half-pixel 오차 안에서 같아야 한다. production artifact는 항상 고정 surface이고 viewport는 이 함수의 입력이 아니다.

### 3.4 Font, wrapping, typography와 unreadable text

- `CompositionService(store, font_path)`는 **한 개의 explicit font path**를 요구한다. search path, OS family fallback, `ImageFont.load_default()`, missing-glyph fallback chain은 없다. service가 font bytes를 한 번 읽어 SHA-256을 계산하고 authoritative `font_sha256`과 exact match할 때만 진행한다. render 동안 path replacement가 결과를 바꾸지 않도록 그 bytes로 FreeType font instances를 만든다.
- `font_size_px = round_half_up(font_size_pct * 1024 / 100)`, outline width도 surface width 기준 half-up이다. 같은 size의 `ImageFont.truetype(BytesIO(font_bytes), size, layout_engine=ImageFont.Layout.RAQM)`는 invocation-local cache로만 재사용하며 authority가 아니다. RAQM layout engine을 만들 수 없거나 non-whitespace glyph mask/measurement가 비어 있으면 실패하며 다른 engine으로 fallback하지 않는다.
- bubble padding은 `round_half_up(padding_pct * min(box_width, box_height) / 100)`이고 content box가 positive가 아니면 실패한다. explicit `\n`은 paragraph/blank-line boundary로 보존한다. 각 paragraph는 whitespace-delimited token을 greedy append하여 `draw.textlength`가 content width를 넘기기 직전에 wrap한다. 한 token 자체가 넘으면 Unicode code point 단위로 hard-wrap한다. 줄 높이는 exact font bounding box, additional leading은 `round_half_up(line_spacing_pct * font_size_px / 100)`다.
- 각 line x는 explicit `text_align`, 전체 block y는 content box 중앙으로 정한다. measure와 draw는 같은 font, stroke 0, 동일 integer positions를 쓴다. 전체 block이 content box 높이를 넘거나 hard-wrap 후 한 code point도 width에 못 들어가면 **materialization 전체 실패**다. auto-shrink, ellipsis, clipping, silent omission은 없다.
- bubble fill/outline을 먼저 그리고 text를 마지막에 그린다. final text truth는 이 PIL pixel output이며 DOM/export/Blogger에 line list나 재flow instruction을 제공하지 않는다.

### 3.5 Deterministic artifact bytes와 self-description

- renderer는 source/font bytes를 고정한 뒤 RGBA에서 모든 compositing을 끝내고 opaque RGB PNG로 저장한다. Pillow `optimize=False`, fixed `compress_level=9`, no timestamp를 사용한다.
- PNG text metadata 한 항목 `comic_new_closure`에 compact sorted canonical JSON을 넣는다: renderer contract `canonical-composition/v1`, surface dimensions, exact normalized state, composition revision, Pillow version, font hash, 그리고 cut `1..5` 각각의 desired revision, realized revision, asset id, source content hash. metadata도 deterministic하다.
- composition revision/closure가 bytes에 포함되므로 서로 다른 accepted revision이 우연히 같은 visible pixels를 내도 기존 `UNIQUE review_artifacts.content_hash`와 충돌하지 않는다. 같은 exact closure/runtime을 두 번 render하면 PNG bytes와 SHA-256이 같아야 한다.
- `content_hash = sha256(full_png_bytes)`이며 `artifact_id = "artifact-" + content_hash`; final relative path는 `assets/review-artifacts/<artifact_id>.png`다. path는 current composition 같은 mutable 이름을 포함하지 않고 overwrite하지 않는다.

## 4. Public interfaces와 writer/reader ownership

### 4.1 Direct module functions

`composition.py`의 concrete surface는 다음 의미만 제공한다. dataclass 이름/private helper 배치는 구현자 재량이다.

- `normalize_state(state: dict) -> dict` — §3.2의 유일한 canonical dict를 반환하거나 `CompositionValidationError`.
- `render_canonical(state, composition_revision, cuts, font_bytes) -> RenderedArtifactBytes` — `composition_revision`은 bool이 아닌 positive integer이고 `cuts` key/order는 정확히 `1..5`여야 한다. 다섯 cut 모두 required `desired_revision`과 `realized_revision`이 bool이 아닌 positive integer로 서로 같고, required `realized_asset_id`가 nonempty string이며, required `realized_content_hash`가 exact lowercase `[0-9a-f]{64}`이고 actual `source_bytes` SHA-256과 같아야 한다. missing/falsey 값을 허용하거나 `asset_id` alias/fallback으로 closure를 보정하지 않는다. 각 source bytes/hash/full decode가 유효한지 다시 검사하고 embedded closure에는 검증된 값을 `(cut_id, desired_revision, realized_revision, asset_id, source_content_hash)`로 기록해 §3 PNG bytes/hash를 반환한다. 네 컷 이하 또는 duplicate/extra cut은 render 전에 실패한다.
- `artifact_path(project_dir, artifact_id) -> Path` — exact immutable relative path 밖으로 나갈 수 없는 content-hash id만 허용한다.

### 4.2 CompositionService

- `materialize(expected_authority_revision: int, expected_composition_revision: int) -> MaterializedArtifact`
  1. fresh `store.snapshot()`에서 caller의 두 expected revision을 대조한다.
  2. `cuts`가 정확히 ordered `[1..5]`, 모두 `CURRENT`, `realization_complete.complete is True`이고, 다섯 각각의 desired/realized revision이 positive/equal하며 realized asset id/path와 lowercase exact content hash가 nonempty인지 검사한다.
  3. composition을 normalize하고 font bytes/hash를 고정한다. numeric string percentage나 uppercase/non-hex font hash는 이 경계에서 실패한다.
  4. source 5개의 actual bytes를 한 번만 읽고 required DB `realized_content_hash`와 대조한 뒤 실제 PNG full decode/positive dimensions를 모두 성공시킨다. 하나라도 실패하면 staging/final/DB artifact는 0개다.
  5. render/save/validate/register/readback은 §5 순서를 따른다.
- `read_artifact(artifact_id: str) -> MaterializedArtifact` — fresh snapshot의 `review_artifacts` row를 먼저 찾은 뒤 그 row의 ordered `artifact_cuts` 다섯 개를 읽고 derived final path를 연다. requested/row `artifact_id`가 `"artifact-" + content_hash`와 같고 actual full-file SHA-256이 row `content_hash`와 같아야 한다. Pillow full decode는 exact RGB PNG 1024×7680이어야 한다. embedded renderer contract/dimensions가 §3과 같고, embedded normalized state가 strict normalization을 다시 통과하며, embedded font hash가 state의 exact lowercase `font_sha256`과 같아야 한다. embedded composition revision은 row와 같고, embedded cuts는 ordered `1..5`이며 각 `(cut_id, realized_revision, asset_id)`가 ordered DB `artifact_cuts`와 exact 같고, 각 desired revision은 같은 positive realized revision, 각 source content hash는 required lowercase exact hex여야 한다. 한 필드라도 다르면 실패한다. directory file presence, unregistered exact-hash orphan 또는 caller hash만으로 등록을 창조하거나 authoritative truth로 취급하지 않는다.

`MaterializedArtifact`는 `artifact_id`, `content_hash`, absolute path, width/height, composition revision, ordered five closure를 담는다. downstream은 `artifact_id`를 이 reader에 넘겨 bytes를 얻는다. typography model이나 bubble boxes를 export API로 넘기지 않는다.

### 4.3 Current writers/readers after cutover

| Truth/effect | Create/update owner | Authoritative deciding read | Removal/reset |
|---|---|---|---|
| composition state/revision | 기존 `accept_composition`, 이제 `normalize_state` 선검증 후 기존 CAS/revoke transaction | fresh `snapshot().composition` | delete/rollback 없음; 새 accepted revision만 가능 |
| realization identity/path/hash | 기존 generation `commit_candidate`만 | fresh snapshot + compositor actual source hash/decode | compositor는 수정/삭제하지 않음 |
| in-memory decoded cuts/font | materialize invocation | renderer only | invocation 종료 시 해제; authority 아님 |
| staging PNG | CompositionService invocation의 private random path | post-save full decode/hash | promotion 시 hard-link source로 사용한 뒤 또는 모든 handled failure에서 exact private staging path만 unlink |
| immutable final artifact file | validated staging에서 same-filesystem hard-link로 exclusive destination creation; 이미 존재하면 exact bytes/metadata 검증 후 공유 채택 | `read_artifact`의 DB row + actual bytes/hash/decode/metadata | final name으로 publish된 뒤에는 이 Scope의 어떤 registration 성공/실패/경합/cleanup 경로도 삭제·overwrite하지 않음; 미등록 exact-hash file은 non-authoritative safe residue |
| artifact registration | 기존 `register_review_artifact` transaction만 | fresh snapshot `review_artifacts`/`artifact_cuts` | row 삭제/update 없음 |
| review/export/release source | 이후 BLOCK-04/05가 `artifact_id`로 `read_artifact` 호출 | 동일 bytes/hash/closure | reflow/crop/reorder 없음 |

CLI는 BLOCK-03 acceptance에 필요하지 않고 현재 official caller도 없으므로 추가하지 않는다. BLOCK-04 server가 서비스 API를 직접 호출할 때까지 CLI surface를 넓히지 않는다.

## 5. Filesystem–SQLite ordering, rollback과 races

### 5.1 Normal path

1. **Authoritative capture** — one fresh snapshot에서 global revision `R`, positive composition revision `C`, normalized state와 ordered five closure `(cut_id, desired_revision, realized_revision, asset_id, source_content_hash)`를 잡는다. snapshot 밖에서 caller-supplied asset list를 섞지 않는다.
2. **Preflight all inputs** — §4.2의 strict number/hash/identity/currentness 조건, font와 다섯 source의 bytes/hash/full decode를 모두 완료한다. 실패 시 staging/final/DB effect가 없다.
3. **Render private staging** — project 내부 `.composition-staging/<random-id>/candidate.png`에 invocation-private exclusive create하고 deterministic bytes를 쓴다. final과 같은 filesystem에 두어 hard-link destination creation이 atomic하도록 한다.
4. **Validate candidate** — staging을 별도 open해 non-empty, exact PNG/RGB/1024×7680, full load, exact embedded closure를 확인하고 file bytes SHA-256을 재계산한다. in-memory bytes/hash/metadata와 하나라도 다르면 실패한다.
5. **Exclusive no-overwrite publish** — existence precheck에 의존하지 않고 validated staging을 source로 `os.link(staging, final)` 같은 same-filesystem hard-link/exclusive destination creation을 한 번 시도한다. 성공하면 immutable final name이 publish된 것이다. `FileExistsError`이면 기존 final을 shared candidate로 채택하되 그 full bytes/hash/decode/metadata가 staging 및 rendered result와 byte-for-byte exact인지 확인한다. hard-link가 unsupported이거나 다른 destination-create 오류이면 정직하게 실패한다. `rename`, `replace`, copy-then-replace 또는 overwrite fallback은 없다. 어느 경우든 호출자가 소유한 private staging만 정리한다.
6. **Register** — 처음 잡은 `R`, `C`와 ordered `(cut_id, realized_revision, asset_id)`를 기존 `register_review_artifact`에 그대로 전달한다. 그 transaction이 current composition, exact-five current closure와 global CAS를 다시 판단한다.
7. **Registration outcome / duplicate convergence** — registration이 성공하면 다음 단계로 간다. Conflict/UNIQUE/기타 registration 오류면 fresh snapshot을 읽되 예외를 catch-and-pass하지 않는다. 같은 `artifact_id`의 registered row가 있을 때만 DB row의 `(artifact_id, content_hash, composition_revision)`, ordered five `artifact_cuts`, embedded full metadata와 actual final bytes가 자신의 rendered row/closure/metadata/bytes와 전부 exact match하고, 현재 composition 및 exact five desired/realized/asset identities가 capture와 같음을 재확인해 idempotent same-artifact receipt 후보로 수렴한다. row 부재나 한 필드/byte라도 불일치하면 원래 registration 오류 또는 더 구체적인 integrity/currentness 오류로 실패한다.
8. **Authoritative readback/currentness** — registration 성공과 exact duplicate convergence 모두 새 connection snapshot에서 DB row+ordered five `artifact_cuts`를 다시 읽고 §4.2 `read_artifact`로 final actual bytes/hash/decode/full embedded closure를 검증한다. 이어 current composition revision이 exact `C`이고 현재 ordered five 각각의 `(cut_id, desired_revision, realized_revision, asset_id)`가 capture와 exact 같을 때만 successful current receipt를 반환한다. 단지 다섯 컷이 모두 `CURRENT`인 것만으로는 부족하다.

파일을 먼저 publish하고 DB를 나중에 등록하는 이유는 등록 row가 missing bytes를 authoritative artifact로 가리키는 더 위험한 상태를 만들지 않기 위해서다. final name은 concurrent invocation이 DB row 생성 전에도 즉시 공유·채택할 수 있으므로 **publish 뒤에는 최초 creator를 포함한 어떤 invocation도 final을 삭제하지 않는다**. process crash나 registration failure 뒤 exact-hash unregistered file이 남을 수 있지만 DB-first product reader는 이를 truth로 보지 않으며, 다음 동일 materialization은 full exact validation 후 재사용할 수 있다. 이 bounded safe residue를 감수하고 broad directory GC/repair framework는 추가하지 않는다.

### 5.2 Handled failure와 partial-effect cleanup

- preflight/render 전 실패: filesystem/DB effect가 없다. private staging 생성·save·decode/metadata 검증 또는 destination publication 실패: 그 invocation의 exact private staging subtree만 제거한다.
- exclusive hard-link가 `FileExistsError` 이외로 실패하면 overwrite/rename fallback 없이 오류를 반환한다. final 경로가 이미 있으나 expected full bytes/hash/decode/metadata와 다르면 기존 경로를 삭제·교체하지 않고 integrity failure를 반환한다.
- final name으로 exact bytes가 publish되거나 기존 exact final을 채택한 뒤 registration이 실패하면 SQLite rollback은 기존 API가 맡고 compositor는 DB row를 raw SQL로 보정하지 않는다. **fresh snapshot에 row가 없더라도 final은 절대 unlink하지 않는다.** 아직 row가 없는 경쟁자가 이미 그 path를 채택했을 수 있기 때문이다. exact-hash unregistered final은 non-authoritative safe residue로 유지한다.
- registration 오류는 §5.1.7의 전 필드/closure/metadata/actual-byte 비교가 모두 성립할 때만 idempotent duplicate convergence로 바뀐다. empty `pass`, exception suppression, row/id/hash 일부만 본 성공 변환은 금지한다.
- registration 성공 후 readback에서 bytes missing/hash mismatch/decode/closure failure: registered identity나 final을 임의 삭제·교체하지 않고 `ArtifactReadbackError`로 실패하며 corruption evidence(path, expected/actual hash/closure)를 보존해 Safe Abort한다. 과거 realization/intent/composition은 건드리지 않는다.
- cleanup 실패는 private staging cleanup 실패로 한정해 원래 오류와 함께 보고하고 success를 반환하지 않는다. realization, final path, historical registered artifact 또는 unregistered final을 scan-delete하지 않는다. 이 규칙이 Main의 반례에서 A의 unlink를 제거하므로 B의 실제 registration 뒤 authoritative row가 missing bytes를 가리키는 경로를 차단한다.

### 5.3 Concurrent materialize/composition/realization changes

- **composition 또는 realization이 render 중 변경**: global `R` CAS 또는 registration의 `C`/closure check가 commit을 거절한다. private staging만 제거하고 publish된 unregistered final은 보존한 채 caller에게 conflict를 반환한다. old snapshot으로 자동 rerender/retry하지 않는다.
- **동일 closure의 동시 materialize**: deterministic bytes/id/path가 같다. exclusive hard-link에서 one creator만 새 path를 만들고 나머지는 exact shared final을 채택한다. DB registration winner가 commit한다. loser는 Conflict/UNIQUE 뒤 §5.1.7의 registered row+ordered five DB closure+embedded metadata+actual full bytes 및 exact current target을 모두 비교해 같은 경우에만 idempotent same-artifact receipt를 반환한다; 다르면 원래 오류를 유지한다. 어느 invocation도 shared final을 삭제하지 않는다.
- **registration 직후 composition 또는 realization change**: registration은 그 commit 순간의 valid historical artifact이고 file/row를 지우지 않는다. final readback에서 current composition revision과 ordered five desired/realized/asset identities가 capture와 exact 다르면, 새 realization도 모두 Current이더라도 `ArtifactNoLongerCurrentError(artifact_id)`를 반환해 current review 성공으로 위장하지 않는다. 새 current closure는 새 materialization을 요구한다. 이후 `authorize_release`도 기존 current-closure check로 old artifact를 거절한다.
- **artifact 생성 뒤 accepted editor change**: `accept_composition`은 새 revision과 active authorization revocation만 commit하며 old artifact path/bytes를 쓰지 않는다. old file SHA-256은 전후 동일해야 한다.

## 6. 구현 순서와 clean cutover

1. 현재 `composition.py`의 schema/renderer를 §3.2/§4.1로 고친다. percentage numeric string과 uppercase font hash 수용을 제거하고, positive equal revisions/nonempty asset identity/required lowercase source hash를 direct renderer에서도 강제한다. Decimal edge math, pure slot/geometry, contain/no-crop 및 renderer choices는 유지한다.
2. five cut decode/hash/contain stitch와 bubble shape/text engine이 한 cut/font/text overflow 실패에서 전체를 중단하는 기존 방향을 유지하고 strict closure 누락/불일치도 output 전에 실패시킨다.
3. deterministic PNG metadata/save/readback과 content-addressed id/path를 유지하되 metadata의 ordered exact closure가 DB 등록 closure와 독립적으로 검증 가능하게 한다.
4. `composition_service.py` publication을 §5의 direct exclusive hard-link/no fallback/no final delete로 교체하고 기존 `register_review_artifact`만 호출한다. raw SQL artifact writer는 만들지 않는다.
5. duplicate error path를 전 필드 비교 후 명시적 convergence 또는 failure로 닫고, post-registration exact current target 및 DB-first reader의 row+`artifact_cuts`+metadata+actual bytes 검증을 연결한다.
6. `store.accept_composition` canonical normalizer clean cutover와 `__init__.py` export를 보존한다. 현재 구현에서 strict input contract가 깨진 callsite만 canonical fixture로 이관하고 compatibility alias/deprecated path는 두지 않는다. CLI/schema/migrations/generation은 실제 필요가 없으므로 그대로 둔다.
7. load-bearing `tests/test_composition.py` regression을 §7의 genuine concurrency와 strict boundary로 고치고 기존 transaction regression을 유지한다. source-text/wiring assertions나 mock pixel/registration success는 두지 않는다.
8. §7 disposable real-boundary scenarios를 실행하고 exact effect paths/bytes/hashes/SQLite before-after/barrier ordering을 verifier handoff에 남긴다. 이 self-check는 semantic verification/Exit verdict가 아니다.

## 7. Implementer self-check와 verifier semantic scenarios

모든 scenario는 Project Root 밖의 새 disposable project에 실제 on-disk SQLite, 실제 Pillow/font bytes와 실제 PNG files를 사용한다. helper로 current realization rows를 만들 때도 다섯 source PNG의 actual bytes/hash/path가 일치해야 하며, seeded metadata나 mocked renderer를 compositor 성공 증거로 쓰지 않는다. 각 scenario는 새 connection snapshot, actual file bytes/decode, created-path inventory와 cleanup을 함께 기록한다.

1. **Geometry / Scope A / Exit 1** — bubble edge cases를 1024×7680과 512×3840 pure surface에 같은 percentages로 계산한다. half-up expected integer edges와 normalized ratios를 비교하고 viewport 값이 API 입력에 없음을 확인한다. 실제 artifact에서 bubble fill/stroke/text의 known-color bounding pixels를 decode해 1024 surface expected box와 대조한다.
2. **Exact five / B / Exit 2** — current cut `1..5` actual PNG로 materialize 성공시킨다. direct renderer에 4, duplicate five, extra sixth뿐 아니라 zero/negative/noninteger/unequal desired-realized revision, empty asset identity, missing/uppercase/malformed/mismatched source hash를 각각 주면 output/DB artifact 없이 실패해야 한다. service는 caller cut list를 받지 않고 snapshot order만 사용함을 actual receipt closure로 확인한다.
3. **Unreadable cut / C / Exit 3–4, PATH-13** — five-current DB를 유지한 채 source 하나를 missing, zero/truncated, non-PNG, decodable JPEG-with-png-name, DB hash mismatch로 각각 만든다. 모든 경우 4-cut artifact/registration이 0이고 other realization bytes/rows가 불변인지 확인한다. 하나를 transparent/odd-size valid PNG로 만들어 contain/no-crop/white-alpha behavior도 decoded pixels로 확인한다.
4. **Currency gate / D / Exit 5, PATH-5** — 다섯 valid files가 있어도 cut 하나의 desired revision을 증가시켜 mismatch를 만든다. `materialize`가 source rendering 전에 `RealizationIncompleteError`로 거절되고 fresh snapshot은 `STALE/UNRESOLVED`, artifact row/file 0이어야 한다. queue/file count로 이를 보정하지 않는다.
5. **Canonical pixels, identity and exact readback / E–G / Exit 6–8** — distinct-color/marker five PNG, nonzero gap, ellipse+rounded rectangle, Korean/CJK/Latin multiline text를 materialize한다. decoded artifact에서 cut order, exact slot/gap pixels, contain margins, bubble bounds와 nonblank text glyph pixels을 읽는다. DB row의 artifact id/hash/composition revision, ordered five `artifact_cuts`, embedded normalized state/font/renderer contract 및 desired/realized/asset/source hashes, actual full file bytes/SHA-256을 모두 exact 대조한다. metadata cut 한 필드만 DB `artifact_cuts`와 다르게 만든 corruption copy도 `read_artifact`가 거절해야 한다. 새 process reader도 같은 bytes를 반환해야 한다.
6. **Determinism and strict state/font/text failures / I / Exit 10–11** — same source/state/font/runtime을 두 번 render해 exact PNG bytes/hash equality를 확인한다. explicit newline, whitespace wrap, one overlong token hard-wrap를 decoded output과 recorded expected line positions로 확인한다. percentage numeric string, bool/non-finite/too-many-decimals, uppercase/non-hex/wrong font hash, missing/unreadable font, too-small geometry, content box overflow를 각각 실행해 canonical correction, fallback, shrink, truncate 없이 전체 실패하고 artifact row/file가 없는지 본다.
7. **Immutability / H / Exit 9** — artifact A bytes/hash/inode identity를 기록한 뒤 bubble text 한 글자, geometry, gap을 각각 유효한 새 `accept_composition` revision으로 수용한다. 매번 A의 bytes/hash가 동일하고 current composition revision만 증가하며 새 materialization 전에는 A를 current artifact로 반환하지 않는지 확인한다. 새 artifact B path/id는 A를 overwrite하지 않는다.
8. **Handled failure and safe residue / Atomic 13.4** — staging save, post-save decode, hard-link destination creation, registration 전/중 SQLite exception을 controlled fault로 각각 유발한다. actual transaction row 상태, source/old artifact 불변, private staging cleanup을 확인한다. final publication 뒤 registration이 실패한 경우 row 0이어도 exact-hash final이 남고 DB-first reader는 이를 거절하며, 같은 closure의 이후 materialization이 full validation 후 재사용할 수 있어야 한다. hard-link unsupported/error에는 rename/replace/copy overwrite fallback이 없어야 한다. registration 후 final bytes를 고의 손상시키는 readback scenario는 success가 아니라 `ArtifactReadbackError`이며 DB/final을 임의 삭제하지 않는지 확인한다.
9. **Concurrent composition/realization race** — renderer를 실제 barrier에서 멈춘 뒤 별도 writer가 `accept_composition` 또는 current cut의 new realization을 commit한다. old call은 registration conflict, no registered old closure, private staging cleanup, published final retention이어야 한다. 별도 scenario에서 registration commit 직후 composition 또는 realization writer가 새 exact-five Current closure를 만들도록 순서를 제어한다. historical artifact가 남되 final current receipt가 exact identity 비교로 거절되고 bytes는 immutable이어야 한다; 단지 모든 cuts가 Current인 사실로 통과하면 실패다.
10. **Genuinely concurrent duplicate/registration-failure race** — 실제 on-disk SQLite와 filesystem에서 두 independent service/thread 또는 process를 controlled barriers로 동시에 실행한다. (a) natural duplicate에서는 둘이 같은 `R/C/closure`를 실제 render/publish/register하고 exactly one row와 one file로 수렴하며, 성공 receipt는 exact same id/hash/full bytes여야 한다. (b) Main 반례 ordering에서는 A가 exclusive final creator가 된 뒤 registration 앞에서 멈추고 B가 같은 final을 실제로 채택한 뒤 registration 앞에서 멈춘다. A의 registration만 attributable Conflict fault로 실패시켜 아직 DB row 0임을 관찰하고 A를 완전히 settle시킨 다음, B는 **real `register_review_artifact`**를 호출해 commit하고 real `read_artifact`로 확인한다. A failure injection은 ordering을 만드는 ancillary fault일 뿐 B의 registration/readback을 대체하지 않는다. 최종 fresh snapshot과 path inventory는 row 1, exact file 1, `registered_file_exists=true`, full hash/decode/closure 일치여야 한다. 두 scenario 모두 모든 thread/process가 settle한 뒤 각 registered row를 DB-first reader로 순회해 missing/corrupt target이 0임을 증명하고 disposable root를 정리한다.
11. **Downstream identity boundary / J–K / Exit 12–13, PATH-7/11** — materialize receipt의 `artifact_id`만 사용해 별도 review-like reader와 export-like reader가 `read_artifact`를 호출한다. 두 read가 DB의 같은 row/ordered `artifact_cuts`/path/full bytes/hash/decoded geometry를 얻고, API에 text/layout input 또는 renderer 호출이 없음을 확인한다. 실제 UI/export/Blogger 실행이나 전달 성공은 주장하지 않는다.
12. **Restart and filesystem false-success** — 모든 process/connection을 닫은 뒤 새 Python process가 snapshot+`read_artifact`로 same identity/hash/bytes를 읽는다. unregistered exact-hash content-addressed file을 따로 두어도 DB-first reader가 거절하되 파일은 보존하는지, DB row만 있고 missing/corrupt/mismatched-metadata file이면 readback failure인지 확인한다.

### 7.1 Acceptance 및 BASELINE Exit map

| Scope Acceptance | Scenario | BLOCK-03 Exit |
|---|---|---|
| A normalized viewport-independent geometry | scenario 1 | 1 |
| B exact-five cut assets | scenario 2 | 2 |
| C one cut unreadable/decode failure → whole failure | scenario 3 | 3, 4 |
| D five Current gate | scenario 4 | 5 |
| E authoritative immutable PIL artifact | scenarios 5, 7 | 6 |
| F artifact identity/closure binding | scenario 5 | 7 |
| G bytes readback hash | scenarios 5, 12 | 8 |
| H editor change leaves old bytes immutable | scenarios 7, 9 | 9 |
| I PIL owns wrap/typography | scenarios 5, 6 | 10, 11 |
| J no downstream reflow/layout required | scenario 11 | 12 |
| K review/export same identity | scenario 11 | 13 |

### 7.2 Verifier handoff and authoritative evidence

Implementation owner hands verifier: exact current Thesis/Scope/Baseline/Plan digests; target source/test hashes; Python/Pillow/SQLite/font path+font hash+feature versions; each disposable scenario command/input; before/after fresh DB snapshots and relevant raw rows; source/font/artifact actual byte hashes; decoded dimensions/pixel boxes/text nonblank observations; private staging/final path inventory; concurrent barrier event trace와 thread/process settlement; registration exception 및 convergence의 exact field comparisons; 모든 registered row에 대한 DB-first actual file/hash/decode/closure readback; cleanup result를 남긴다. Internal return, HTTP acceptance, screenshot, mock/canned registration success, metadata-only registration 또는 file presence alone은 proof가 아니다.

Verifier target은 fresh implementation bytes와 fresh disposable project다. scenario 중 font/Pillow environment가 unavailable하면 geometry/stitching의 관찰과 typography `INCONCLUSIVE`를 분리하고 surrogate success로 전체를 통과시키지 않는다. non-authoritative exact-hash orphan 자체는 known partial/corruption이 아니지만 DB-first 거절과 bytes integrity를 확인해야 한다. registered row→missing/corrupt/mismatched bytes, unresolved invariant 또는 final 삭제 경로가 하나라도 있으면 BLOCK-04 handoff는 금지된다.

## 8. Conditional first work

### 8.1 Font/runtime boundary

- `plan_anchor`: §2.3, §3.4, §7.6.
- `permitted_initial_work`: implementation source edit 전 current target에서 configured font file을 read/hash하고 Pillow가 그 exact bytes로 최소 두 font size의 `한글 漫画 ABC`를 measure/render해 nonblank decodable scratch PNG를 만드는 bounded Project-Root 밖 experiment.
- `discriminating_observation`: readable stable font bytes/hash, requested sizes의 FreeType construction, representative non-whitespace glyph masks와 actual rendered nonblank pixels. 이 결과는 font boundary만 지지하며 compositor completion은 아니다.
- `dependent_work_not_yet_permitted`: font fallback/search chain, default font 성공 주장, typography acceptance/Exit 10–11, BLOCK-04 handoff.
- `response_if_refuted`: geometry/cut/file ordering과 독립인 안전 작업만 계속할 수 있다. Main/environment owner가 exact readable font bytes/path를 공급하지 못하면 typography verification은 `INCONCLUSIVE`; renderer를 fallback으로 바꾸거나 Scope 의미를 축소하지 않는다. font identity contract를 바꿔야 하면 이 Plan을 재검토한다.

### 8.2 Existing registration contract currentness

- `plan_anchor`: §2.1.6, §4.2, §5.
- `permitted_initial_work`: implementation 시작 시 exact `register_review_artifact` signature/body와 `review_artifacts`/`artifact_cuts` schema를 다시 읽고 supplied source hashes/current Scope validator 결과를 대조한다.
- `discriminating_observation`: global CAS, composition revision equality, five-current check, cut closure match와 atomic inserts가 이 Plan의 grounded contract와 동일하다.
- `dependent_work_not_yet_permitted`: raw SQL/새 artifact transaction writer, schema migration, 또는 새 independent Review가 §5를 admit하기 전의 filesystem/DB correction mutation. §5와 다른 atomicity/cleanup strategy는 새 method review 없이는 허용되지 않는다.
- `response_if_refuted`: affected composition service 구현을 중단하고 Planner/Main에게 method revision을 반환한다. 기존 transaction을 우회하거나 복제하지 않는다.

## 9. 구현 재량, 위험과 반환 조건

### 9.1 구현자 재량

Private helper/dataclass 이름, error message wording, local cache container, test fixture 색상/문구, equivalent Pillow drawing call의 작은 배치는 재량이다. surface dimensions, contain/no-crop, integer slot formula, half-up edge math, percentage JSON-number-only, exact lowercase font/source hashes, positive equal cut revisions/nonempty asset identity, fail-on-overflow, content-addressed exclusive hard-link/no-overwrite path, existing registration transaction, publish 후 final no-delete, exact duplicate convergence/currentness 및 DB-first full closure readback은 재량이 아니다.

### 9.2 Material risks/conditions

- Pillow/FreeType/RAQM drift는 rerender hash를 바꿀 수 있다. exact runtime/font identity를 evidence에 남기되 이미 등록된 bytes를 재렌더하여 “동일”하다고 만들지 않는다.
- filesystem과 SQLite는 하나의 atomic transaction이 아니다. 이 Plan은 authoritative DB→missing bytes보다 exact-hash non-authoritative orphan 가능성을 의도적으로 택한다. handled cleanup은 invocation-private staging에만 적용하며 publish된 final은 registration outcome이나 fresh row absence와 무관하게 보존한다. DB-first/readback 없이 file presence를 성공으로 보지 않는다.
- source realization path는 DB가 immutable attribution으로 사용하지만 OS가 bytes mutation을 구조적으로 금지하지 않는다. compositor는 actual source hash를 DB와 대조해 mismatch를 실패시키고, rendering 동안 읽은 bytes를 고정한다.
- global authority CAS는 unrelated generation fact 변화에도 render registration을 conflict시킬 수 있다. 이는 기존 transaction contract를 좁게 보존하는 정직한 거절이며 자동 retry 이유가 아니다.

### 9.3 Plan/Scope/Thesis 반환

다음은 영향 작업을 멈추고 이 Plan을 개정해 새 independent Plan Review를 받아야 하는 material method change다.

- canvas/slot/order/fit/crop, percentage basis/rounding, bubble/style/wrap/overflow 또는 font identity contract 변경;
- `register_review_artifact` 대체/우회, schema migration, artifact path/identity/hash 의미나 filesystem–DB ordering 변경, published final 삭제/GC, hard-link 외 rename/replace/overwrite fallback 도입;
- multiple renderer/downstream reflow, mutable overwrite path, incomplete closure/partial four-cut output, exact target 대신 all-current만 보는 currentness 또는 stale current 허용;
- existing writer/caller가 canonical composition validation을 우회해야 한다는 결론;
- real evidence가 owner/interface/persistence/race/cleanup/readback 전략을 반박하는 경우.

Exactly-five, Canonical Review Artifact, approval/downstream 의미를 바꿔야 하면 `THESIS-001` owner에게 반환한다. current Outcome/Acceptance/Non-Goals 또는 BLOCK-03 경계를 바꿔야 하면 Scope shaping owner에게 반환한다. font/runtime이 단지 unavailable하면 제품 정책을 발명하지 말고 §8의 evidence limit와 환경 owner에게 반환한다.

## 10. Plan 완료 경계

이 문서는 exact ready BLOCK-03의 개정 실행/자체확인 방법만 준비한다. product source/data/schema, Thesis, Scope, Baseline, completed Scope/status, prior review artifact, UI/release/external system을 변경하지 않았고 implementation, semantic verification, Plan Review decision 또는 BLOCK-03 Exit를 발행하지 않는다. 이전 `/home/user01/tmp/comic-new-block03-plan-review.json`의 `ADMIT`은 이전 Plan hash에만 결속되어 stale이며 구현 재개 권위가 없다. 다음 단계는 Main이 별도 Gemini Flash invocation으로 이 exact revised Plan bytes를 검토해 `/home/user01/tmp/comic-new-block03-plan-review-r2.json`에 fresh independent decision을 남기는 것이다. 그 review의 `ADMIT`, exact digest currentness 및 §8 조건 확인 전에는 §1.2 correction/start scope를 실행하지 않는다.
