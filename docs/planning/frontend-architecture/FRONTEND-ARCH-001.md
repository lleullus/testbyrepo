# Web Comic Studio Frontend Architecture Decision

- Status: DECIDED
- Artifact: FRONTEND-ARCH-001
- Product authority: `docs/planning/product-thesis/web-comic-studio/THESIS-001.md`
- Scope: frontend implementation architecture only; this document is a derived projection and cannot redefine product meaning.
- Retrieval: 0 external fetches; project and local platform evidence only.

## 1. Final stack

| Area | Decision | Excluded |
|---|---|---|
| UI | Vue 3 Composition API, `<script setup>`, TypeScript `strict` | React/Svelte/vanilla |
| Build | Vite; Bun 1.3 is package manager/script runner, Node 24 is the supported fallback runtime | Bun-only bundling, SSR |
| State | Pinia, exactly one domain store: `useStudioStore` | Vuex, multiple entity stores, XState, RxJS, query-cache layer |
| Transport | native `fetch`, native `EventSource` | Axios, WebSocket, GraphQL |
| Layout | scoped plain CSS, CSS custom properties, Grid/Flexbox | Tailwind, CSS-in-JS, layout library |
| Canvas interaction | DOM/SVG overlay plus native `PointerEvent` | Fabric.js, Konva, interact.js, general DnD library |
| UI primitives | native `<dialog>`, Vue `Teleport`, local anchored popover and toast components | full component suite |
| Routing | no client router: one studio shell | Vue Router |
| Tests | Vitest only for coordinate/state reducers whose boundary behavior merits a permanent test | component snapshot suite |

**Selected:** Vue 3 + TypeScript + Vite. The repository has no existing frontend stack to preserve. Vue's SFC and reactivity directly fit one stateful studio screen; Vite produces deterministic static assets without introducing SSR or a second server. React offers no deployment advantage here and would add more state/event ceremony; Svelte and vanilla would replace familiar Vue conventions without reducing the required domain state. Stop comparison here.

### Dependency budget

Runtime dependencies are only `vue` and `pinia`. Build dependencies are `vite`, `typescript`, `vue-tsc`, and `@vitejs/plugin-vue`. Toasts, dialogs, popovers, split layout, SSE, and drag/resize are local/native code. Add no canvas or DnD package unless a measured browser interaction cannot meet this specification.

## 2. FastAPI single-deployment contract

```text
frontend/                         # source; never served directly
  package.json
  bun.lock
  vite.config.ts
  tsconfig.json
  index.html
  src/
src/comic_new/static/            # generated Vite dist; Python package data
  index.html
  assets/*.[hash].js
  assets/*.[hash].css
```

- `vite.config.ts`: `base: '/'`, `build.outDir: '../src/comic_new/static'`, `emptyOutDir: true`.
- `bun run build` invokes `vue-tsc --noEmit && vite build`; Vite remains the bundler.
- The Python build pipeline runs `bun install --frozen-lockfile && bun run build` before wheel assembly and includes `src/comic_new/static/**` as package data.
- `comic-new serve` starts the only process: FastAPI serves `/assets` from package resources, API/SSE routes under `/api`, and `GET /` returns the generated `index.html`.
- No SPA fallback is needed because there is one client route. Unknown non-API paths return 404 rather than hiding server route errors behind `index.html`.
- Development may run Vite with `/api` proxying to FastAPI, but this is not a production process or deployment dependency.
- Startup fails clearly if `static/index.html` is missing; it must not silently serve an empty shell.

