/** Typed fetch wrapper for same-origin /api. No Axios/query-cache. */

import type {
  ApiErrorDTO,
  BaselineStructureDTO,
  BloggerReleaseRequest,
  BloggerReleaseResponse,
  CutId,
  CutIntentDTO,
  CompositionStateDTO,
  ExportPngRequest,
  ExportPngResponse,
  JobDTO,
  ReviewArtifactDTO,
  StudioSnapshotDTO,
} from './contracts'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiErrorDTO['error'],
  ) {
    super(body.message)
    this.name = 'ApiError'
  }

  get code() {
    return this.body.code
  }

  get currentSnapshot(): StudioSnapshotDTO | undefined {
    return this.body.current_snapshot
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const init: RequestInit = {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }
  const resp = await fetch(path, init)
  if (!resp.ok) {
    let errBody: ApiErrorDTO['error']
    try {
      const json = await resp.json() as ApiErrorDTO
      errBody = json.error
    } catch {
      errBody = { code: 'internal_error', message: `HTTP ${resp.status}` }
    }
    throw new ApiError(resp.status, errBody)
  }
  return resp.json() as Promise<T>
}

// --- Queries ---

export function fetchSnapshot(): Promise<StudioSnapshotDTO> {
  return request<StudioSnapshotDTO>('GET', '/api/studio/snapshot')
}

export function fetchArtifactMetadata(artifactId: string): Promise<ReviewArtifactDTO> {
  return request<ReviewArtifactDTO>('GET', `/api/review-artifacts/${artifactId}`)
}

export function artifactContentUrl(artifactId: string): string {
  return `/api/review-artifacts/${artifactId}/content`
}

export function cutRealizationUrl(cutId: CutId, assetId: string, revision: number): string {
  return `/api/cuts/${cutId}/realization?asset_id=${encodeURIComponent(assetId)}&revision=${revision}`
}

// --- Mutations ---

interface MutationResponse {
  accepted_mutation_id: string
  snapshot: StudioSnapshotDTO
}

export function postBaseline(payload: {
  expected_authority_revision: number
  mutation_id: string
  baseline_id: string
  structure: BaselineStructureDTO
  intents: Array<{ cut_id: CutId; intent: CutIntentDTO }>
}): Promise<MutationResponse> {
  return request<MutationResponse>('POST', '/api/baselines', payload)
}

export function postCutIntent(
  cutId: CutId,
  payload: {
    expected_authority_revision: number
    mutation_id: string
    intent: CutIntentDTO
  },
): Promise<MutationResponse> {
  return request<MutationResponse>('POST', `/api/cuts/${cutId}/intent`, payload)
}

export function putComposition(payload: {
  expected_authority_revision: number
  expected_composition_revision: number
  mutation_id: string
  state: CompositionStateDTO
}): Promise<MutationResponse> {
  return request<MutationResponse>('PUT', '/api/composition', payload)
}

// --- Generation ---

interface GenerationResponse {
  jobs: JobDTO[]
  snapshot: StudioSnapshotDTO
}

export function postGenerationJobs(payload: {
  expected_authority_revision: number
  cut_id: CutId | null
}): Promise<GenerationResponse> {
  return request<GenerationResponse>('POST', '/api/generation/jobs', payload)
}

interface StopResponse {
  receipt: unknown
  snapshot: StudioSnapshotDTO
}

export function postJobStop(jobId: string): Promise<StopResponse> {
  return request<StopResponse>('POST', `/api/generation/jobs/${jobId}/stop`)
}

export function postGlobalStop(): Promise<StopResponse> {
  return request<StopResponse>('POST', '/api/generation/stop')
}

// --- Review / Approve ---

interface MaterializeResponse {
  artifact: ReviewArtifactDTO
  snapshot: StudioSnapshotDTO
}

export function postMaterializeReview(payload: {
  expected_authority_revision: number
  expected_composition_revision: number
}): Promise<MaterializeResponse> {
  return request<MaterializeResponse>('POST', '/api/review-artifacts', payload)
}

interface AuthorizeResponse {
  authorization_id: string
  submitted_artifact_id: string
  submitted_content_hash: string
  snapshot: StudioSnapshotDTO
}

export function postAuthorize(
  artifactId: string,
  payload: {
    expected_authority_revision: number
    content_hash: string
  },
): Promise<AuthorizeResponse> {
  return request<AuthorizeResponse>(
    'POST',
    `/api/review-artifacts/${artifactId}/authorize`,
    payload,
  )
}

export function postExportPng(
  payload: ExportPngRequest,
): Promise<ExportPngResponse> {
  return request<ExportPngResponse>(
    'POST',
    '/api/release/export-png',
    payload,
  )
}

export function postBloggerRelease(
  payload: BloggerReleaseRequest,
): Promise<BloggerReleaseResponse> {
  return request<BloggerReleaseResponse>(
    'POST',
    '/api/release/blogger',
    payload,
  )
}
