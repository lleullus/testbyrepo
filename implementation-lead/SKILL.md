---
name: implementation-lead
description: Use for one exact ready local Markdown Ticket through the Implementation Verification Module with the fixed Terra Worker designation.
---

# Implementation Lead

## Active Contract

1. Accept one exact ready local Markdown Ticket.
2. Use the selected fixed `TerraWorker` designation only.
3. Create the production Module with its fixed OpenCode routing.
4. Call `Module.implement(Ticket, TerraWorker())`.
5. Treat the returned Candidate as pending independent verification.

Terra receives only a bounded Ticket and private-source projection. Its assignment is a strict
`{path, value}` value, applied only by the isolated private-workspace executor. The Module performs the
local implementation check; agent text cannot make that check pass.

## Supported Range

The active range supports zero-mutation Candidates, source and local verification observations, and
fail-closed mutation requests. Canonical source adoption is not supported and stops before any canonical
write. Authenticated reads and production effects are not supported.
