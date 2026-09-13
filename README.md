# IIS Planning Skills

IIS is the planning layer that turns user intent into approved product authority and a validated Ready Ticket Set for one current construction Increment. Baseline IIS remains the default and ends at Ready Tickets. Spec and Ticket projection use leaf-local defect-first self-review by default; separate per-artifact user/planning-owner approval is an explicit option. IIS itself does not implement Tickets, independently verify them, orchestrate delivery agents, or declare product completion.

## Components

- `product-thesis/`: conditional product-meaning design with a saved full source before downstream planning. New `iis-product-meaning/v2` bindings reference exact source bytes; existing v1 authority remains supported without bulk migration.
- `scope-shaper/`: connected outcome-landscape investigation plus selection of exactly one durable next product construction Increment from the actual current product state.
- `scope-investigation-runner/`: optional read-only evidence investigation used only when the user explicitly authorizes Runner use and supplies the exact roster/concurrency binding.
- `behavior-design-lead/`: canonical Behavior authority design performed inside planning.
- `matt/`: one-Increment product/Behavior/UI planning, optional explicit adversarial consensus, approved Spec creation, and reviewed Ready Ticket decomposition.
- `planning-workspace/`: project-local planning workspace support.
- `observatory/`: read-only IIS state scanner and CLI for cross-repository overview, repository health, next-work pointers, consistency checks, and planning history.
- `iis-observatory/`: Codex skill wrapper for Observatory. The globally installed copy lives at `~/.codex/skills/iis-observatory/` and routes status inspection to the read-only CLI.
- `iis-workflow/`: canonical planning-only entry router. A generic IIS request goes to Ask Matt only when it is already next-increment-ready; otherwise Scope Shaper first selects the Increment.
- `iis-adaptive-planning/`: explicit opt-in planning mode. Outer Main routes enabled execution preparation, implementation, semantic verification and post-success Coverage without becoming a second product authority.
- `repo-snapshot/`: independent Git working-tree snapshot skill.
- `companion-skills/`: repository investigation, purpose-first review, execution-plan preparation, Ready Ticket implementation, verification and read-only post-success Coverage outside IIS Planning authority.

## Coherent bundle installation

IIS planning/companion skills, their helpers and the Ready runtime install from one immutable source snapshot. Live skills no longer point into a changing source worktree. Prepare and check are not evidence of loaded code or permission to interrupt an active host.

```bash
python3 scripts/sync_installed_iis.py prepare --source /absolute/candidate --store /absolute/iis-store
python3 scripts/sync_installed_iis.py check --store /absolute/iis-store --bundle <reported-sha256>
python3 scripts/sync_installed_iis.py activate --store /absolute/iis-store --bundle <reported-sha256> --host omp --confirm-quiescent
```

The default store is `${XDG_DATA_HOME:-~/.local/share}/iis`; `current` selects one complete release. `--host codex` selects the separate Codex install, not OMP. Existing unmanaged files/symlinks require explicit `--migrate`, which preserves exact previous entries in a recovery snapshot. Never declare hosts quiescent from a cancellation receipt: settle workers/services and unresolved effects first. Start a **fresh top-level host** and check actual loaded identity and behavior after activation. The installer reports `loaded_identity: NOT_CHECKED`.

`rollback --confirm-quiescent` restores the preceding install snapshot only after candidate work/effects are contained. `remove --confirm-quiescent` restores original entries and preserves releases/runtime data; neither rolls back product or external effects. Intervening user changes stop recovery rather than being overwritten. Model configuration, credentials, the replaceable model guide, product Tickets and runtime state are not bundled. Observatory's independent installer remains `python3 scripts/sync_installed_observatory.py`.

Thesis source storage is authorized before Run Contract/model/approval closure; it does not approve product meaning or release Scope/Matt/delivery gates. Sources normally live at `docs/planning/product-thesis/<meaning-slug>/THESIS-NNN.md`; preserve referenced revisions rather than overwriting them. Scope/Spec consumers validate and read the exact source through the existing immutable Scope lineage (or directly for direct Matt). Run Contract refers to unchanged source outcomes/items/success sections and adds only this invocation's scope/stage restrictions inside the Mandate ceiling. Optional Transition Baseline remains a transition map, not a replacement Thesis.

