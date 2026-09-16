/** Revision-derived selectors — pure functions, no store coupling. */

import type { CutDTO, StudioSnapshotDTO, CutId } from '@/api/contracts'

/** A cut is CURRENT only when desired == realized and both are non-null. */
export function isCutCurrent(cut: CutDTO): boolean {
  return (
    cut.currency === 'CURRENT' &&
    cut.desired_revision !== null &&
    cut.realized_revision !== null &&
    cut.desired_revision === cut.realized_revision
  )
}

/** All 5 cuts Current. */
export function isRealizationComplete(cuts: CutDTO[]): boolean {
  return cuts.length === 5 && cuts.every(isCutCurrent)
}

/** Active/stoppable job count from snapshot. */
export function countActiveJobs(snapshot: StudioSnapshotDTO): number {
  return snapshot.jobs.filter(
    (j) => j.status === 'queued' || j.status === 'running',
  ).length
}

/** Check if a job can be stopped. */
export function isJobStoppable(status: string): boolean {
  return status === 'queued' || status === 'running'
}

/** Get the realized asset URL for a cut, if available. */
export function cutRealizationUrl(cut: CutDTO): string | null {
  if (!cut.realized_asset_id || cut.realized_revision === null) return null
  return `/api/cuts/${cut.cut_id}/realization?asset_id=${encodeURIComponent(cut.realized_asset_id)}&revision=${cut.realized_revision}`
}
