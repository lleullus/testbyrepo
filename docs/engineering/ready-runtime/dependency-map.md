# Ready Runtime Dependency Map

## External contract that remains fixed

`ready-ticket-implement` keeps its current caller-facing contract:

- inputs: exact Ticket path, Project Root, additional user instructions
- topology: SUBAGENT by default with exactly one implementation worker; DIRECT only when the current user explicitly selects it for that implementation stage
- checkpoints: SUBAGENT PRE_ACTION before first source mutation and MATERIAL_TURN only for material direction/authority/change-surface/evidence changes
- terminal result: existing `IMPLEMENT RESULT` fields and `Completion: COMPLETE | BLOCKED | PARTIAL`
- Ticket status: exact `ready` remains `ready` after implementation
- heuristic probing and final verification remain separate owners

## Repository dependencies

Primary implementation surface:

- `companion-skills/ready-ticket-implement/SKILL.md`
- `companion-skills/ready-ticket-implement/references/implement.md`
- `companion-skills/ready-ticket-implement/agents/openai.yaml`

Direct compatibility surfaces:

- `iis-adaptive-planning/SKILL.md`
- `iis-adaptive-planning/references/08-delivery-continuation.md`
- `iis-adaptive-planning/references/09-run-contract.md`
- `tests/test_delivery_subagent_contract.py`

Canonical planning locator and validator:

- current `iis-workflow/SKILL.md` To Tickets route
- adjacent `matt/skills/to-tickets/validate_ticket.py` at the resolved route target

Explicit non-owners:

- `companion-skills/ready-ticket-heuristic-probe/**`
- `companion-skills/ready-ticket-verify/**`
- Adaptive Run Contract schema
- Ticket validator/schema semantics

## OMP extension boundary confirmed from the installed source checkout

Reference checkout: `/home/user01/project/oh-my-pi-custom`.

Confirmed extension capabilities used by this runtime:

- `resources_discover`
- `tool_call`: fires before concurrency scheduling, tool execution start, and approval; can block or replace execution input
- `tool_result`: carries matching `toolCallId`, tool name, input, result content, details, and error flag
- `session_start`, `session_switch`, `session_branch`, `session_shutdown`
- `registerTool`
- `ExtensionContext.sessionManager.getSessionId()` for explicit session identity
- tool source provenance through `getAllTools()` / `ToolInfo.sourceInfo`

The runtime does not modify OMP itself. Unknown custom/MCP mutation surfaces are not guessed to be equivalent to native tools; their enforcement status is reported as an explicit boundary.
