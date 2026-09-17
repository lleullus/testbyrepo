/** Wire DTOs — exact Plan §3 contract. No client logic here. */

export type Sha256 = string
export type PromptOrigin = 'user' | 'llm_draft' | 'intelligent_default'
export type CutId = number
export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'interrupted' | 'superseded'
export type DeliveryOutcome = 'unknown' | 'confirmed_success' | 'confirmed_failure'

export interface ApiErrorDTO {
  error: {
    code:
      | 'validation_error'
      | 'conflict'
      | 'not_found'
      | 'realization_incomplete'
      | 'artifact_not_current'
      | 'runner_busy'
      | 'process_settlement_failed'
      | 'baseline_required'
      | 'invalid_path'
      | 'draft_service_unavailable'
      | 'draft_generation_failed'
      | 'internal_error'
    message: string
    expected_revision?: number
    actual_revision?: number
    current_snapshot?: StudioSnapshotDTO
    details?: Record<string, unknown>
  }
}

export interface DraftCutDTO {
  draft_id: string
  display_order: number
  role: string
  beat: string
  dialogue: string
  prompt: string
}

export type DraftAttemptOutcome = 'succeeded' | 'failed'
export type DraftAttemptCategory =
  | 'timeout'
  | 'connection'
  | 'rate_limited'
  | 'upstream_5xx'
  | 'invalid_response'
  | 'budget_exhausted'

export interface DraftAttemptDTO {
  model: string
  reasoning_effort: string
  outcome: DraftAttemptOutcome
  status_code: number | null
  elapsed_ms: number
  category?: DraftAttemptCategory
}

export interface DraftGenerationResponseDTO {
  source_brief: string
  cut_count: number
  cuts: DraftCutDTO[]
  provenance: {
    provider: string
    selected_model: string
    attempts: DraftAttemptDTO[]
  }
}

export interface BaselineStructureDTO {
  source_brief: string
  cuts: Array<{ cut_id: CutId; role: string; beat: string }>
}

export interface CutIntentInputDTO {
  prompt: string
  dialogue: string
}
export interface BaselineCutIntentInputDTO extends CutIntentInputDTO {
  prompt_origin: PromptOrigin
}

export interface CutIntentDTO extends CutIntentInputDTO {
  prompt_origin: PromptOrigin
}

export interface LegacyGlobalRectDTO {
  x_pct: number
  y_pct: number
  w_pct: number
  h_pct: number
}

interface BubbleStyleDTO {
  bubble_id: string
  cut_id: CutId
  shape: 'ellipse' | 'rounded_rectangle'
  text: string
  font_size_pct: number
  line_spacing_pct: number
  text_align: 'left' | 'center' | 'right'
  text_rgba: string
  fill_rgba: string
  outline_rgba: string
  outline_width_pct: number
  padding_pct: number
}

export interface AnchoredBubbleDTO extends BubbleStyleDTO {
  anchor_status: 'ANCHORED'
  local_x_pct: number
  local_y_pct: number
  local_w_pct: number
  local_h_pct: number
}

export interface ReanchorRequiredBubbleDTO extends BubbleStyleDTO {
  anchor_status: 'REANCHOR_REQUIRED'
  legacy_global_rect: LegacyGlobalRectDTO
}

export type BubbleDTO = AnchoredBubbleDTO | ReanchorRequiredBubbleDTO

export interface CompositionStateDTO {
  schema_version: 2
  canvas_width_px: 1024
  gap_px: number
  slot_heights_px: number[]
  fit: 'contain'
  font_sha256: Sha256
  bubbles: BubbleDTO[]
}

export interface CutDTO {
  cut_id: CutId
  display_order: number
  desired_revision: number | null
  latest_generation_request_seq: number
  effective_intent: CutIntentDTO | null
  realized_revision: number | null
  realized_asset_id: string | null
  realized_content_hash: Sha256 | null
  realized_asset_url: string | null
  currency: 'CURRENT' | 'STALE'
}

