# Independent Verification Feature Removal Draft

Status: `SOURCE_CUTOVER_IMPLEMENTED_DATA_INERT`
Date: 2026-08-11

Implementation note: the tracked source, ignored runtime, and installed public
router cutover was performed without commit or push. The existing
`~/.iis/route-navigation/` and `~/.iis/verification/` trees were not deleted;
their readers and writers are removed and their pre/post digests are unchanged.

## Decision

Remove the IIS independent-verification feature as one bounded cutover. This is
not a redesign that transfers Verification Lead duties to Implementation Lead,
Primary Verifier, another agent, or a renamed runtime. After cutover, IIS ends at
the Implementation Lead result and does not provide an independent Ticket
verification action, AC verdict, whole-Ticket `VERIFIED` result, coverage
challenge, verification-plan approval, verification remediation, or verification
result publication.

Keep Ticket `## Verification` content as an observable product-flow description
used by planning and implementation. Keep Implementation Lead's source review,
focused checks, gross actual-product handoff-liveness checks, and honest report
of unresolved runtime uncertainty. Those checks remain implementation-stage
closure and never become independent verification or a final AC verdict.

## User-Visible Result

The supported lifecycle becomes:

```text
Scope Shaper -> Matt -> Spec -> Tickets -> Implementation Lead -> implementation result
```

An explicit request for independent Ticket verification has no IIS route after
cutover. The IIS router must state that the workflow does not provide that
action; it must not silently route the request to Implementation Lead, a generic
agent, a direct Primary selection, or a compatibility command. The response is
an exact unsupported/no-route refusal, not an invitation to approximate the
removed result with implementation checks.

Implementation completion means only:

- the exact ready Ticket was implemented within its approved authority;
- the real project diff and applicable implementation checks were reviewed;
- no known correctable in-scope due-now implementation work remains; and
- performed gross actual-product checks and unresolved runtime uncertainty are
  reported without an independent verdict.

It does not mean every AC has independent direct evidence or that the Ticket is
`VERIFIED`.

## Removal Boundary

### Delete Tracked Verification Runtime

Delete these tracked files and directories:

- `verification-lead/SKILL.md`
- `verification-lead/coverage_gate.py`
- `primary-verifier/SKILL.md`
- `iis_ephemeral_transport.py`
- `tests/test_iis_ephemeral_transport.py`

`iis_ephemeral_transport.py` is deleted in full, not reduced to a generic store.
Its route-navigation, plan-envelope, user-approval, remediation, and final-outcome
APIs exist only for the removed verification workflow. No active Python caller
outside its tests imports it. Preserve `iis_path_contract.py`: it is an active
shared path helper independently consumed by planning-workspace and Scope Shaper,
not part of the verification transport.

### Remove Ignored Runtime Residue

Remove the untracked/ignored `verification-runtime/` tree, including its profile,
dependencies, bytecode, and any `iis-verify` residue. It is not part of current
HEAD and must not remain as an alternate verification entry after the tracked
feature is removed.

### Rewrite Active Contracts

Update `implementation-lead/SKILL.md` so that it:

- removes the requirement to begin or hand off to independent verification;
- removes `route-navigation`, provenance, Primary, Verification Lead, terminal
  grace, cleanup, and verification-only handoff terminology;
- keeps all current implementation feasibility, authority, user-change
  preservation, same-Ticket correction, real-diff review, focused-check, and
  gross actual-product check duties;
- reports unresolved behavior that would require broader runtime evidence as an
  implementation-result limitation rather than deferring it to a removed owner;
- explicitly forbids claiming independent verification, an AC verdict, or final
  `VERIFIED` status; and
- creates no serialized handoff or replacement verification artifact.

Update `matt/skills/to-tickets/SKILL.md` so that it:

- preserves exact authored Acceptance Criteria and `## Verification` product
  flows as planning and implementation authority;
- removes Verification Lead, Primary Verifier, Runtime Runner, coverage gate,
  route sidecar, independent-verification blocker, and affected-AC
  re-verification ownership;
- keeps `Verification` solution-independent and product-boundary-oriented; and
- keeps every exact authored `## Verification` product flow as authority for
  implementation-stage planning and check selection without turning it into an
  independent-evidence or independent-verdict obligation; and
