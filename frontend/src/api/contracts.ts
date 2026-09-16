/** Wire DTOs — exact Plan §3 contract. No client logic here. */

export type Sha256 = string
export type CutId = 1 | 2 | 3 | 4 | 5
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
      | 'internal_error'
    message: string
    expected_revision?: number
    actual_revision?: number
    current_snapshot?: StudioSnapshotDTO
  }
}

export interface BaselineStructureDTO {
  source_brief: string
  cuts: [
    { cut_id: 1; role: string; beat: string },
    { cut_id: 2; role: string; beat: string },
    { cut_id: 3; role: string; beat: string },
    { cut_id: 4; role: string; beat: string },
    { cut_id: 5; role: string; beat: string },
  ]
}

export interface CutIntentDTO {
  prompt: string
  dialogue: string
}

export interface BubbleDTO {
  bubble_id: string
  cut_id: CutId
  shape: 'ellipse' | 'rounded_rectangle'
  x_pct: number
  y_pct: number
  w_pct: number
  h_pct: number
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

export interface CompositionStateDTO {
  schema_version: 1
  gap_px: number
  font_sha256: Sha256
  bubbles: BubbleDTO[]
}

export interface CutDTO {
  cut_id: CutId
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
  cuts: Array<{ cut_id: CutId; realized_revision: number; asset_id: string }>
  asset_url: string
}

export interface ReviewArtifactDTO extends ReviewArtifactSummaryDTO {
  cuts: Array<{
    cut_id: CutId
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

export interface StudioSnapshotDTO {
  schema_version: 4
  authority_revision: number
  baseline: null | {
    baseline_id: string
    structure: BaselineStructureDTO
    authority_revision: number
    created_at: string
    intents: Array<{ cut_id: CutId; intent_revision: number }>
  }
  cuts: [CutDTO, CutDTO, CutDTO, CutDTO, CutDTO]
  realization_complete: { complete: boolean; status: 'COMPLETE' | 'UNRESOLVED' }
  composition: { revision: number; state: CompositionStateDTO | null; updated_at: string }
  render_contract: { width: 1024; height: 7680; default_composition: CompositionStateDTO }
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

function isCutId(v: unknown): v is CutId {
  return v === 1 || v === 2 || v === 3 || v === 4 || v === 5
}

function isJobStatus(v: unknown): v is JobStatus {
  return (
    v === 'queued' ||
    v === 'running' ||
    v === 'succeeded' ||
    v === 'failed' ||
    v === 'cancelled' ||
    v === 'interrupted' ||
    v === 'superseded'
  )
}

function isDeliveryOutcome(v: unknown): v is DeliveryOutcome {
  return v === 'unknown' || v === 'confirmed_success' || v === 'confirmed_failure'
}

function isBubbleDTO(v: unknown): v is BubbleDTO {
  if (!isObject(v)) return false
  if (typeof v.bubble_id !== 'string') return false
  if (!isCutId(v.cut_id)) return false
  if (v.shape !== 'ellipse' && v.shape !== 'rounded_rectangle') return false
  if (typeof v.x_pct !== 'number' || !Number.isFinite(v.x_pct)) return false
  if (typeof v.y_pct !== 'number' || !Number.isFinite(v.y_pct)) return false
  if (typeof v.w_pct !== 'number' || !Number.isFinite(v.w_pct) || v.w_pct < 0) return false
  if (typeof v.h_pct !== 'number' || !Number.isFinite(v.h_pct) || v.h_pct < 0) return false
  if (typeof v.text !== 'string') return false
  if (typeof v.font_size_pct !== 'number' || !Number.isFinite(v.font_size_pct) || v.font_size_pct <= 0) return false
  if (typeof v.line_spacing_pct !== 'number' || !Number.isFinite(v.line_spacing_pct) || v.line_spacing_pct < 0) return false
  if (v.text_align !== 'left' && v.text_align !== 'center' && v.text_align !== 'right') return false
  if (typeof v.text_rgba !== 'string') return false
  if (typeof v.fill_rgba !== 'string') return false
  if (typeof v.outline_rgba !== 'string') return false
  if (typeof v.outline_width_pct !== 'number' || !Number.isFinite(v.outline_width_pct) || v.outline_width_pct < 0) return false
  if (typeof v.padding_pct !== 'number' || !Number.isFinite(v.padding_pct) || v.padding_pct < 0) return false
  return true
}

function isCompositionStateDTO(v: unknown): v is CompositionStateDTO {
  if (!isObject(v)) return false
  if (v.schema_version !== 1) return false
  if (!isNonNegativeSafeInt(v.gap_px)) return false
  if (!isSha256(v.font_sha256)) return false
  if (!Array.isArray(v.bubbles)) return false
  for (const b of v.bubbles) {
    if (!isBubbleDTO(b)) return false
  }
  return true
}

function isBaselineStructureDTO(v: unknown): v is BaselineStructureDTO {
  if (!isObject(v)) return false
  if (typeof v.source_brief !== 'string') return false
  if (!Array.isArray(v.cuts) || v.cuts.length !== 5) return false
  for (let i = 0; i < 5; i++) {
    const c = v.cuts[i]
    if (!isObject(c)) return false
    if (c.cut_id !== (i + 1)) return false
    if (typeof c.role !== 'string') return false
    if (typeof c.beat !== 'string') return false
  }
  return true
}

function isCutIntentDTO(v: unknown): v is CutIntentDTO {
  if (!isObject(v)) return false
  return typeof v.prompt === 'string' && typeof v.dialogue === 'string'
}

function isCutDTO(v: unknown, expectedCutId: CutId): v is CutDTO {
  if (!isObject(v)) return false
  if (v.cut_id !== expectedCutId) return false
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
  if (!isObject(v)) return false
  if (typeof v.artifact_id !== 'string') return false
  if (!isSha256(v.content_hash)) return false
  if (!isNonNegativeSafeInt(v.composition_revision)) return false
  if (typeof v.created_at !== 'string') return false
  if (typeof v.asset_url !== 'string') return false
  if (!Array.isArray(v.cuts)) return false
  for (const c of v.cuts) {
    if (!isObject(c)) return false
    if (!isCutId(c.cut_id)) return false
    if (!isNonNegativeSafeInt(c.realized_revision)) return false
    if (typeof c.asset_id !== 'string') return false
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
  if (!isObject(v)) return false
  if (v.schema_version !== 4) return false
  if (!isNonNegativeSafeInt(v.authority_revision)) return false

  // baseline
  if (v.baseline !== null) {
    if (!isObject(v.baseline)) return false
    if (typeof v.baseline.baseline_id !== 'string') return false
    if (!isBaselineStructureDTO(v.baseline.structure)) return false
    if (!isNonNegativeSafeInt(v.baseline.authority_revision)) return false
    if (typeof v.baseline.created_at !== 'string') return false
    if (!Array.isArray(v.baseline.intents) || v.baseline.intents.length !== 5) return false
    for (let index = 0; index < v.baseline.intents.length; index++) {
      const intent = v.baseline.intents[index]
      if (!isObject(intent)) return false
      if (intent.cut_id !== index + 1) return false
      if (!isNonNegativeSafeInt(intent.intent_revision)) return false
    }
  }

  // cuts
  if (!Array.isArray(v.cuts) || v.cuts.length !== 5) return false
  for (let i = 0; i < 5; i++) {
    const expectedId = (i + 1) as CutId
    if (!isCutDTO(v.cuts[i], expectedId)) return false
  }
  if (v.baseline === null) {
    if ((v.cuts as CutDTO[]).some((cut) => cut.desired_revision !== null || cut.effective_intent !== null)) {
      return false
    }
  } else if ((v.cuts as CutDTO[]).some((cut) => cut.desired_revision === null || cut.effective_intent === null)) {
    return false
  }

  // realization_complete
  if (!isObject(v.realization_complete)) return false
  if (typeof v.realization_complete.complete !== 'boolean') return false
  if (v.realization_complete.status !== 'COMPLETE' && v.realization_complete.status !== 'UNRESOLVED') {
    return false
  }

  // realization_complete consistency with cuts' CURRENT status
  const allCutsCurrent = (v.cuts as CutDTO[]).every(
    (cut) =>
      cut.currency === 'CURRENT' &&
      cut.desired_revision !== null &&
      cut.desired_revision === cut.realized_revision,
  )
  if (v.realization_complete.complete !== allCutsCurrent) return false
  if (v.realization_complete.status !== (allCutsCurrent ? 'COMPLETE' : 'UNRESOLVED')) return false

  // composition
  if (!isObject(v.composition)) return false
  if (!isNonNegativeSafeInt(v.composition.revision)) return false
  if (typeof v.composition.updated_at !== 'string') return false
  if (v.composition.state !== null && !isCompositionStateDTO(v.composition.state)) return false

  // render_contract
  if (!isObject(v.render_contract)) return false
  if (v.render_contract.width !== 1024 || v.render_contract.height !== 7680) return false
  if (!isCompositionStateDTO(v.render_contract.default_composition)) return false

  // jobs
  if (!Array.isArray(v.jobs)) return false
  for (const job of v.jobs) {
    if (!isJobDTO(job)) return false
  }
  for (const cut of v.cuts as CutDTO[]) {
    const cutJobs = (v.jobs as JobDTO[]).filter((job) => job.cut_id === cut.cut_id)
    if (cutJobs.some((job) => job.request_seq > cut.latest_generation_request_seq)) return false

    const latestJobs = cutJobs.filter(
      (job) => job.request_seq === cut.latest_generation_request_seq,
    )
    if (cut.latest_generation_request_seq === 0) {
      if (latestJobs.length !== 0) return false
    } else if (latestJobs.length !== 1) {
      return false
    }

    const revisionsMatch =
      cut.desired_revision !== null &&
      cut.realized_revision !== null &&
      cut.desired_revision === cut.realized_revision
    const sequenceCurrent =
      cut.latest_generation_request_seq === 0 || latestJobs[0]?.status === 'succeeded'
    if ((cut.currency === 'CURRENT') !== (revisionsMatch && sequenceCurrent)) return false
  }

  // review_artifacts
  if (!Array.isArray(v.review_artifacts)) return false
  for (const art of v.review_artifacts) {
    if (!isReviewArtifactSummaryDTO(art)) return false
  }

  // release_authorization
  if (!isObject(v.release_authorization)) return false
  if (v.release_authorization.active !== null && !isAuthorizationDTO(v.release_authorization.active)) {
    return false
  }
  if (!Array.isArray(v.release_authorization.history)) return false
  for (const auth of v.release_authorization.history) {
    if (!isAuthorizationDTO(auth)) return false
  }

  // delivery_attempts
  if (!Array.isArray(v.delivery_attempts)) return false
  for (const da of v.delivery_attempts) {
    if (!isDeliveryAttemptDTO(da)) return false
  }

  // generation_control
  if (!isGenerationControlDTO(v.generation_control)) return false

  return true
}

export function validateStudioSnapshot(value: unknown): StudioSnapshotDTO {
  if (!isStudioSnapshotDTO(value)) {
    throw new Error('Invalid studio snapshot payload')
  }
  return value
}