For `iis-product-meaning/v2`, `product-thesis/tools/product_meaning_binding.py fingerprint <artifact>` computes SHA-256 of the source bytes; `validate` checks source availability/hash and `validate-spec` also checks the exact existing Scope lineage. Preserve or relocate source bytes and update references explicitly when moving projects; an absolute reference is not portable by itself. Neither hashing nor Run Contract `STRUCTURE_VALID` proves semantic fidelity. The planning owner must read source sections, resolve referenced required/candidate sets and apply the original causal meaning to the current outcome.

## Adaptive execution boundary

`IIS Adaptive Planning` remains an explicit opt-in skill. Outer Main carries the invocation-local Run Contract and routes exact owner results. Product planning still stops at the reviewed Ready Ticket Set. Enabled implementation first consumes a current independent execution-plan review, then performs implementation and actual self-check. Enabled verification directly binds the current implemented target and owns every authored Flow/AC, discriminating scenarios, fresh evidence and cleanup. After VERIFIED from ready, the finalization-owning caller obtains one independent read-only Coverage review of actual implementation paths against that exact evidence. Only COMPLETE with no unresolved material gaps permits the original opaque handle's submission to ready_finalize. An already implemented `ready` Ticket can be verified without requiring a new implementation plan. Stage-specific execution mode and confirmed model choices are preserved; DIRECT uses current Main and never promotes self-check evidence into an unexamined final verdict. Material method changes return to preparation; verification has no pause/release checkpoints and supplementary adjudication uses a fresh verifier invocation. Default current-Increment delivery and broader named/outcome completion obligations are unchanged.

The delivery skills keep their own authority and only caller-owned `ready_finalize` performs guarded `ready -> done`; the verifier owns the immutable semantic verdict. Adaptive carries the relevant invocation-local model selection and bounded evidence-economy instruction through the current delivery owner contract; it adds no Graph database, scheduler, retry ledger, evidence budget, or extra Spec/Ticket review status.

### Adaptive model recommendations

The replaceable recommendation source is [model-selection-guide.md](model-selection-guide.md) at the repository root (`~/project/iis-skills/model-selection-guide.md`), initially the user-supplied v4.3 guide. Expand `~` against the current user's home directory. The repository Skill and its installed copy read this file directly from the repository root; it is not bundled in the Skill payload. To update recommendation data, edit or replace only that file; no Skill synchronization is needed for guide-only changes. Skill prompts and templates do not maintain copies of its model rankings. [Run Contract model selection](iis-adaptive-planning/references/09-run-contract.md#delivery-model-selection) preserves supplied model/effort choices, recommends a workload-appropriate configuration for missing enabled SUBAGENT stages using current available configurations, and asks the user to confirm those choices together. A recommendation is not consent. DIRECT/disabled stages need no child-model question; confirmed choices carry across the invocation without per-Ticket reconfirmation or automatic model/effort substitution.

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

Ready Tickets retain their product-contract meaning. `ready-ticket-plan` owns a separate method plan and a current per-Ticket `ADMIT | REVISE | EVIDENCE_NEEDED` review result, not a new Ticket status. A preparation-only request closes at `READY_EXECUTION_PLANS` only when every required Ticket has current ADMIT. Direct/assigned/resumed/replacement implementation consumes that review at the common admission boundary. Reading a Skill or inspecting authority alone does not arm an execution. `Verification: yes` includes semantic verification and post-success read-only Coverage, not another delivery switch. Coverage has no AC/status authority, and the unchanged finalizer does not mechanically enforce the caller protocol. FAILED/INCONCLUSIVE keep non-progressing finalization without Coverage. Only ready_finalize may complete guarded `ready -> done`; a done string without successful progression and the current obligation denominator is not a delivery result.

When the user explicitly asks IIS only for the current state or next planning item, the router performs a read-only Current Planning State Check over the existing Scope/Work Package/Increment/Spec/Ticket artifacts. `done` Tickets are treated as completed, non-`done` Tickets in the current Increment are reported as remaining work, superseded historical Increments do not block the current pointer, and the already-authored Scope is used to report the next Work Package/Increment and which leaf would be used next. The check stops after reporting; it never executes Scope Shaper, Ask Matt, To Spec, or To Tickets on the user's behalf.

IIS does not use a controller database, persistent Goal state, implementation roster, verification roster, attempt ledger, evidence cache, event/replay engine, or generic workflow DSL.