## 3. Studio shell and three-column layout

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Header: project truth summary | queue summary | STOP | review/release│
├────────────────┬───────────────────────────────┬─────────────────────┤
│ Left           │ Center                        │ Right               │
│ exactly 5 cuts │ composition canvas            │ selected inspector  │
│ revisions      │ overlay/selection/zoom tools  │ text/style/geometry │
│ STALE badges   │ unsaved/conflict markers      │ save state          │
└────────────────┴───────────────────────────────┴─────────────────────┘
```

Desktop CSS contract:

```css
.studio-shell {
  display: grid;
  grid-template:
    "header header header" 52px
    "left center right" minmax(0, 1fr)
    / clamp(240px, 19vw, 304px) minmax(0, 1fr) clamp(288px, 23vw, 368px);
  height: 100dvh;
  overflow: hidden;
}
.left-panel, .right-panel, .canvas-region { min-width: 0; min-height: 0; }
.left-panel, .right-panel { overflow: auto; }
.canvas-region { overflow: hidden; }
```

The three permanent regions are justified because cut selection/status, visual manipulation, and selected-object properties must remain simultaneously visible during repeated cross-work. The header is permanent because STOP and truth status must never depend on the current selection or scroll position.

At widths below 1100px, Center remains permanent; Left and Right become independently toggled, viewport-edge, **non-modal** panels. They do not trap focus and do not imply a blocking decision. Only the currently opened edge panel overlays Center. This responsive conversion is CSS Grid/Flex plus local state, not a layout dependency.

## 4. Five-axis interaction boundary

| Surface | Modality | Persistence | Anchoring | Task role | Focus behavior | Component |
|---|---|---|---|---|---|---|
| Header truth/queue/STOP | non-modal | permanent | viewport top | status + immediate command | normal traversal | `StudioHeader` |
| Left five-cut rail | non-modal | permanent on desktop | grid left edge | selection + currency inspection | normal traversal | `CutRail` |
| Center canvas | non-modal | permanent | grid center | primary manipulation | roving object focus | `CompositionCanvas` |
| Right inspector | non-modal | permanent on desktop | grid right edge | detailed edit form | normal traversal | `InspectorPanel` |
| Queue details | non-modal | temporary | queue button | inspect jobs and per-job stop | returns to trigger | anchored `QueuePopover` |
| Bubble quick actions | non-modal | temporary | selected bubble | command menu | returns to trigger | anchored `BubbleMenu` |
| Canonical review | **modal** | one decision session | viewport | inspect immutable artifact + authorize | trap; Esc closes before authorization | native `dialog.showModal()` |
| Re-baseline/release confirmation | **modal** | one decision | viewport | consequential confirmation | trap; explicit confirm/cancel | native `dialog` |
| Save/error feedback | non-modal | temporary plus persistent inline marker | viewport bottom-right | feedback | no focus theft; `aria-live` | `ToastRegion` |

Rules:

- A right-side inspector is never implemented as a modal: editing requires continued canvas access.
- A canonical review is always modal: editing the projection while approving a fixed artifact would invalidate what is being decided.
- Destructive or authority-bearing actions use a dialog; ordinary selection uses panel controls or anchored popovers.
- Toasts never replace durable state markers. A failed save remains visible on the affected field/object after the toast expires.

## 5. Canvas and lettering interaction contract

### 5.1 Geometry model

Every bubble uses normalized, top-left geometry relative to the **canonical composition surface**, not the browser viewport or source cut image:

```ts
interface BubbleGeometry {
  x_pct: number; // 0..100, left edge
  y_pct: number; // 0..100, top edge
  w_pct: number; // >0..100
  h_pct: number; // >0..100
}