export interface JobAttemptDTO {
  attempt_id: string
  ordinal: number
  status: string
  started_at: string
  finished_at: string | null
  detail: string | null
  provider_request_id: string | null
}

export interface JobDTO {
  job_id: string
  cut_id: CutId
  target_desired_revision: number
  request_seq: number
  model: string
  effective_prompt: string
  effective_prompt_origin: PromptOrigin
  effective_prompt_sha256: Sha256
  status: JobStatus
  terminal_detail: string | null
  created_at: string
  updated_at: string
  attempts: JobAttemptDTO[]
}

export interface ReviewArtifactSummaryDTO {
  artifact_id: string
  content_hash: Sha256
  composition_revision: number
  created_at: string
  cuts: Array<{ cut_id: CutId; display_order: number; realized_revision: number; asset_id: string }>
  asset_url: string
}

export interface ReviewArtifactDTO extends ReviewArtifactSummaryDTO {
  cuts: Array<{
    cut_id: CutId
    display_order: number
    desired_revision: number
    realized_revision: number
    asset_id: string
    source_content_hash: Sha256
  }>
}

export interface AuthorizationDTO {
  authorization_id: string
  artifact_id: string
  artifact_content_hash: Sha256
  authorized_authority_revision: number
  created_at: string
  revoked_authority_revision?: number
  revoked_at?: string
}

export interface DeliveryAttemptDTO {
  attempt_id: string
  kind: 'png' | 'blogger'
  authorization_id: string
  artifact_id: string
  request_id: string
  outcome: DeliveryOutcome
  destination_id: string | null
  destination_url: string | null
  evidence: unknown | null
  observed_authority_revision: number | null
  created_at: string
  updated_at: string
}

export interface GenerationControlDTO {
  stop_epoch: number
  runner_id: string | null
  runner_pid: number | null
  runner_start_token: string | null
  runner_started_at: string | null
}

export interface ResolvedSlotDTO {
  cut_id: number
  top_px: number
  bottom_px: number
  height_px: number
}

export interface RenderContractDTO {
  width_px: 1024
  height_px: number
  gap_px: number
  fit: 'contain'
  slots: ResolvedSlotDTO[]
  default_composition: CompositionStateDTO
}

export interface StudioSnapshotDTO {
  schema_version: 7
  authority_revision: number
  baseline: null | {
    baseline_id: string
    structure: BaselineStructureDTO
    authority_revision: number
    created_at: string
    intents: Array<{ cut_id: CutId; intent_revision: number }>
  }
  cuts: CutDTO[]
  realization_complete: { complete: boolean; status: 'COMPLETE' | 'UNRESOLVED' }
  composition: { revision: number; state: CompositionStateDTO | null; updated_at: string }
  render_contract: RenderContractDTO
  jobs: JobDTO[]
  review_artifacts: ReviewArtifactSummaryDTO[]
  release_authorization: { active: AuthorizationDTO | null; history: AuthorizationDTO[] }
  delivery_attempts: DeliveryAttemptDTO[]
  generation_control: GenerationControlDTO
}

export interface ExportPngRequest {
  expected_authority_revision: number
  output_path?: string
}

export interface ExportPngResponse {
  attempt_id: string
  kind: 'png'
  authorization_id: string
  artifact_id: string
  output_path: string
  content_hash: Sha256
  bytes_written: number
  snapshot: StudioSnapshotDTO
}

export interface BloggerReleaseRequest {
  expected_authority_revision: number
  blog_id?: string
  title?: string
}

export interface BloggerReleaseResponse {
  attempt_id: string
  kind: 'blogger'
  authorization_id: string
  artifact_id: string
  outcome: DeliveryOutcome
  destination_id: string | null
  destination_url: string | null
  snapshot: StudioSnapshotDTO
}

// --- Runtime StudioSnapshotDTO Validator ---

