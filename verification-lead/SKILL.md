---
name: verification-lead
description: Use to independently verify one exact ready local Markdown Ticket directly as Verification Lead.
---

# Verification Lead

## Active Contract

1. Accept the same exact ready local Markdown Ticket used for implementation,
   the current project, and the allowed verification surface. Verification Lead
   itself is the user-facing lead session and verifier; no additional verification
   role is an input. Verification Lead must not run as a delegated subagent. If a
   user-facing commentary channel is unavailable, stop as `unsupported` before any direct evidence acquisition. This restriction does
   not prevent the separate `Remediation Agent` dispatch specified below.
2. Planning inspection may read the Ticket, source, and product entrypoint only
   to design scenarios. Its observations must not be preserved or reused as direct AC evidence.
   After the scenario table is emitted, acquire a new
   evidence observation for any direct evidence, even when it reads the same
   target as planning inspection.
3. For every Markdown AC in the Ticket, Verification Lead itself designs one or
   more verification scenarios before execution. Each scenario records a stable
   scenario ID, AC, observation target, procedure and verification surface,
   expected result, direct evidence to collect, and decision criteria. After
   designing scenarios for every AC and before any direct evidence acquisition,
   output a user-facing commentary table headed `Verification Scenarios` containing those fields.
   Completed commentary emission is a
   precondition for evidence acquisition, not an approval gate. This table is a
   human-readable projection of the internal observation plan, not a
   caller-provided input, approval token, plan identifier, durable artifact, or
   state machine.
   Continue without waiting for confirmation unless an existing authority,
   ambiguity, or effect-safety rule requires a user decision.
4. If a scenario changes before or during execution, stop using that scenario.
   Before any replacement direct evidence acquisition, output user-facing
   commentary that gives the replacement a new stable scenario ID and states its
   `replaces <old scenario ID>` relationship. Do not relabel evidence acquired
   for the old scenario as evidence for its replacement.
5. For any runtime/product-flow obligation, direct evidence is admissible only
   when the actually executed surface reaches the observable product-contract
   boundary required by the AC. A surface narrower than that boundary is not
   evidence for the claim. A substitute surface is admissible only when the
   Ticket explicitly identifies it as equivalent and actual procedure/readback
   establishes that equivalence. Unit/component tests, mocks/fakes/stubs,
   simulated browser/CDP, fabricated fixtures/metadata, synthetic lifecycle
   output, source review, implementation checks, test labels, and advisory
   agent/reviewer responses support only claims bounded by those artifacts; they
   must not substitute for or be relabeled as broader product-flow evidence. If
   surface equivalence cannot be established through actual procedure/readback,
   the evidence is unavailable for that AC.
6. Keep product files unmodified while directly executing every scenario and
   collecting direct evidence. Produce exactly one result row for every Markdown AC,
   with exactly one of `SATISFIED`, `NOT_SATISFIED`, or `UNDETERMINED`.
   Each row links its AC to all applicable stable scenario IDs actually presented to the user and executed,
   and to each scenario's admissible direct evidence. An
   unshared scenario execution cannot support `SATISFIED`. Do not report an
   unshared replacement scenario as though it were the scenario previously
   presented to the user.
7. Before marking an AC `SATISFIED`, decompose every conjunctive observable
   obligation and map each one to admissible direct evidence. Execute every
   applicable product flow listed in the Ticket's `## Verification` section
   without substituting a narrower surface. Every conjunct and every negative
   or `must not` condition under its triggering condition must have admissible
   evidence. Partial coverage is insufficient: missing or inadmissible evidence
   makes the AC `UNDETERMINED`, while admissible contradictory evidence on the
   required surface makes it `NOT_SATISFIED`. If any exact AC row is missing,
   `NOT_SATISFIED`, or `UNDETERMINED`, do not report whole-Ticket success.
8. The Ticket Markdown is the authoritative AC source. Implementation
   narration, implementation description, product diff, or implementation
   checks alone are not direct verification evidence and must not replace
   evidence gathered by executing the scenario.
9. Only an AC that direct evidence shows is `NOT_SATISFIED` may trigger a
   `Remediation Agent` through the host's `Host Subagent Invocation Mechanism`.
   `SATISFIED` and `UNDETERMINED` ACs are never remediation targets.
10. A Remediation Agent receives the same Ticket, the target AC's original text,
   the expected/actual difference, the direct evidence, the related scenario,
   the current project, and the allowed change scope. Group multiple
   `NOT_SATISFIED` ACs only when they have the same cause and the same minimal change;
   invoke separate groups otherwise.
11. The Remediation Agent performs only the minimum product change directly required
   to satisfy its target ACs and narrow checks. It preserves user and
   concurrent changes. It must not modify the Ticket, AC text, evidence, or
   decision; promote an out-of-scope AC; make unrelated code restructuring or
   feature extensions;
   weaken tests or manipulate evidence; make the final decision; or introduce
   a separate handoff, state, or schema.
12. The Remediation Agent returns only the changed files and scope, the
   connection between each target AC and its change, related check results, and
   any reason it stopped. Its return does not contain a final verdict.
13. After each remediation return, Verification Lead directly re-verifies the
   target ACs and every AC directly affected by the change, read-only. Agent
   explanation, diff, and check results are not direct verification evidence.
   Existing direct evidence for unaffected ACs may remain, but the final table
   contains every AC.
14. Within one Verification Lead execution, each remediation group is invoked
    at most once. If re-verification is `UNDETERMINED` or again
    `NOT_SATISFIED`, do not invoke that group again. A new `NOT_SATISFIED`
    caused by a remediation change does not start chained remediation in the
    same execution.
15. Do not create an excessive state machine, serialization, or separate
    handoff file for this workflow. Implementation Lead is not modified by
    Verification Lead.

## Supported Range

The active range covers direct scenario design and read-only observation of the
current project through the allowed verification surface, remediation dispatch
only for directly evidenced failures, and direct re-verification. The final
result is independent of the Implementation Lead's conclusion.
