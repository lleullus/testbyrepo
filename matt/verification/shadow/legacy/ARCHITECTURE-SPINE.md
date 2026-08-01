# Architecture Spine

Revision: shadow-v1

## Scope

The only implementation change is the missing-config return value in `project/main.go` and its expectation in `project/main_test.go`.

## Contract Freeze Index

Contract Freeze Result: pass

- PRD: `legacy/PRD.md`, revision `shadow-v1`.
- Architecture Spine: `legacy/ARCHITECTURE-SPINE.md`, revision `shadow-v1`.
- State registry: `legacy/STATE-TRANSITION-MATRIX.md`, revision `shadow-v1`.
- Schema registry: `legacy/SCHEMA-MIGRATION-REGISTRY.md`, revision `shadow-v1`.
- Capability registry: `legacy/CAPABILITY-MATRIX.md`, revision `shadow-v1`.
- Epic authority: `legacy/epics.md`, revision `shadow-v1`.
- Ownership authority: `legacy/story-dependency-ownership-matrix.md`, revision `shadow-v1`.
- UX contract: not-applicable because the sole change is CLI exit behavior with no UI or interaction obligation.

## Implementation Constraint

The Go module root is `project`. No external capability, hard-factor, state-transition, or schema-migration claim is required.
