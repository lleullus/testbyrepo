# PLAN-001 — Client Resync Safety and Empirical Cutover

## Bound Authority

- Project Root: `/home/user01/project/comic_new`
- Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md` (`THESIS-002`, sha256 `1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`)
- Scope: `/home/user01/project/comic_new/docs/planning/work/client-resync-cutover/SCOPE.md` (sha256 `6adc3b1b4ef94921d28933a203ec4541944a0390a03aae0671becbb8e309e2b4`, `Status: ready`)
- Transition Authority: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md` (sha256 `629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55`, selected `BLOCK-09`)
- Repository investigation: None supplied; current source plus completed BLOCK-06/07/08 artifacts form the evidence baseline.
- Entry: BLOCK-06, BLOCK-07 and BLOCK-08 exact Scopes are `done`; each has a final independent Gemini `VERIFIED` cycle and Luna `COMPLETE / Findings: None` Coverage.

## Current State

1. `frontend/src/store/studio.ts` defines freshness as `server != null && !gapFetchPending`. On a failed gap recovery it sets `gapFetchPending=false`, re-enabling actions over stale state.
2. EventSource errors only set `stream.state='reconnecting'`; `hasCurrentSnapshot`, generate, materialize, authorize and release gates ignore this state.
3. `snapshot-required` fetches collapse while pending and `applySnapshot()` prevents authority revision rollback, but no persistent resync-required latch exists and event envelope revision is not checked against payload revision.
4. Baseline/intent/composition saves call their API without a freshness gate. Local drafts should remain editable, but stale authoritative submission must not leave the browser.
5. STOP/cancel paths are safety actions and must stay available in degraded state.
6. BLOCK-06/07/08 already implement the server-side Gate 1–4 mechanisms. BLOCK-09 must re-exercise them on the final integrated target, not redesign them.

## Method

### 1. Explicit client stream state machine

Replace the lowercase `state + gapFetchPending` truth with one explicit public stream contract in `types.ts`:

```ts
stream: {
  status: 'CONNECTING' | 'OPEN' | 'DEGRADED'
  resyncPending: boolean
  lastEventId?: string
}
```

Use one private `resyncRequired` latch in the store. `hasCurrentSnapshot` is true only when `server != null`, `stream.status === 'OPEN'`, `resyncRequired === false`, and `resyncPending === false`.

Transitions:

- initial: `CONNECTING`; `loadStudio()` fetches the first snapshot, then opens SSE; first successful `onopen` with no prior degradation moves to `OPEN`;
- any EventSource error: set `DEGRADED`, latch resync required; do not clear server/drafts;
- `snapshot-required`: set `DEGRADED`, latch resync required, invoke the shared recovery function;
- reconnect `onopen` while latched: remain `DEGRADED` and invoke the shared recovery function;
- recovery failure: clear only `resyncPending`; remain `DEGRADED` and latched;
- recovery success: apply only a structurally valid, non-regressing authoritative snapshot; then clear the latch/pending and set `OPEN`;
- a valid `studio.snapshot` event whose envelope revision equals payload revision and is not older than the current server snapshot may itself settle recovery and set `OPEN`;
- malformed, mismatched or older events never clear degraded state.

Use one `requestResync()` promise boundary to collapse concurrent triggers. Do not introduce timers/backoff/retry frameworks. EventSource reconnect/open or a fresh `snapshot-required` event supplies the next retry trigger.

Make `applySnapshot()` return whether the supplied snapshot is acceptable/current without weakening monotonic draft base-change handling. Equal revision may establish freshness after reconnect but must not reapply or clear drafts; lower revision cannot.

### 2. Fail-closed mutation gates

Add a single computed `canMutateAuthority = hasCurrentSnapshot`. Reuse it in `canGenerate`, `canMaterializeReview`, `canAuthorize`, and `canRelease`.

Defense in depth at action boundaries:

- `dispatchEdit()` returns before executing any API callback when degraded; the caller's local draft remains untouched and an alert toast states resync is required;
- baseline/intent/composition save entrypoints use the same guard;
- generation, materialize, authorize, export and Blogger release already use computed gates; retain internal guard checks;
- local draft setters, selection, panels and review display remain usable;
- `stopJob()` and `stopAll()` remain callable while degraded.

No optimistic request, queued replay, or automatic save occurs after recovery. The user explicitly reissues any blocked mutation.

### 3. Honest degraded UI

Update `events.ts` state callback types and `StudioHeader.vue`:

- show `OPEN`, `CONNECTING`, or `DEGRADED / 재동기화 필요` through an accessible status label and visible text/icon treatment;
- do not hide the last snapshot surface merely because freshness is degraded; `StudioShell` renders when `server` exists, while action controls consume fail-closed gates;
- initial load without any snapshot retains the loading surface;
- button aria labels explain resync blocking where relevant without duplicating new modal/state systems.