const SHA256_REGEX = /^[0-9a-fA-F]{64}$/

function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

function isNonNegativeSafeInt(v: unknown): v is number {
  return typeof v === 'number' && Number.isSafeInteger(v) && v >= 0
}

function isSha256(v: unknown): v is Sha256 {
  return typeof v === 'string' && SHA256_REGEX.test(v)
}

function isPromptOrigin(v: unknown): v is PromptOrigin {
  return v === 'user' || v === 'llm_draft' || v === 'intelligent_default'
}

function hasOnlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const allowed: Record<string, true> = {}
  for (const key of keys) allowed[key] = true
  return Object.keys(value).every((key) => allowed[key] === true)
}

function isDraftCutDTO(value: unknown): value is DraftCutDTO {
  if (!isObject(value)) return false
  if (!hasOnlyKeys(value, ['draft_id', 'display_order', 'role', 'beat', 'dialogue', 'prompt'])) return false
  if (typeof value.draft_id !== 'string' || !value.draft_id.trim()) return false
  if (!isPositiveSafeInt(value.display_order)) return false
  if (typeof value.role !== 'string' || !value.role.trim()) return false
  if (typeof value.beat !== 'string' || !value.beat.trim()) return false
  if (typeof value.dialogue !== 'string') return false
  if (typeof value.prompt !== 'string' || !value.prompt.trim()) return false
  const prompt = value.prompt.toLowerCase()
  if (/same\s+as\s+(?:the\s+)?(?:previous|prior|earlier|above|preceding|last|before)|character\s+as\s+(?:above|before)|same\s+character\s+as|as\s+(?:stated\s+)?(?:above|before)|ditto|refer\s+to\s+(?:the\s+)?(?:previous|prior|earlier|last|above)|continue\s+from\s+(?:the\s+)?(?:previous|prior|earlier|last)|이전\s*(?:컷|장면)과\s*(?:동일|같)|앞\s*(?:컷|장면)과\s*같|위와\s*(?:동일|같)/i.test(value.prompt)) return false
  if (!/negative\s+space/.test(prompt)) return false
  if (!/speech\s+(?:balloon|bubble)s?|말풍선/.test(prompt)) return false
  if (!/no\s+(?:rendered\s+)?text/.test(prompt) || !/no\s+[^.]{0,120}\btypography\b|typography\s+(?:must\s+not|not|is\s+prohibited|rendered)/.test(prompt)) return false
  return true
}

function isDraftAttemptDTO(value: unknown): value is DraftAttemptDTO {
  if (!isObject(value)) return false
  if (!hasOnlyKeys(value, ['model', 'reasoning_effort', 'outcome', 'status_code', 'elapsed_ms', 'category'])) return false
  if (typeof value.model !== 'string' || !value.model.trim()) return false
  if (typeof value.reasoning_effort !== 'string' || !value.reasoning_effort.trim()) return false
  if (value.outcome !== 'succeeded' && value.outcome !== 'failed') return false
  if (value.status_code !== null && !isNonNegativeSafeInt(value.status_code)) return false
  if (!isNonNegativeSafeInt(value.elapsed_ms)) return false
  if (value.category !== undefined && value.category !== null && !isDraftAttemptCategory(value.category)) return false
  if (value.outcome === 'failed' && !isDraftAttemptCategory(value.category)) return false
  return true
}

function isPositiveSafeInt(v: unknown): v is number {
  return typeof v === 'number' && Number.isSafeInteger(v) && v >= 1
}

function isDraftAttemptCategory(v: unknown): v is DraftAttemptCategory {
  return v === 'timeout' || v === 'connection' || v === 'rate_limited' ||
    v === 'upstream_5xx' || v === 'invalid_response' || v === 'budget_exhausted'
}

