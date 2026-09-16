/** EventSource lifecycle and decoding — Plan §3.4 */

import { type StudioSnapshotDTO, isStudioSnapshotDTO } from './contracts'

export interface StudioSnapshotEvent {
  type: 'studio.snapshot'
  boot_id: string
  authority_revision: number
  snapshot: StudioSnapshotDTO
}

export interface SnapshotRequiredEvent {
  type: 'snapshot-required'
  reason: 'boot-changed' | 'replay-miss' | 'revision-gap'
  authority_revision: number
}

export type StudioEvent = StudioSnapshotEvent | SnapshotRequiredEvent

export type StudioStreamTransportState = 'connecting' | 'open' | 'reconnecting'

export interface StudioEventSourceOptions {
  onEvent: (event: StudioEvent) => void
  onStateChange: (state: StudioStreamTransportState) => void
}

export function createStudioEventSource(opts: StudioEventSourceOptions): {
  close: () => void
} {
  let es: EventSource | null = null
  let closed = false

  function connect() {
    if (closed) return
    opts.onStateChange('connecting')
    es = new EventSource('/api/events')

    es.onopen = () => {
      if (!closed) opts.onStateChange('open')
    }

    es.onerror = () => {
      if (!closed) opts.onStateChange('reconnecting')
    }

    es.addEventListener('studio.snapshot', (e: MessageEvent) => {
      if (closed) return
      try {
        const data = JSON.parse(e.data) as {
          schema: string
          boot_id: string
          authority_revision: number
          snapshot: unknown
        }
        if (
          !data ||
          typeof data !== 'object' ||
          data.schema !== 'studio-event/v1' ||
          typeof data.boot_id !== 'string' ||
          data.boot_id.length === 0 ||
          !Number.isSafeInteger(data.authority_revision) ||
          data.authority_revision < 0 ||
          !data.snapshot ||
          typeof data.snapshot !== 'object' ||
          !isStudioSnapshotDTO(data.snapshot) ||
          data.snapshot.authority_revision !== data.authority_revision
        ) {
          return
        }
        opts.onEvent({
          type: 'studio.snapshot',
          boot_id: data.boot_id,
          authority_revision: data.authority_revision,
          snapshot: data.snapshot,
        })
      } catch {
        // malformed event — ignore
      }
    })

    es.addEventListener('snapshot-required', (e: MessageEvent) => {
      if (closed) return
      try {
        const data = JSON.parse(e.data) as {
          schema: string
          reason: 'boot-changed' | 'replay-miss' | 'revision-gap'
          authority_revision: number
        }
        if (
          !data ||
          typeof data !== 'object' ||
          data.schema !== 'studio-event/v1' ||
          (data.reason !== 'boot-changed' && data.reason !== 'replay-miss' && data.reason !== 'revision-gap') ||
          !Number.isSafeInteger(data.authority_revision) ||
          data.authority_revision < 0
        ) {
          return
        }
        opts.onEvent({
          type: 'snapshot-required',
          reason: data.reason,
          authority_revision: data.authority_revision,
        })
      } catch {
        // malformed event — ignore
      }
    })
  }

  connect()

  return {
    close() {
      closed = true
      es?.close()
      es = null
    },
  }
}
