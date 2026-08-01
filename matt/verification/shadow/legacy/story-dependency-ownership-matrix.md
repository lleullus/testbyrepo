# Story Dependency / Ownership Matrix

Revision: shadow-v1

## Machine-Bearing Relationship Cells

There are no shared obligations for this single Story change.

| Obligation ID | Product authority | Contract IDs | Accountable producer Story ref | Delivery contributors | Direct consumer Story refs | Downstream consumer Story refs | Prerequisites (tagged refs) | First required horizon | Evidence due now | Later verification owner | Capability / hard-factor prerequisites | Owning Story / AC / Task | Materialization | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Story materialization index

| Exact Story ID | Story key | Ownership row refs | Contract IDs | Detailed Story path | Materialization status | Source revision |
| --- | --- | --- | --- | --- | --- | --- |
| `STORY-001` | `missing-config-exit-code` | `[]` | `[]` | `legacy/stories/STORY-001.md` | `materialized` | `shadow-v1` |

## Dependency order

| Exact Story ID | Prerequisites (tagged refs) | Reason | Admission-sensitive capability | First safe start condition |
| --- | --- | --- | --- | --- |
| `STORY-001` | `{"stories":[],"obligations":[]}` | No dependency. | `[]` | The existing Go baseline is available. |

## Ownership checks

- No shared obligation requires an accountable producer.
- The materialization index resolves `STORY-001` exactly once.
- No Story or boundary-obligation prerequisite exists.