- does not imply that Implementation Lead supplies independent evidence or final
  verdicts. Replacing the old consumer clause must not merge, split, weaken, or
  discard any authored observable product flow.

Update `scope-shaper/SKILL.md`, `README.md`, and the public
`/home/user01/.codex/skills/iis-workflow/SKILL.md` router to remove independent
verification from the advertised lifecycle and route table. The router must have
no path to deleted files or ignored runtime residue. Treat that exact installed
router as an active cutover surface: its verification leaf, absolute
`verification-runtime/iis-verify` path, command examples, and fallback wording
must all be absent rather than relying on repository-local routing alone.

### Rewrite Active Tests And Census

Update `implementation-lead/tests/contract/test_skill_contract.py` to remove:

- imports and reads of Verification Lead, Primary Verifier, and coverage gate;
- coverage-gate behavior tests;
- route-navigation and verification handoff assertions; and
- assertions that require removed paths or roles.

Replace them only with bounded assertions that Implementation Lead retains its
own implementation-stage review/check duties. The rewritten contract tests must
separately reject each of these claims: independent verification, direct or
independent AC evidence/verdict, and final `VERIFIED` status. They must also
require unresolved runtime or causal uncertainty to be reported as the exact
observed implementation-stage fact or limitation, not converted into a generic
`not verified` pseudo-verdict.

Update `tests/test_behavior_workflow_contract.py` so Behavior/UI authority is
required through Spec, Ticket, and Implementation Lead only. Do not add a
replacement verification consumer. Add producer-contract assertions that every
authored top-level `## Verification` item preserves its count, order, product
trigger, expected effect, readback, and grouping. The Implementation Lead may use
those flows only to select and report implementation-stage product-boundary
closure; neither producer nor consumer may convert them into an internal test
seam or independent verdict.

Update `tests/test_iis_entry_routing_contract.py` with a negative installed-router
contract. In addition to preserving the current Ask Matt and Scope Shaper routing
assertions, it must read `/home/user01/.codex/skills/iis-workflow/SKILL.md` and
reject the removed verification leaf, `verification-runtime/iis-verify`, the
`iis-verify` command, and any fallback that sends an independent-verification
request to Implementation Lead or a generic agent. It must positively require
the exact unsupported/no-route response for that request, so deleting the route
without defining its refusal is not enough. The current test covers only Ask Matt
and Scope Shaper, so an otherwise green full suite does not establish this
removal boundary.

Update `phase8_removal_census.py` and
`tests/test_phase8_removal_census.py` as an actual removal gate, not only by
changing the installed-skill list:

- removed `verification-lead` and `primary-verifier` installations are forbidden.
  A separately installed `implementation-lead` is optional, because the
  canonical installed `iis-workflow/SKILL.md` router directly names the
  repository leaf; if a separate installation exists, its target and content
  must match the repository, while its absence is not an error;
- make the repository root, state root, installed Codex skill root
  (`/home/user01/.codex/skills`), and active OpenCode configuration root
  (`/home/user01/.config/opencode`) explicit required census inputs rather than
  silently omitting an unprovided external surface;
- the bounded tracked and filesystem inventory additionally rejects current
  `verification-lead/`, `primary-verifier/`, `iis_ephemeral_transport.py`,
  `tests/test_iis_ephemeral_transport.py`, and `verification-runtime/`, including
  ignored files, bytecode, empty directories, and symlink residue;
- the bounded bytecode inventory rejects compiled transport, coverage-gate,
  root-inventory, test-runner, and verification-runtime modules under the named
  verification feature directories, including the currently observed
  `verification-lead/__pycache__/` and `verification-runtime/__pycache__/`
  residue, without treating unrelated project caches as this feature;
- the process census rejects exact invocations of `iis-verify` and the removed
  verification runtime scripts or their bytecode without broadly matching
  unrelated Python or OpenCode processes;
- active router/config/skill surfaces are checked for a callable verification
  entry rather than relying only on repository path absence. The installed
  public router is checked at the exact relative path `iis-workflow/SKILL.md`;
- the gate fails, rather than reporting zero residue, when any required root or
  installed router is omitted, missing, unreadable, or not fully classified;
  unavailable process observation is likewise an error, and any exact matching
  entry outside the allowed active/historical classification is an error; and
