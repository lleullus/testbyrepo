---
name: verification-lead
description: Use to independently verify one exact ready local Markdown Ticket with a user-designated Fresh Verification Subagent.
---

# Verification Lead

## Active Contract

1. Accept the same exact ready local Markdown Ticket and current project used
   for implementation, plus one user-designated `Fresh Verification Subagent`
   role. There is no implementation handoff object to reinterpret as evidence.
2. Invoke that designated role through the host's `Host Subagent Invocation Mechanism`.
   The Lead contract does not prescribe the host's invocation,
   communication, resumption, retry, or scheduling details.
3. Require the Fresh Verification Subagent to inspect product files and the
   permitted verification surface read-only. Provide only the same exact
   Ticket, current project, and permitted verification surface as its input;
   do not provide the Implementation Lead's or Implementation Subagent's
   narration or conclusions at all.
4. Produce exactly one result row for every Markdown AC in the Ticket. Each row
   contains one of `SATISFIED`, `NOT_SATISFIED`, or `UNDETERMINED`, together
   with the direct evidence supporting that row.
5. Do not treat implementation diff or implementation-check coverage alone as
   direct verification evidence. All ACs must have independent evidence before
   the verification outcome is considered complete.

The Ticket Markdown is the authoritative AC source. The Fresh Verification
Subagent does not modify product files.

## Supported Range

The active range covers read-only observation of the current project and direct
evidence for each Ticket AC. The verification result is independent of the
implementation Lead's conclusion.