export function isDraftGenerationResponseDTO(value: unknown): value is DraftGenerationResponseDTO {
  if (!isObject(value)) return false
  if (!hasOnlyKeys(value, ['source_brief', 'cut_count', 'cuts', 'provenance'])) return false
  if (typeof value.source_brief !== 'string' || !value.source_brief.trim()) return false
  if (!isPositiveSafeInt(value.cut_count)) return false
  if (!Array.isArray(value.cuts) || value.cuts.length !== value.cut_count) return false
  const identities = new Set<string>()
  for (let index = 0; index < value.cuts.length; index++) {
    const cut = value.cuts[index]
    if (!isDraftCutDTO(cut) || cut.display_order !== index + 1 || identities.has(cut.draft_id.trim())) return false
    identities.add(cut.draft_id.trim())
  }
  if (!isObject(value.provenance) || !hasOnlyKeys(value.provenance, ['provider', 'selected_model', 'attempts'])) return false
  if (value.provenance.provider !== 'opencodex' || typeof value.provenance.selected_model !== 'string' || !value.provenance.selected_model.trim()) return false
  if (!Array.isArray(value.provenance.attempts) || value.provenance.attempts.length === 0) return false
  for (const attempt of value.provenance.attempts) {
    if (!isDraftAttemptDTO(attempt)) return false
  }
  const last = value.provenance.attempts[value.provenance.attempts.length - 1]
  if (last.outcome !== 'succeeded' || last.model !== value.provenance.selected_model) return false
  return true
}

export function validateDraftGenerationResponse(value: unknown): DraftGenerationResponseDTO {
  if (!isDraftGenerationResponseDTO(value)) {
    throw new Error('Invalid draft generation response payload')
  }
  return value
}

function isCutId(v: unknown): v is CutId {
  return isPositiveSafeInt(v)
}

function isJobStatus(v: unknown): v is JobStatus {
  return v === 'queued' || v === 'running' || v === 'succeeded' || v === 'failed' ||
    v === 'cancelled' || v === 'interrupted' || v === 'superseded'
}

function isDeliveryOutcome(v: unknown): v is DeliveryOutcome {
  return v === 'unknown' || v === 'confirmed_success' || v === 'confirmed_failure'
}

function isBubbleStyleDTO(v: Record<string, unknown>): boolean {
  return typeof v.bubble_id === 'string' && v.bubble_id.trim().length > 0 && isCutId(v.cut_id) &&
    (v.shape === 'ellipse' || v.shape === 'rounded_rectangle') && typeof v.text === 'string' &&
    typeof v.font_size_pct === 'number' && Number.isFinite(v.font_size_pct) && v.font_size_pct > 0 &&
    typeof v.line_spacing_pct === 'number' && Number.isFinite(v.line_spacing_pct) && v.line_spacing_pct >= 0 &&
    (v.text_align === 'left' || v.text_align === 'center' || v.text_align === 'right') &&
    typeof v.text_rgba === 'string' && typeof v.fill_rgba === 'string' && typeof v.outline_rgba === 'string' &&
    typeof v.outline_width_pct === 'number' && Number.isFinite(v.outline_width_pct) && v.outline_width_pct >= 0 &&
    typeof v.padding_pct === 'number' && Number.isFinite(v.padding_pct) && v.padding_pct >= 0
}

function isLocalRect(v: Record<string, unknown>): boolean {
  return typeof v.local_x_pct === 'number' && Number.isFinite(v.local_x_pct) && v.local_x_pct >= 0 &&
    typeof v.local_y_pct === 'number' && Number.isFinite(v.local_y_pct) && v.local_y_pct >= 0 &&
    typeof v.local_w_pct === 'number' && Number.isFinite(v.local_w_pct) && v.local_w_pct > 0 &&
    typeof v.local_h_pct === 'number' && Number.isFinite(v.local_h_pct) && v.local_h_pct > 0 &&
    v.local_x_pct + v.local_w_pct <= 100 && v.local_y_pct + v.local_h_pct <= 100
}

