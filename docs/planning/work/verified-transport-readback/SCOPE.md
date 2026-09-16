# Scope: Verified Transport and Content-Identity Readback

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md sha256:1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md sha256:629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55

## Outcome

`BLOCK-07`은 완료되었다. 현재 릴리즈 preflight는 승인 아티팩트 파일을 검사한 뒤 경로를 반환하고, PNG export와 Blogger 전달은 그 경로를 나중에 다시 읽는다. 검증과 사용 사이의 파일 교체가 승인되지 않은 바이트를 외부화할 수 있다. Google Blogger 경로는 목적지 GET의 응답 본문을 버리므로 HTTP 200만으로 성공을 선언하며, 통제 어댑터도 콘텐츠 identity readback 없이 성공을 반환한다. `unknown` delivery attempt를 원격 콘텐츠와 다시 대조할 권위 있는 reconcile 경로도 없다.

이 Scope는 `BASELINE-002`의 `BLOCK-08`을 선택한다. Release preflight는 승인 정본을 한 번 읽고 전체 무결성을 검증한 뒤 immutable verified in-memory bytes와 `artifact_id`/SHA-256 결속을 반환한다. PNG export와 Blogger 전송은 이 동일한 바이트 객체만 소비하며 검증 후 원본 경로를 다시 열지 않는다. Blogger HTML에는 exact `<!-- comic-new:artifact-id={artifact_id}:sha256={content_hash} -->` 마커가 포함된다. 목적지 readback은 HTTP 상태가 아니라 원격 HTML에서 exact artifact ID와 SHA-256 마커를 파싱해 일치할 때만 `confirmed_success`를 영속화한다. 200 응답이어도 마커 누락·중복·형식 오류·identity/hash 불일치는 `confirmed_failure`와 구체적 content-identity 증거로 기록한다. 전송 또는 readback 결과가 불명확하면 `unknown`을 유지하며, 이미 알려진 post ID/URL이 증거에 남아 있는 경우 동일 attempt를 안전하게 재대조하는 reconcile API가 같은 identity 검증을 수행한다. 목적지 정보를 확보하지 못한 unknown은 성공을 추측하지 않고 그대로 유지한다.

포함: `delivery.py` verified-byte transport 경계, Google/controlled adapter marker 생성과 HTML readback, delivery evidence, unknown reconcile 서비스/API, PNG/Blogger/HTTP/CLI 관련 호출자와 focused regression, 기존 BLOCK-05 승인·전달 생명주기 보존.

제외: 실제 외부 Blogger 계정에 대한 발행, provider retry/fallback, 새로운 배포처, BLOCK-09 SSE degraded safety와 최종 cutover, delivery history 스키마의 범용 감사 시스템화.

## Acceptance

### A. 검증 바이트 단일 handoff

활성 승인과 5개 Current cut을 가진 프로젝트에서 preflight는 승인된 Canonical Review Artifact를 한 번 읽고, SHA-256·PNG 규격·등록 closure·물리 cut assets를 검증한 immutable `verified_bytes`와 exact `artifact_id`/content hash를 반환한다. 반환 직후 원본 review artifact 파일을 다른 유효 PNG로 교체하거나 삭제해도 이미 시작된 PNG export와 Blogger publish는 검증된 메모리 바이트만 소비하며, transport에 전달된 SHA-256은 승인 hash와 정확히 일치한다. 검증 뒤 원본 경로를 다시 여는 호출은 없다.

### B. PNG export의 anti-TOCTOU 보존

preflight 직후 원본 파일 변조를 주입한 PNG export는 검증된 메모리 바이트를 원자적으로 목적지에 기록한다. 출력 바이트와 승인 artifact 바이트는 byte-for-byte 동일하고 hash가 일치한다. 출력 readback은 실제 목적지 파일에서 수행된다. preflight 이전 변조는 기존 무결성 게이트에서 차단되며 delivery attempt나 부분 출력이 생기지 않는다.

### C. Blogger payload identity marker

Google 및 통제 어댑터에 전달되는 HTML은 검증된 PNG 바이트를 사용하며 exact 마커 `<!-- comic-new:artifact-id={id}:sha256={hash} -->`를 하나 포함한다. 마커의 ID/hash는 활성 승인 및 verified bytes에서 유도되고 호출자 임의 입력으로 대체할 수 없다. publish 기록에서 실제 전달 bytes hash와 marker identity를 재조회할 수 있다.

### D. 200 응답의 거짓 성공 차단

Blogger insert가 post ID/URL을 반환하고 목적지 GET이 HTTP 200이어도 HTML에 마커가 없거나, 마커가 malformed/중복이거나, artifact ID 또는 SHA-256이 다르면 delivery attempt는 `confirmed_success`가 되지 않는다. 결정 가능한 불일치는 `confirmed_failure`로 영속화되고 evidence에 expected/observed identity와 원인이 남는다.

### E. exact content identity에서만 성공

목적지 HTML에서 exact artifact ID와 SHA-256 마커가 유일하게 파싱되고 승인 identity와 일치할 때만 Blogger attempt가 `confirmed_success`로 전이한다. SQLite, snapshot, HTTP 응답의 destination ID/URL과 evidence는 같은 post/readback 사실을 반환하며, 성공 evidence는 marker 검증 결과를 포함한다.

### F. Unknown 보존과 안전한 reconcile

insert 응답 또는 목적지 readback이 timeout/disconnect/불완전하여 정합성을 결정할 수 없으면 attempt는 `unknown`을 유지한다. post ID/URL이 이미 알려졌다면 evidence에 보존한다. reconcile 서비스/API는 해당 unknown attempt의 저장된 authorization/artifact identity와 알려진 destination만 사용해 원격 HTML을 다시 읽고, exact marker 일치 시에만 같은 attempt를 `confirmed_success`로 전이하며 불일치는 `confirmed_failure`로 전이한다. destination을 알 수 없거나 재대조가 다시 불명확하면 상태는 `unknown`으로 남고 새 발행이나 성공 추측을 하지 않는다. terminal attempt 재조정은 거절된다.

### G. 권위·경쟁·호환성 보존

preflight 후 외부 I/O 중 authority가 바뀌거나 승인이 취소되어도 관찰 기록은 원 delivery attempt와 artifact identity를 바꾸지 않으며, 새 권위를 과거 성공의 근거로 사용하지 않는다. 기존 승인 철회, All-or-Nothing, `unknown`/`confirmed_failure`, API/CLI/frontend snapshot 계약은 유지된다. BLOCK-06/07의 generation currency, interruption, baseline/dialogue 불변식은 변경되지 않는다.

## Non-Goals

- 실제 Blogger 자격 증명 또는 실계정 side effect
- 원격 게시물 수정·삭제·재발행 자동화
- 목적지 identity 없이 제목/시간만으로 게시물을 추측하는 reconcile
- SSE gap 복구, DEGRADED UI, 최종 production cutover
- Blogger 외 배포처

## Open Decisions

None
