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
  schema_version: 2
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