function isLegacyGlobalRect(v: unknown): v is LegacyGlobalRectDTO {
  if (!isObject(v) || !hasOnlyKeys(v, ['x_pct', 'y_pct', 'w_pct', 'h_pct'])) return false
  return typeof v.x_pct === 'number' && Number.isFinite(v.x_pct) &&
    typeof v.y_pct === 'number' && Number.isFinite(v.y_pct) &&
    typeof v.w_pct === 'number' && Number.isFinite(v.w_pct) &&
    typeof v.h_pct === 'number' && Number.isFinite(v.h_pct)
}

function isBubbleDTO(v: unknown): v is BubbleDTO {
  if (!isObject(v) || !isBubbleStyleDTO(v)) return false
  if (v.anchor_status === 'ANCHORED') {
    return hasOnlyKeys(v, ['anchor_status', 'bubble_id', 'cut_id', 'shape', 'local_x_pct', 'local_y_pct', 'local_w_pct', 'local_h_pct', 'text', 'font_size_pct', 'line_spacing_pct', 'text_align', 'text_rgba', 'fill_rgba', 'outline_rgba', 'outline_width_pct', 'padding_pct']) && isLocalRect(v)
  }
  return v.anchor_status === 'REANCHOR_REQUIRED' &&
    hasOnlyKeys(v, ['anchor_status', 'bubble_id', 'cut_id', 'shape', 'legacy_global_rect', 'text', 'font_size_pct', 'line_spacing_pct', 'text_align', 'text_rgba', 'fill_rgba', 'outline_rgba', 'outline_width_pct', 'padding_pct']) &&
    isLegacyGlobalRect(v.legacy_global_rect)
}

function isCompositionStateDTO(v: unknown): v is CompositionStateDTO {
  if (!isObject(v) || !hasOnlyKeys(v, ['schema_version', 'canvas_width_px', 'gap_px', 'slot_heights_px', 'fit', 'font_sha256', 'bubbles'])) return false
  if (v.schema_version !== 2 || v.canvas_width_px !== 1024 || !isNonNegativeSafeInt(v.gap_px) || v.fit !== 'contain' || !isSha256(v.font_sha256)) return false
  if (!Array.isArray(v.slot_heights_px) || v.slot_heights_px.length === 0 || v.slot_heights_px.some((h) => !isPositiveSafeInt(h))) return false
  if (!Array.isArray(v.bubbles)) return false
  const ids = new Set<string>()
  for (const b of v.bubbles) {
    if (!isBubbleDTO(b) || ids.has(b.bubble_id)) return false
    ids.add(b.bubble_id)
  }
  return true
}

function isResolvedSlotDTO(v: unknown): v is ResolvedSlotDTO {
  return isObject(v) && hasOnlyKeys(v, ['cut_id', 'top_px', 'bottom_px', 'height_px']) &&
    isCutId(v.cut_id) && isNonNegativeSafeInt(v.top_px) && isPositiveSafeInt(v.height_px) &&
    isPositiveSafeInt(v.bottom_px) && v.bottom_px - v.top_px === v.height_px
}

function isRenderContractDTO(v: unknown): v is RenderContractDTO {
  if (!isObject(v) || !hasOnlyKeys(v, ['width_px', 'height_px', 'gap_px', 'fit', 'slots', 'default_composition'])) return false
  if (v.width_px !== 1024 || !isPositiveSafeInt(v.height_px) || !isNonNegativeSafeInt(v.gap_px) || v.fit !== 'contain' || !Array.isArray(v.slots) || v.slots.length === 0 || !isCompositionStateDTO(v.default_composition)) return false
  const ids = new Set<number>()
  let cursor = 0
  for (let i = 0; i < v.slots.length; i += 1) {
    const slot = v.slots[i]
    if (!isResolvedSlotDTO(slot) || ids.has(slot.cut_id) || slot.top_px !== cursor) return false
    ids.add(slot.cut_id)
    cursor = slot.bottom_px + (i < v.slots.length - 1 ? v.gap_px : 0)
  }
  return cursor === v.height_px && v.default_composition.slot_heights_px.length === v.slots.length
}