- tests prove each tracked, untracked, ignored, symlink, installed, config, and
  exact-process residue class makes the gate fail closed, including omitted,
  missing, and unreadable observation roots. Include a foreign/stale installed
  router fixture, and independently prove that its removed leaf, runtime path,
  and command each fail the gate.

Update every normal and error invocation in the
`tests/test_phase8_removal_census.py` census helper to supply all four roots, not
only selected new fixtures. Add separate omission, missing, unreadable,
foreign/stale-router, removed-runtime-path, and removed-command cases so an
expected input failure cannot mask an unobserved surface. Run both
`python3 run_tests.py` and `python3 implementation-lead/run_tests.py`; the former
discovers the root census/router contracts and the latter discovers the rewritten
Implementation Lead contracts.

Preserve all existing census coverage for retired historical verification-run
and implementation mechanisms; removing the current verification feature must
not make old executable residue acceptable. Prefer extending this one bounded
census over adding a second overlapping removal tool. Use explicit bounded path,
active-file, and executable allowlists: historical documents and unrelated
Python/OpenCode processes, dependencies, and caches are not matching residue.

### External Registration And Installation

Current `/home/user01/.config/opencode/opencode.json` contains no
`verification-lead` or `primary-verifier-*` registration, so no config edit is
currently required. The cutover census must still fail if any matching agent,
command, plugin, tool, skill link, or executable entry exists elsewhere under
the active OpenCode/Codex configuration surfaces. The installed
`iis-workflow/SKILL.md` router is mandatory and must retain its canonical direct
route to the repository `implementation-lead/SKILL.md`; a separate
`implementation-lead` skill installation is not mandatory.

Because `/home/user01/.codex/skills/iis-workflow/SKILL.md` is outside the
repository change set, record its pre-change and post-change path, type, link
target if applicable, mode, size, and SHA-256 separately from Git evidence.
Create a bounded temporary backup before editing it, verify the post-change
digest against the exact router contract, and include this file in pre-commit
rollback verification.

If `/home/user01/.codex/skills/verification-lead` or
`/home/user01/.codex/skills/primary-verifier` exists at cutover time, remove the
installation only after verifying that it resolves to this removed repository
feature. Record the entry's path, type, link target where applicable, mode, and
content digest before removal so the entry itself can be restored during a
pre-commit rollback; never delete the external target of a link. Never delete an
unrelated target based only on its basename.

## Data Disposition

The following data belongs exclusively to the removed mechanism and is not
planning authority, independent evidence that remains supported, or a result
that any remaining IIS reader can consume:

- `/home/user01/.iis/route-navigation/` currently contains two JSON sidecars.
- `/home/user01/.iis/verification/` currently contains one Ticket directory with
  `plan-envelope.json`, `user-approval.json`, and `final-outcome.json`.

The preferred complete-removal disposition is to delete both bounded trees after
recording a read-only pre-removal manifest of path, type, mode, size, and digest
for execution evidence. The manifest must also record whether a separately
approved backup exists and is restorable. If no such backup exists, the approval
must state that deletion is irreversible and source rollback cannot restore
those bytes. Do not archive their contents into the repository, build a
compatibility reader, migrate schemas, or preserve a dual-read period.

Data deletion is a separate destructive step from source cutover. It requires
the user's explicit confirmation at implementation time. If confirmation is not
available, remove every active reader/writer/entrypoint and leave the data inert,
reporting that complete data removal remains pending. Do not call that state full
filesystem removal.

## Historical Documents

Phase, Oracle, consensus, simplification, conversion, and removal documents are
historical design records. They are not active runtime entrypoints and are not
rewritten merely to erase terminology. Active-residue census must use explicit
path classification so historical prose cannot keep a removed mechanism active
and cannot create false zero-residue failures.

`TIER-B-ADVERSARIAL-CONSENSUS.md` may remain as the record that once authorized
the route sidecar. Its statements describing a then-current contract are
historical after this cutover, not compatibility authority.

## Cutover Order

Perform the implementation in one working-tree change set:

1. Capture the current tracked/untracked/config/installed/data/process census.
   Before deleting ignored `verification-runtime/`, create a bounded temporary
   backup plus a path/type/mode/size/digest manifest sufficient to restore the
   exact pre-cutover tree. Capture equivalent restoration metadata for any
   verified matching installed entry before removing the entry itself. Capture
   and back up the external public router before editing it.