Update styles minimally using existing current/stale tokens. Rebuild production static assets only after runtime behavior passes focused checks.

### 4. Focused store and browser evidence

Expand the existing `SSE gap recovery` tests rather than create a second harness:

- disconnect from OPEN immediately makes all consequential gates false while STOP remains available;
- gap recovery failure leaves DEGRADED after pending clears;
- duplicate gap/open signals produce one concurrent fetch;
- successful retry restores OPEN;
- valid newer snapshot event settles degraded state; older/mismatched/malformed event does not;
- newer SSE arriving before older fetch remains authoritative and recovery cannot rollback it;
- baseline/intent/composition drafts remain byte-equivalent while blocked saves issue zero mutation fetches;
- equal current revision can settle reconnect freshness without replacing local drafts.

Run Vitest and `vue-tsc --noEmit`. Build Vite into `src/comic_new/static` and start actual `comic-new serve` on a disposable project. Drive Chromium against the production static build, inject EventSource/fetch faults at browser boundaries, and observe DOM button disabled states, status text, no mutation HTTP requests, draft preservation, and successful recovery.

### 5. Fresh Gate 1–4 empirical cycle

The independent Gemini verifier—not the implementer—owns the final semantic gate cycle on one stable post-build target:

- **Gate 1:** controlled generation provider with two same-revision requests; complete older/latest in adverse order, including cancellation/failure, and read SQLite/file/snapshot currency. Only latest request sequence may commit Current.
- **Gate 2:** create exactly five current realizations, materialize/authorize, then accept one-character dialogue change and separately 1px gap change through actual API/browser paths. Read active/history authorization in SQLite and snapshot; old export/Blogger calls must fail.
- **Gate 3:** real mock-provider subprocess reaches the pre-commit barrier; accept STOP before release; then release/finish provider. Read job/attempt/control rows, cut realization/file identity, staging cleanup, process tree and SSE snapshot. No ghost pixel commit.
- **Gate 4:** local Blogger HTTP harness exercises timeout/truncated/invalid body, 200 missing/wrong marker, exact marker and unknown reconcile. Read exact attempt state/evidence and prove no republish.

These scenarios may reuse existing verifier techniques and focused test utilities, but must execute fresh against the final target. A prior report alone is not evidence.

### 6. Final integration and authoritative readback

After implementation and focused checks:

1. run complete backend `pytest` once;
2. run complete frontend Vitest and typecheck once;
3. build production static once and hash `index.html`, referenced JS and CSS;
4. start actual `comic-new serve` against a disposable complete project and verify strict static preflight/readiness;
5. perform browser initial load → OPEN → fault → DEGRADED block → recovery → OPEN;
6. perform final SQLite and HTTP snapshot readback for schema version, exactly five cuts, baseline bindings, request sequences/currencies, no active jobs, composition, artifact/authorization/delivery truth and stream UI;
7. stop server/browser/provider, verify no process/staging/temp residue, and re-hash all stable target files.

Only an independent `VERIFIED` result for A–I followed by Luna Coverage `COMPLETE / Findings: None` permits Main to set Scope `done`, record BASELINE-002 completion and close the user's sequential request.

## Acceptance Mapping

- A: Sections 1–3; disconnect transition, action matrix and STOP exception.
- B: Sections 1 and 4; persistent failure latch, collapsed fetches, no flicker.
- C: Sections 1 and 4; envelope/payload/revision admission and race ordering.
- D: Sections 2–4; actual production browser, disabled DOM, zero requests, draft preservation.
- E: Section 5 Gate 1.
- F: Section 5 Gate 2.
- G: Section 5 Gate 3.
- H: Section 5 Gate 4.
- I: Section 6 final suite/build/serve/readback/cleanup.

## Failure, Race, and Preservation

- `DEGRADED` is fail-closed and sticky until authoritative recovery evidence; fetch completion alone is insufficient if the response regresses current authority.
- A valid newer SSE snapshot may supersede an older pending fetch. The late fetch cannot regress server state or draft base relation.
- Consequential actions check freshness both through UI computed state and at store method boundaries. Programmatic calls cannot bypass UI disabled attributes.
- Local drafts never become authority merely because the stream is degraded and are never discarded by recovery failure.
- STOP/Cancel remain available and do not depend on freshness.
- No gate test mutates the source repository or contacts a live Blogger account. Every process and network harness is disposable and settled.

## Non-Goals

No new domain feature, optimistic degraded fallback, background retry system, real deployment/publication, new provider/destination, policy revision, or weakening of final empirical gates.

## Return Boundary

Implementation starts only after independent Gemini High Plan Review `ADMIT` for this exact Scope/Plan. Any proposal to clear DEGRADED on failed/older recovery, allow consequential mutation while stale, block STOP, substitute old reports for fresh gates, or skip production build/browser readback returns to Plan/Scope ownership.