function isBaselineStructureDTO(v: unknown): v is BaselineStructureDTO {
  if (!isObject(v) || typeof v.source_brief !== 'string' || !Array.isArray(v.cuts) || v.cuts.length === 0) return false
  const ids = new Set<number>()
  for (const c of v.cuts) {
    if (!isObject(c) || !isCutId(c.cut_id) || ids.has(c.cut_id) || typeof c.role !== 'string' || typeof c.beat !== 'string') return false
    ids.add(c.cut_id)
  }
  return true
}

function isCutIntentDTO(v: unknown): v is CutIntentDTO {
  if (!isObject(v)) return false
  return typeof v.prompt === 'string' && typeof v.dialogue === 'string' && isPromptOrigin(v.prompt_origin)
}
function isCutDTO(v: unknown, expectedCutId: CutId): v is CutDTO {
  if (!isObject(v) || v.cut_id !== expectedCutId || !isPositiveSafeInt(v.display_order)) return false
  if (v.desired_revision !== null && !isNonNegativeSafeInt(v.desired_revision)) return false
  if (!isNonNegativeSafeInt(v.latest_generation_request_seq)) return false
  if (v.effective_intent !== null && !isCutIntentDTO(v.effective_intent)) return false
  if (v.realized_revision === null) {
    if (v.realized_asset_id !== null || v.realized_content_hash !== null || v.realized_asset_url !== null) {
      return false
    }
  } else {
    if (
      !isNonNegativeSafeInt(v.realized_revision) ||
      typeof v.realized_asset_id !== 'string' ||
      !isSha256(v.realized_content_hash) ||
      (v.realized_asset_url !== null && typeof v.realized_asset_url !== 'string')
    ) {
      return false
    }
  }
  if (v.currency !== 'CURRENT' && v.currency !== 'STALE') return false
  if (
    v.currency === 'CURRENT' &&
    (v.desired_revision === null ||
      v.realized_revision === null ||
      v.desired_revision !== v.realized_revision)
  ) {
    return false
  }
  return true
}

function isJobAttemptDTO(v: unknown): v is JobAttemptDTO {
  if (!isObject(v)) return false
  if (typeof v.attempt_id !== 'string') return false
  if (!isNonNegativeSafeInt(v.ordinal)) return false
  if (typeof v.status !== 'string') return false
  if (typeof v.started_at !== 'string') return false
  if (v.finished_at !== null && typeof v.finished_at !== 'string') return false
  if (v.detail !== null && typeof v.detail !== 'string') return false
  if (v.provider_request_id !== null && typeof v.provider_request_id !== 'string') return false
  return true
}

function isJobDTO(v: unknown): v is JobDTO {
  if (!isObject(v)) return false
  if (typeof v.job_id !== 'string') return false
  if (!isCutId(v.cut_id)) return false
  if (!isNonNegativeSafeInt(v.target_desired_revision)) return false
  if (!isNonNegativeSafeInt(v.request_seq)) return false
  if (typeof v.model !== 'string' || !v.model.trim()) return false
  if (typeof v.effective_prompt !== 'string' || !v.effective_prompt.trim()) return false
  if (!isPromptOrigin(v.effective_prompt_origin)) return false
  if (!isSha256(v.effective_prompt_sha256)) return false
  if (!isJobStatus(v.status)) return false
  if (v.terminal_detail !== null && typeof v.terminal_detail !== 'string') return false
  if (typeof v.created_at !== 'string') return false
  if (typeof v.updated_at !== 'string') return false
  if (!Array.isArray(v.attempts)) return false
  for (const a of v.attempts) {
    if (!isJobAttemptDTO(a)) return false
  }
  return true
}