interface BubbleDraft extends BubbleGeometry {
  id: string;
  cut_id: 1 | 2 | 3 | 4 | 5;
  text: string;
  style_id: string;
  order: number;
}
```

- The composition surface has the same aspect ratio and cut/gap geometry as the canonical compositor.
- Base cut images and bubble overlays are children of that one `position: relative` surface.
- Overlay CSS uses percentages directly: `left`, `top`, `width`, `height`. No coordinates are stored in CSS pixels.
- `object-fit` letterboxing is not a coordinate basis. If images use `object-fit: contain`, their fitted image boxes are precomputed inside their cut slots; bubble coordinates remain relative to the whole composition surface.
- Persist four decimal places at pointer commit. Do not round during movement.

### 5.2 Pointer algorithm

On bubble/handle `pointerdown`:

1. Ignore non-primary mouse buttons.
2. Call `setPointerCapture(pointerId)` and `preventDefault()`; set the canvas interaction layer to `touch-action: none`.
3. Snapshot `surface.getBoundingClientRect()`, pointer start, and the bubble's starting percentage geometry. Freeze this rect for the gesture.
4. Keep transient gesture numbers local to `BubbleOverlay`; do not stream pointer frames through Pinia or the server.

On `pointermove`:

```ts
const dxPct = ((event.clientX - startClientX) / surfaceRect.width) * 100;
const dyPct = ((event.clientY - startClientY) / surfaceRect.height) * 100;
next.x_pct = clamp(start.x_pct + dxPct, 0, 100 - start.w_pct);
next.y_pct = clamp(start.y_pct + dyPct, 0, 100 - start.h_pct);
```

- Resize handles apply the same delta to the relevant edge, enforce compositor-defined minimum width/height, then clamp to the surface.
- `getBoundingClientRect()` already represents visual zoom, so deltas remain correct under a CSS scale transform. Pan affects the rect origin but not the delta ratio.
- Update one element with `requestAnimationFrame`; do not allocate a new whole composition on every pointer event.

On `pointerup`:

1. Release capture.
2. Round geometry to four decimals.
3. Write one local draft mutation and enqueue one save.
4. The accepted server response, not pointerup, determines saved status.

On `pointercancel`, discard only the transient gesture and return to the last local draft. Do not save.

Keyboard parity: a focused bubble moves by `0.25%` with arrow keys and `1%` with Shift+arrow; resize handles expose the same increments. `Delete` opens no dialog for an unsaved newly added bubble, but deleting a persisted bubble requires the same save/error pipeline as every other authoritative change.

### 5.3 WYSIWYG boundary

- The editable DOM/SVG canvas is explicitly labeled **Interactive Projection**, never the release truth.
- Placement is coordinate-faithful because editor and compositor share the same normalized composition/cut/gap schema.
- Browser text wrapping is not allowed to become a second authority. The save response returns compositor-resolved line breaks/typography metrics for the accepted revision; the projection renders those accepted metrics. While typing, the unsaved preview is visibly marked as draft.
- Exact final WYSIWYG is the server-materialized `Canonical Review Artifact`. The review dialog displays the artifact bytes by immutable `artifact_id`/hash; it does not reconstruct bubbles in the browser.
- Export and Blogger delivery reference that approved artifact identity and may uniformly scale/encode its bytes. They never rerender current editor state. Thus what the user approves is exactly what is delivered.

## 6. One-store state model

Use one Pinia store, `useStudioStore`. Gesture-only state remains local to the canvas component.

```ts
interface StudioState {
  server: StudioSnapshot | null;       // last authoritative readback
  drafts: Record<string, DraftPatch>;  // local projection, never authority
  saves: Record<string, SaveState>;    // idle | pending | failed | conflict
  selection: { cutId: 1|2|3|4|5; bubbleId?: string };
  jobs: Record<string, JobView>;
  queueOrder: string[];
  stream: { state: 'connecting'|'open'|'reconnecting'; lastEventId?: string };
  ui: { leftOpen: boolean; rightOpen: boolean; reviewArtifactId?: string };
  toasts: ToastMessage[];
}
```

Derived selectors only; never duplicate their truth in mutable fields:

```ts
cutCurrent(cut) = cut.desired_revision === cut.realized_revision
realizationComplete = cuts.length === 5 && cuts.every(cutCurrent)
projectedComposition = merge(server.composition, drafts)
hasUnsaved = Object.keys(drafts).length > 0
canMaterializeReview = realizationComplete && !hasUnsaved && noSaveFailures
canAuthorize = openedArtifact.identity === server.reviewArtifact.identity
canDeliver = server.releaseAuthorization?.artifact_id === server.reviewArtifact.id
```

Execution, currency, authorization, and delivery remain separate fields and selectors. A job becoming `completed` never sets a cut `Current`; only authoritative revision equality does.

## 7. Save isolation and error visibility

### Save protocol

- Every mutation sends `base_composition_revision` (or equivalent ETag) and a client `mutation_id`.
- Serialize composition saves: at most one request is in flight. Edits made during a request remain as a newer draft and are submitted next; they are never cleared by an older response.
- On 2xx, replace only the `server` layer from the returned authoritative snapshot. Clear a draft only when its `mutation_id` is the response's accepted mutation and no newer local mutation exists.
- Accepted pixel/text/geometry/gap changes cause server-side release authorization revocation. The response/SSE snapshot must show that revocation; the client does not fabricate it optimistically.

### Failure rules

| Result | Store behavior | Required UI |
|---|---|---|
| network/500 | keep draft; mark `failed` | error toast with Retry + persistent `저장 안 됨` badge on object/field |
| 409 | keep draft; update server layer from conflict payload or refetch; mark `conflict` | error toast + persistent comparison actions `서버 값 보기` / `최신본에 다시 적용` |
| later SSE update while dirty | update server layer only; never overwrite draft | mark draft `base changed`; require save/reconcile |
| retry success | clear only accepted draft | success toast optional; saved indicator becomes authoritative revision |

Toast copy is direct: `저장 실패 — 변경 내용은 이 브라우저에만 남아 있습니다.` A console log is insufficient. Toasts use `role="status"` for ordinary feedback and `role="alert"` for save failure. A local draft disables review materialization and shows `미저장 변경은 승인본에 포함되지 않음`; it does not masquerade as an accepted intent or revoke server authority by itself.

## 8. SSE and queue rules

Open one native `EventSource('/api/events')` when the studio snapshot is loaded; close it on app unmount. The server's event ID/domain revision is mandatory.

| Event class | Apply rule |
|---|---|
| snapshot/intent/composition/authorization | apply to `server` only when its revision is newer; retain drafts |
| job queued/started/progress/stop-requested/interrupted/failed | update `jobs` and `queueOrder` only; never infer cut currency |
| realization accepted | update cut realization only from authoritative payload; `Current` remains revision equality |
| realization discarded/superseded | preserve old pixels; show `STALE` if desired != realized |
| artifact materialized/authorized | store immutable artifact identity and authorization readback |
| delivery outcome | store exactly `confirmed_success`, `confirmed_failure`, or `unknown`; never map timeout to success/failure |

- Duplicate or older entity revisions are ignored.
- An event-ID gap, `snapshot-required`, or reconnect without replay triggers one `GET /api/studio/snapshot`; the returned snapshot replaces only the server layer.
- `EventSource.onerror` changes connection state to `reconnecting` and shows a persistent header indicator; it does not clear jobs or infer interruption.
- Late success from a superseded/cancelled generation may appear in job history but cannot update canonical realization unless the server payload proves it was accepted for the current desired revision.

### Immediate STOP

- Header always shows active/queued counts and an enabled `STOP` whenever any job is stoppable.
- Pressing STOP immediately sends the stop request—no confirmation dialog—and marks only `stopRequested: true` locally.
- The job remains running until authoritative SSE/snapshot readback says `interrupted`/terminal.
- Accepted desired intent remains. Existing pixels remain visible and become/remain `STALE` whenever revisions differ.
- `QueuePopover` shows every queued/running job, target cut, desired revision, progress, and per-job STOP. The persistent header summary ensures queue visibility even while the popover is closed.

## 9. Canonical review and release flow

1. `검토물 생성` is enabled only when exactly five cuts are Current and there are no unsaved/failed/conflicting edits.
2. FastAPI materializes and returns an immutable artifact identity: at minimum `artifact_id`, content hash, composition revision, five desired/realized revisions, and asset URL.
3. `CanonicalReviewDialog` displays the returned image bytes with contain/zoom only. No DOM text or bubble reconstruction occurs.
4. `승인` posts the exact artifact ID/hash currently displayed.
5. Any later accepted receiver-visible change invalidates authorization immediately. UI derives this from authoritative response/SSE.
6. Export/publish submits only the authorized artifact identity. Missing cut/composition mismatch blocks the request; no partial payload path exists.
7. Blogger/network timeout is shown as `발행 결과 미확인` until destination readback resolves it. Authorization and delivery are never combined into one status.

## 10. Component tree

```text
App
└─ StudioShell
   ├─ StudioHeader
   │  ├─ TruthSummary                  # execution/currency/auth/delivery separate
   │  ├─ QueueSummary
   │  ├─ ImmediateStopButton
   │  └─ QueuePopover
   ├─ CutRail
   │  └─ CutCard × exactly 5
   │     ├─ RevisionPair
   │     ├─ CurrencyBadge              # CURRENT or STALE
   │     └─ CutJobStatus
   ├─ CanvasRegion
   │  ├─ CanvasToolbar                 # select/zoom/pan/review trigger
   │  ├─ CompositionCanvas
   │  │  ├─ CutLayer × 5
   │  │  ├─ BubbleLayer
   │  │  │  └─ BubbleOverlay × N
   │  │  │     ├─ ResizeHandles
   │  │  │     └─ BubbleMenu
   │  │  └─ ProjectionStatusOverlay    # unsaved/conflict/STALE
   │  └─ CanvasStatusBar               # zoom, coordinates, save state
   ├─ InspectorPanel
   │  ├─ CutIntentEditor
   │  ├─ BubbleTextEditor
   │  ├─ BubbleGeometryEditor
   │  ├─ BubbleStyleEditor
   │  └─ SaveStateNotice
   ├─ CanonicalReviewDialog
   ├─ RebaselineDialog
   └─ ToastRegion