2. Rewrite active producer, Implementation Lead, router, README, behavior/UI
   contract tests, and removal census to the no-verification lifecycle.
3. Delete the tracked verification roles, gate, transport, and transport tests.
4. Remove ignored `verification-runtime/` residue and verified matching installed
   entrypoints.
5. Run targeted contract tests, the full repository suite, active-entrypoint
   census, ignored/untracked/filesystem/process residue census, and diff
   validation. A green census must establish absence of both the earlier legacy
   mechanisms and the current verification feature; changing only
   `INSTALLED_SKILL_NAMES` is insufficient.
6. After separate explicit user confirmation, delete the bounded `~/.iis`
   route-navigation and verification data and verify both trees and their empty
   parent feature directories are absent. Report source-cutover completion and
   filesystem-data removal as separate statuses.

Do not release an intermediate state in which the router or Implementation Lead
still names verification while the target runtime is absent, or in which the
runtime remains callable after contracts say it is removed.

## Verification Criteria

The cutover is complete only when all of the following are true:

- tracked paths `verification-lead/`, `primary-verifier/`,
  `iis_ephemeral_transport.py`, and `tests/test_iis_ephemeral_transport.py` are
  absent;
- ignored/untracked `verification-runtime/` and retired verification bytecode are
  absent;
- active skill/router/config/test execution has no import, route, entrypoint,
  consumer, or callable configuration for Verification Lead, Primary Verifier,
  `iis-verify`, route-navigation, coverage-gate, verification transport, or
  independent verification. Historical-only census classification literals and
  negative fixtures may retain those names but cannot be callable or treated as
  active authority;
- `tests/test_iis_entry_routing_contract.py` proves the installed public router
  contains neither the removed verification leaf/runtime command nor a fallback
  transfer of its duties;
- no active OpenCode agent, command, plugin, custom tool, or Codex skill exposes
  the removed feature;
- Ticket producers still emit exact authored Acceptance Criteria and observable
  `## Verification` flows with their count, order, product trigger, expected
  effect, readback, and grouping unchanged;
- Implementation Lead still performs and reports its implementation-stage
  source review, focused checks, gross actual-product checks, and unresolved
  limitations, but cannot report independent verification or final `VERIFIED`;
- no replacement artifact, renamed verifier, implicit generic-agent fallback, or
  Implementation Lead self-certification path was introduced;
- `python3 run_tests.py` and `python3 implementation-lead/run_tests.py` pass after
  intentional test removal/rewrite;
- `git diff --check` passes and the actual diff contains only the approved
  removal/correction surface; and
- after separately authorized data deletion, both bounded `~/.iis` trees and
  empty parent feature directories are absent.

## Rollback

Before commit, rollback is the working-tree restoration of the exact pre-cutover
HEAD plus restoration of ignored `verification-runtime/` and any removed
installed entry from the mandatory bounded pre-cutover backup/manifest,
restoration of the external public router from its mandatory backup, and
restoration of separately deleted `~/.iis` data from an explicitly approved
temporary backup if one was created. Verify restored path identities against
their manifests before calling pre-commit rollback complete.

After commit, a normal revert restores only the tracked part of the cutover. It
does not recreate ignored runtime, external installed entries, the external
public-router revision, or deleted `~/.iis` bytes; restoration of those surfaces
requires their retained approved backup. If that backup is not retained, their
deletion or replacement is one-way. A rollback must not selectively restore only
a router, role leaf, or transport function.

Do not create a compatibility layer for rollback. A future decision to restore
independent verification requires restoring a complete coherent runtime and
freshly producing any needed state rather than trusting orphaned artifacts.

## Explicit Non-Goals

- Moving independent-verification duties into Implementation Lead.
- Promoting Primary Verifier to a direct entrypoint.
- Keeping coverage gate or transport as a generic utility without an active
  consumer.
- Replacing IIS verification with a generic agent, Oracle, test command, or
  manual checklist.
- Weakening Ticket Acceptance Criteria, Behavior authority, UI authority, or
  implementation authorization.
- Rewriting historical documents solely to remove old names.
- Deleting `~/.iis` data without explicit user confirmation.
- Committing or pushing without an explicit request.