function isReviewArtifactSummaryDTO(v: unknown): v is ReviewArtifactSummaryDTO {
  if (!isObject(v) || typeof v.artifact_id !== 'string' || !isSha256(v.content_hash) || !isNonNegativeSafeInt(v.composition_revision) || typeof v.created_at !== 'string' || typeof v.asset_url !== 'string' || !Array.isArray(v.cuts)) return false
  const ids = new Set<number>()
  for (let index = 0; index < v.cuts.length; index += 1) {
    const c = v.cuts[index]
    if (!isObject(c) || !isCutId(c.cut_id) || !isPositiveSafeInt(c.display_order) || c.display_order !== index + 1 || ids.has(c.cut_id) || !isNonNegativeSafeInt(c.realized_revision) || typeof c.asset_id !== 'string') return false
    ids.add(c.cut_id)
  }
  return true
}

function isAuthorizationDTO(v: unknown): v is AuthorizationDTO {
  if (!isObject(v)) return false
  if (typeof v.authorization_id !== 'string') return false
  if (typeof v.artifact_id !== 'string') return false
  if (!isSha256(v.artifact_content_hash)) return false
  if (!isNonNegativeSafeInt(v.authorized_authority_revision)) return false
  if (typeof v.created_at !== 'string') return false
  if (
    v.revoked_authority_revision !== undefined &&
    v.revoked_authority_revision !== null &&
    !isNonNegativeSafeInt(v.revoked_authority_revision)
  ) {
    return false
  }
  if (
    v.revoked_at !== undefined &&
    v.revoked_at !== null &&
    typeof v.revoked_at !== 'string'
  ) {
    return false
  }
  return true
}

function isDeliveryAttemptDTO(v: unknown): v is DeliveryAttemptDTO {
  if (!isObject(v)) return false
  if (typeof v.attempt_id !== 'string') return false
  if (v.kind !== 'png' && v.kind !== 'blogger') return false
  if (typeof v.authorization_id !== 'string') return false
  if (typeof v.artifact_id !== 'string') return false
  if (typeof v.request_id !== 'string') return false
  if (!isDeliveryOutcome(v.outcome)) return false
  if (v.destination_id !== null && typeof v.destination_id !== 'string') return false
  if (v.destination_url !== null && typeof v.destination_url !== 'string') return false
  if (v.observed_authority_revision !== null && !isNonNegativeSafeInt(v.observed_authority_revision)) {
    return false
  }
  if (typeof v.created_at !== 'string') return false
  if (typeof v.updated_at !== 'string') return false
  return true
}

function isGenerationControlDTO(v: unknown): v is GenerationControlDTO {
  if (!isObject(v)) return false
  if (!isNonNegativeSafeInt(v.stop_epoch)) return false
  if (v.runner_id !== null && typeof v.runner_id !== 'string') return false
  if (v.runner_pid !== null && (!Number.isSafeInteger(v.runner_pid) || (v.runner_pid as number) < 0)) {
    return false
  }
  if (v.runner_start_token !== null && typeof v.runner_start_token !== 'string') return false
  if (v.runner_started_at !== null && typeof v.runner_started_at !== 'string') return false
  return true
}

