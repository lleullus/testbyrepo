# IIS Planning Skills

IIS is the planning layer that turns user intent into approved product authority and a validated Ready Ticket Set for one current construction Increment. Baseline IIS remains the default and ends at Ready Tickets. Spec and Ticket projection use leaf-local defect-first self-review by default; separate per-artifact user/planning-owner approval is an explicit option. IIS itself does not implement Tickets, independently verify them, orchestrate delivery agents, or declare product completion.

## Components

- `scope-shaper/`: connected outcome-landscape investigation plus selection of exactly one durable next product construction Increment from the actual current product state.
- `scope-investigation-runner/`: optional read-only evidence investigation used only when the user explicitly authorizes Runner use and supplies the exact roster/concurrency binding.
- `behavior-design-lead/`: canonical Behavior authority design performed inside planning.
- `matt/`: one-Increment product/Behavior/UI planning, optional explicit adversarial consensus, approved Spec creation, and reviewed Ready Ticket decomposition.
- `planning-workspace/`: project-local planning workspace support.
- `observatory/`: read-only IIS state scanner and CLI for cross-repository overview, repository health, next-work pointers, consistency checks, and planning history.
- `iis-observatory/`: Codex skill wrapper for Observatory. The globally installed copy lives at `~/.codex/skills/iis-observatory/` and routes status inspection to the read-only CLI.
- `iis-workflow/`: canonical planning-only entry router. A generic IIS request goes to Ask Matt only when it is already next-increment-ready; otherwise Scope Shaper first selects the Increment.
- `iis-adaptive-planning/`: explicit opt-in planning mode whose ownership still ends at Ready Tickets while the outer caller defaults the current Increment through separate implementation/verification and authority-based corrective re-entry unless the user selects a stop override.
- `repo-snapshot/`: independent Git working-tree snapshot skill.
- `companion-skills/`: version-controlled companion skills that remain outside IIS Planning authority. Ready Ticket implementation/verification and shared review discipline live here as canonical sources while their live Codex entries are linked from `~/.codex/skills/`.

## Global skill synchronization

The live Codex skill installs are synchronized from this repository:

```bash
python3 scripts/sync_installed_router.py
python3 scripts/sync_installed_adaptive.py
python3 scripts/sync_installed_observatory.py
```

Use `--check` on these commands to detect drift without changing the installed copy.

The three `companion-skills/` entries are not managed by these copy-sync scripts. Their canonical directories live in this repository and the corresponding `~/.codex/skills/<name>` entries are direct directory symlinks to those sources.

## Adaptive execution boundary

`IIS Adaptive Planning` remains explicit opt-in. Its planning authority still ends at the validated current Ready Ticket Set, but the outer caller continues that current Increment through the separately installed Ready Ticket implementation and verification skills by default unless the user explicitly selects planning-only/stop-at-Ready-Tickets/no implementation/no verification. Corrective re-entry after a material correction is the Adaptive default; success continuation beyond the current Increment remains separately controlled by the Mandate's Continuation Authority.

The delivery skills keep their own authority and the verifier alone owns guarded `ready -> done`. Adaptive passes only a bounded invocation-local evidence-economy instruction; it adds no Graph database, scheduler, retry ledger, evidence budget, or extra Spec/Ticket review status.

## Planning boundary

The canonical Scope-shaped flow is:

```text
Long-term intent + actual current product state
  -> Scope Shaper
  -> horizontal Work Package decomposition when needed
  -> exactly one ready-for-matt INC-NNN
  -> Ask Matt
  -> Behavior/UI authority
  -> optional explicit adversarial consensus
  -> self-reviewed approved Spec for that Increment
  -> To Tickets
  -> self-reviewed, validated Ready Ticket Set for that Increment
  -> Baseline IIS ends
```

A Work Package is a horizontal outcome boundary with `Status: scoped`; it is not an Ask Matt handoff. Future construction can be described provisionally, but only the current selected `INC-NNN.md` is `ready-for-matt`. Every confirmed shaping pass has an immutable `revisions/SHAPE-NNN.md` snapshot, and its Increment keeps that exact revision as historical planning authority even after the current `SCOPE-SHAPING-RESULT.md` advances. After delivery, a later Scope Shaping cycle inspects the actual resulting product state before selecting another Increment; prior ready Increments become `superseded` so only one Scope-shaped handoff remains admissible.

Construction candidates use a small auditable structure: outcome area, current/target state, actor, trigger or inspection target, observable result, authoritative readback, durable foundation, future policy avoided, disposition, and reason. Exactly one candidate is selected and must close structurally into the Selected Increment. The validator checks that closure only; it does not score product judgment or decide which candidate is substantively best.

A Scope-shaped Spec records `Source-Increment` and To Spec revalidates that Increment immediately before writing. Direct next-increment-ready Ask Matt work records `Source-Increment: None`. The trace does not import deferred or provisional future scope into the Spec.

A direct ordinary request may enter Ask Matt without Scope Shaper only when the current baseline and one durable observable current-to-next state transition are already clear and no construction-stage, foundation, product-capability-ordering, or split/merge decision remains. A genuinely unrooted greenfield request may be shaped from the brief before a repository exists, but durable artifacts and Ask Matt admission wait for one exact project root; IIS does not bootstrap product source as a planning side effect.

Legacy `ready-for-matt` Work Packages are not directly re-admitted. Scope Shaper treats them as preserved historical planning context, re-inspects the actual current product state, and performs semantic migration into the current one-Increment contract. This avoids restoring the old bypass while preserving prior approved evidence.

Ticket Verification flows use current positional `Parent outcome ordinal`, `AC ordinals`, and `Behavior authority ordinals` so observable delivery obligations remain traceable to their parent outcome and semantic authorities without persistent IDs or a trace database.

Ready Tickets are the interface to delivery. Baseline IIS stops at that boundary. Under explicit IIS Adaptive Planning, the outer caller hands each exact Ready Ticket to the separate implementation and verification skills under their own contracts by default unless the user selected a stop override; IIS still does not own delivery execution, scheduling, or verdicts. When the verification lifecycle actually satisfies a Ticket's authored completion obligations it may mark the existing Ticket `Status: done`; IIS itself never infers delivery completion.

When the user explicitly asks IIS only for the current state or next planning item, the router performs a read-only Current Planning State Check over the existing Scope/Work Package/Increment/Spec/Ticket artifacts. `done` Tickets are treated as completed, non-`done` Tickets in the current Increment are reported as remaining work, superseded historical Increments do not block the current pointer, and the already-authored Scope is used to report the next Work Package/Increment and which leaf would be used next. The check stops after reporting; it never executes Scope Shaper, Ask Matt, To Spec, or To Tickets on the user's behalf.

IIS does not use a controller database, persistent Goal state, implementation roster, verification roster, attempt ledger, evidence cache, event/replay engine, or generic workflow DSL.