```

## 11. Source directory

```text
frontend/src/
  main.ts
  App.vue
  api/
    client.ts                       # typed fetch + ApiError
    events.ts                       # EventSource lifecycle and decoding
    contracts.ts                    # wire DTOs only
  store/
    studio.ts                       # sole Pinia store/actions/selectors
    types.ts                        # client state types
  components/
    shell/StudioShell.vue
    shell/StudioHeader.vue
    shell/TruthSummary.vue
    cuts/CutRail.vue
    cuts/CutCard.vue
    canvas/CanvasRegion.vue
    canvas/CompositionCanvas.vue
    canvas/BubbleLayer.vue
    canvas/BubbleOverlay.vue
    canvas/CanvasToolbar.vue
    inspector/InspectorPanel.vue
    inspector/BubbleTextEditor.vue
    inspector/BubbleGeometryEditor.vue
    review/CanonicalReviewDialog.vue
    jobs/QueuePopover.vue
    feedback/ToastRegion.vue
  composables/
    useBubblePointer.ts             # pointer math and capture only
    useStudioEvents.ts              # store-facing SSE lifecycle
  domain/
    geometry.ts                     # clamp/normalize/round pure functions
    currency.ts                     # revision-derived selectors
  styles/
    tokens.css
    base.css
    studio.css