export function isStudioSnapshotDTO(v: unknown): v is StudioSnapshotDTO {
  if (!isObject(v) || v.schema_version !== 7 || !isNonNegativeSafeInt(v.authority_revision)) return false
  if (v.baseline !== null) {
    if (!isObject(v.baseline) || typeof v.baseline.baseline_id !== 'string' || !isBaselineStructureDTO(v.baseline.structure) || !isNonNegativeSafeInt(v.baseline.authority_revision) || typeof v.baseline.created_at !== 'string') return false
    if (!Array.isArray(v.baseline.intents) || v.baseline.intents.length !== v.baseline.structure.cuts.length) return false
    for (let index = 0; index < v.baseline.intents.length; index += 1) {
      const intent = v.baseline.intents[index]
      if (!isObject(intent) || intent.cut_id !== v.baseline.structure.cuts[index].cut_id || !isNonNegativeSafeInt(intent.intent_revision)) return false
    }
  }
  if (!Array.isArray(v.cuts) || v.cuts.length === 0) return false
  const cutIds = new Set<number>()
  for (let index = 0; index < v.cuts.length; index += 1) {
    const cut = v.cuts[index]
    if (!isObject(cut) || !isCutId(cut.cut_id) || cutIds.has(cut.cut_id) || !isCutDTO(cut, cut.cut_id) || cut.display_order !== index + 1) return false
    cutIds.add(cut.cut_id)
  }
  if (v.baseline === null) {
    if (v.cuts.some((cut) => cut.desired_revision !== null || cut.effective_intent !== null)) return false
  } else {
    if ((v.baseline.structure as BaselineStructureDTO).cuts.map((cut) => cut.cut_id).join(',') !== v.cuts.map((cut) => cut.cut_id).join(',')) return false
    if (v.cuts.some((cut) => cut.desired_revision === null || cut.effective_intent === null)) return false
  }
  if (!isObject(v.realization_complete) || typeof v.realization_complete.complete !== 'boolean' || (v.realization_complete.status !== 'COMPLETE' && v.realization_complete.status !== 'UNRESOLVED')) return false
  const allCutsCurrent = v.cuts.every((cut) => cut.currency === 'CURRENT' && cut.desired_revision !== null && cut.desired_revision === cut.realized_revision)
  if (v.realization_complete.complete !== allCutsCurrent || v.realization_complete.status !== (allCutsCurrent ? 'COMPLETE' : 'UNRESOLVED')) return false
  if (!isObject(v.composition) || !isNonNegativeSafeInt(v.composition.revision) || typeof v.composition.updated_at !== 'string' || (v.composition.state !== null && !isCompositionStateDTO(v.composition.state))) return false
  if (!isRenderContractDTO(v.render_contract)) return false
  if (v.render_contract.slots.map((slot) => slot.cut_id).join(',') !== v.cuts.map((cut) => cut.cut_id).join(',')) return false
  if (!Array.isArray(v.jobs) || v.jobs.some((job) => !isJobDTO(job))) return false
  for (const cut of v.cuts) {
    const cutJobs = v.jobs.filter((job) => job.cut_id === cut.cut_id)
    if (cutJobs.some((job) => job.request_seq > cut.latest_generation_request_seq)) return false
    const latestJobs = cutJobs.filter((job) => job.request_seq === cut.latest_generation_request_seq)
    if (cut.latest_generation_request_seq === 0 ? latestJobs.length !== 0 : latestJobs.length !== 1) return false
    const revisionsMatch = cut.desired_revision !== null && cut.realized_revision !== null && cut.desired_revision === cut.realized_revision
    const sequenceCurrent = cut.latest_generation_request_seq === 0 || latestJobs[0]?.status === 'succeeded'
    if ((cut.currency === 'CURRENT') !== (revisionsMatch && sequenceCurrent)) return false
  }
  if (!Array.isArray(v.review_artifacts) || v.review_artifacts.some((art) => !isReviewArtifactSummaryDTO(art))) return false
  if (!isObject(v.release_authorization) || (v.release_authorization.active !== null && !isAuthorizationDTO(v.release_authorization.active)) || !Array.isArray(v.release_authorization.history) || v.release_authorization.history.some((auth) => !isAuthorizationDTO(auth))) return false
  if (!Array.isArray(v.delivery_attempts) || v.delivery_attempts.some((da) => !isDeliveryAttemptDTO(da))) return false
  return isGenerationControlDTO(v.generation_control)
}

export function validateStudioSnapshot(value: unknown): StudioSnapshotDTO {
  if (!isStudioSnapshotDTO(value)) {
    throw new Error('Invalid studio snapshot payload')
  }
  return value
}