```

Do not add repository/service/controller layers on the client. `api/client.ts` owns transport, the sole store owns domain transitions, pure `domain` functions own testable math, and components own rendering/ephemeral interaction.

## 12. Thesis invariants and counterexample gates

| Thesis requirement | Frontend enforcement |
|---|---|
| INV-1 single intent/baseline | one server snapshot; exactly five stable cut IDs; re-baseline is explicit |
| INV-2 monotonic realization | revision-gated SSE; late/superseded results cannot replace canonical cut |
| INV-3 truthful currency | `Current` only by desired/realized equality; execution is separate; visible STALE badge |
| INV-4 canonical artifact | modal displays immutable artifact bytes; delivery references artifact identity |
| INV-5 immediate revocation | accepted receiver-visible change consumes server revocation readback; no local approval shadow |
| INV-6 complete/honest release | review/release gate requires all five Current; delivery has success/failure/unknown |
| INV-7 durable interruption | STOP changes job truth only; desired intent and prior pixels remain, with STALE indication |
| INV-8 durable authority | server snapshot is authority; drafts/SSE/cache never become a competing authority |
| Gate 1 Currency | `realizationComplete` cannot be true with any revision mismatch |
| Gate 2 Identity | authorization is bound to exact artifact identity and disappears after accepted change |
| Gate 3 Interruption | STOP cannot clear intent or claim terminal state before readback |
| Gate 4 External truth | network ambiguity remains `unknown`; local state cannot claim publication |

## 13. Implementation order and proof gates

1. Bootstrap Vue/Vite and FastAPI static-package contract; prove `comic-new serve` serves generated `/` and hashed asset.
2. Implement store types, snapshot load, and revision-derived selectors; prove one stale cut prevents Complete.
3. Implement shell/three columns and responsive edge panels; render-check desktop and narrow viewport.
4. Implement native PointerEvent move/resize; interaction-check at 100% and zoomed scale, including pointercancel and keyboard movement.
5. Implement serialized save isolation; reproduce 409 and 500 and verify draft retention, persistent marker, and toast.
6. Implement SSE revision gating/queue/STOP; prove a late superseded completion cannot make a cut Current and STOP preserves desired intent.
7. Implement canonical artifact review/authorization/delivery; prove a one-character accepted edit invalidates authorization and a timeout remains Unknown.

Do not add a feature, abstraction, or dependency beyond the first failing proof that requires it.
