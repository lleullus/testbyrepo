---
name: adversarial-consensus
description: Optional Ask Matt planning gate used only when the user explicitly requests adversarial consensus for the current planning unit and explicitly designates the exact Adversarial Planning Challenger.
disable-model-invocation: true
---

# Adversarial Planning Consensus

## Purpose

Stress-test one Ask Matt candidate planning contract without changing the user's
intent, product authority, Scope authority, or final approval boundary. The gate
exists to let one explicitly user-designated `Adversarial Planning Challenger`
attack the strongest current candidate while Matt/Main actively defends the
confirmed user intent, counterattacks the Challenger's alternatives, and adopts
only a better-supported result.

This is an optional planning gate, not an ordinary default review. It never runs
merely because adversarial review could be useful.

## Activation

Activate this gate only when both conditions are explicit in the current
conversation for this exact planning unit:

1. the user explicitly instructs Ask Matt to run adversarial consensus; and
2. the user explicitly designates one exact Challenger counterpart for the
   `Adversarial Planning Challenger` role.

A Challenger designation without an explicit instruction to run the gate does
not activate it. An instruction to run the gate without one exact counterpart
does not authorize Matt to choose a model, Oracle, subagent, or fallback. At the
finalization boundary return:

```text
ADVERSARIAL CONSENSUS: CHALLENGER BINDING REQUIRED
```

Do not proactively suggest, default to, infer, or auto-enable this gate when the
user supplied neither condition. If an exact designated counterpart becomes
unavailable, do not substitute another counterpart without a new user
instruction.

## Authority Order

Use this authority order throughout the gate:

1. the complete current user conversation context, including the original words
   and any later explicit user changes; a later user change supersedes only the
   intent it actually changes and does not erase unaffected original context;
2. the current user-confirmed Intent Anchor as a derivative representation of
   that conversation, never as a replacement for it;
3. unavoidable verified external contracts and current directly observed facts;
4. the ordered Purpose-First material-problem and purpose-gate result, followed
   only then by purpose-preserving tradeoff analysis against the user's currently
   confirmed outcome and priorities;
5. Matt's current candidate planning contract; and
6. Challenger proposals or claims.

Matt's summary, candidate, recommendation, prior interpretation, or desire to
preserve prior work never outranks the user's current intent. If new evidence
shows that Matt's candidate is wrong, abandoning the candidate can be the correct
way to defend the user's intent. Only the user may change the product intent, and
when the user explicitly changes it the gate must update the affected intent
rather than defending the superseded meaning.

Observed implementation behavior is evidence about the current product, not
product policy by itself unless the confirmed contract adopts that behavior.
Convenience, simplicity, cost, speed, reversibility, and familiar patterns do not
outrank the confirmed purpose. After the purpose gate passes, consider their
material effects on the user's outcome, complexity, context interaction, drift,
auditability, and maintenance. Among sufficiently purpose-preserving options,
prefer the minimum-sufficient change rather than the most elaborate defense.

## Position In Ask Matt

Run ordinary Ask Matt investigation first: Existing Authority First,
Lead-First Investigation, Behavioral Design, Counterexample Stress Test, UI
judgment when applicable, the complete current user-decision frontier, and
verification-feasibility closure. The Challenger does not replace or reduce any
of those Matt-owned duties.

Run this gate after that current frontier is resolved and the complete
provisional candidate contract is available, but before new or changed Behavior
or UI authority receives final approval and before the integrated shared
understanding is finally approved for `to-spec`.

## Required Purpose-First Review Discipline

Before preparing the Challenger attack and before Matt/Main adjudicates any
challenge, read `../../../companion-skills/purpose-first-review/SKILL.md` in full
and apply it as the required review discipline. Do not replace it with a
remembered summary or duplicate its full rulebook here. This skill continues to
own adversarial activation, authority, counterpart, continuity, and consensus
boundaries.

If the canonical Purpose-First Review cannot be read, do not invoke the
Challenger or claim consensus. Return:

```text
ADVERSARIAL CONSENSUS: BLOCKED
Reason: canonical purpose-first review discipline unavailable
```

For each attacked candidate rule, boundary, assumption, or omission, apply these
gates in order:

1. **Establish the purpose** — state the concrete failure mode being prevented,
   the guarantee being preserved, and the observable success condition.
2. **Material-problem admission** — require a plausible trigger, causal path,
   and material impact tied to the current candidate. Preference, a cleaner
   design, remote hypotheticals, negligible impact, pre-existing unrelated
   problems, or imperfection alone are not findings. A better alternative does
   not make the current candidate defective.
3. **Purpose gate** — decide whether the candidate materially achieves its
   purpose and whether it materially undermines that purpose. Classify a failure
   as `PURPOSE FAILURE` or `PURPOSE UNDERMINING`; do not offset it with unrelated
   benefits.
4. **Purpose-preserving comparison** — only after an option passes the purpose
   gate, compare realistic tradeoffs. A candidate that fails the gate cannot be
   retained by weighted tradeoff; compare only corrections that restore and
   preserve the purpose sufficiently.
5. **Minimum-sufficient correction** — prefer an existing mechanism,
   clarification or consolidation, or a narrow control at the failure layer
   before broader/global instruction or review expansion. Add a safeguard only
   when it provides distinct material protection.

Review-rule growth, duplicate defensive prose, context expansion, instruction
conflict, false assurance, and drift are themselves material only when they
plausibly weaken the gate's purpose. After `NO PROBLEM`, close that attack and
stop; do not prolong the debate with optional polish or increasingly remote
objections.

## Intent Anchor Confirmation

Before invoking the Challenger, Matt presents an `Intent Anchor` that contains,
as applicable:

- desired outcome;
- confirmed priorities and results that must not be sacrificed;
- included Scope;
- excluded Scope and Non-Goals;
- preserved user-observable behavior;
- unavoidable external constraints when materially relevant;
- currently material tradeoffs;
- any still-provisional interpretation that is not itself user authority; and
- the exact designated Challenger.

Ask the user only to confirm that this is the intended basis for adversarial
review and that Matt may begin with the exact designated Challenger. Challenger
invocation is not allowed before that confirmation. Do not add a routine second
approval about repository disclosure. Use only the minimum relevant material
already available under the current user/host authority. Ask for additional
user authorization only when the Challenger actually requires sensitive/private
material, unrelated repository scope, or another disclosure expansion not already
covered by that authority.

Intent Anchor confirmation is not final product-contract approval, Behavior
approval, UI-authority approval, Spec approval, or permission to replace the
user's original words with Matt's summary. If the Anchor later proves to omit,
weaken, reorder, or contradict material user intent, return to the original
conversation context, correct the Anchor, and obtain renewed confirmation when
the correction can materially change the result.

## Challenger Boundary

The Challenger is read-only and advisory. It may attack reasoning and candidate
policy but may not:

- mutate product source, product state, planning artifacts, Spec, Tickets,
  Behavior/UI authorities, or external state;
- own or issue final product-policy authority;
- replace Matt's first-hand investigation or Behavior/UI conclusion;
- act as a delivery implementer or verifier merely because the same model or
  agent could later be used outside IIS Planning; or
- turn implementation facts, tests, votes, model agreement, or its own assertion
  into product authority.

For an external Oracle or other counterpart outside the local planning context,
provide only the minimum relevant current material needed to attack the candidate.
Do not disclose secrets, credentials, unrelated repository material, or adjacent
files merely because a counterpart asks for them. Existing user/host authority is
sufficient for ordinary relevant project material already in scope; ask the user
again only when access would materially expand into sensitive/private or unrelated
material not already authorized.

Invoke the exact designated counterpart only through the host- and user-authorized
mechanism that actually corresponds to that counterpart. A designated host
subagent uses the host's `Host Subagent Invocation Mechanism`; a designated Oracle
uses the configured authorized Oracle mechanism when one is available. Do not
reinterpret one mechanism or counterpart as the other. Give the invocation only
the current Intent Anchor, latest candidate, and material evidence needed for the
attack. When the mechanism supports conversation continuation or resumption, use
it for later rounds under the continuity rules below. If the exact designated
counterpart cannot be invoked or resumed far enough to produce a compliant current
assessment, use the `BLOCKED` boundary rather than inventing another transport,
agent, or fallback.

## Challenger Attack Contract

For every alleged challenge, require the Challenger to identify:

```text
Purpose: <failure mode, preserved guarantee, and observable success condition>
Challenge: <candidate rule, assumption, boundary, or omission being attacked>
Material problem: <plausible trigger -> causal path -> material impact>
Material-problem result: ESTABLISHED | NOT ESTABLISHED
Candidate relationship: <introduced or materially worsened by candidate | pre-existing/unrelated>
Counterexample: <concrete different in-scope observable result>
Intent impact: <which confirmed user outcome or priority is affected>
Evidence: <direct fact, external contract, or explicit inference and uncertainty>
Purpose-gate result: NOT APPLICABLE | PASS | PURPOSE FAILURE | PURPOSE UNDERMINING
Alternative: <stronger purpose-preserving result, when needed>
Minimum-sufficient correction: <smallest sufficient change if a finding survives>
Alternative tradeoffs: <new losses, risks, costs, and uncertainty after the alternative passes the purpose gate>
```

A better alternative alone is not a finding. If `Material-problem result` is
`NOT ESTABLISHED`, set `Purpose-gate result` to `NOT APPLICABLE`, return
`NO PROBLEM` for that attack, and do not require a correction. If the result is
`PURPOSE FAILURE` or `PURPOSE UNDERMINING`, do not
retain the current candidate by offsetting the failure against unrelated
benefits. Apply the same material-problem and purpose gates to every proposed
alternative before treating it as stronger.

As applicable, attack unsupported assumptions; invented priorities; unauthorized
Scope expansion or reduction; hidden product policy; identity and ownership;
lifecycle and terminal states; partial failure and recovery; interruption and
resume; retry, replay, duplicate, late, or out-of-order events; time and
concurrency; cross-capability invariants; current implementation accidentally
promoted into policy; false tradeoffs; unverifiable obligations; and two
reasonable implementations that satisfy the text while producing materially
different user-visible results.

The Challenger need not invent a weak objection merely to prolong the debate. If
no material objection survives its stress test, it may return
`NO MATERIAL OBJECTION` together with the material counterexamples it tried and
why they do not change the current candidate.

## Main Defense And Counterattack

For every material Challenger attack, Matt/Main must actively adjudicate it.
Passive acceptance such as "good point, adopted" is insufficient.

Perform all of the following:

1. **Intent defense** — identify the applicable original user context and
   confirmed Intent Anchor.
2. **Material-problem admission** — confirm the concrete trigger, causal path,
   material impact, and whether the current candidate introduced or materially
   worsened the problem. If that case is not established, record `NO PROBLEM`
   and close the attack rather than manufacturing a finding.
3. **Purpose gate** — determine whether the candidate materially achieves its
   established purpose and whether it materially undermines that purpose. A
   `PURPOSE FAILURE` or `PURPOSE UNDERMINING` result cannot be offset by unrelated
   benefits.
4. **Candidate defense or honest abandonment** — state the strongest current
   basis for the candidate; when direct evidence defeats it, abandon the
   candidate rather than fabricate a defense.
5. **Counterattack** — apply the same material-problem and purpose gates to the
   Challenger alternative, including sacrificed user results, new failure modes,
   hidden policy, Scope drift, unverifiable promises, implementation convenience
   promoted into policy, duplicated safeguards, context growth, instruction
   conflict, false assurance, drift, and other material costs.
6. **Alternative expansion** — do not restrict the decision to Matt's first idea
   versus the Challenger's first idea; consider a materially stronger third
   alternative when one exists.
7. **Minimum-sufficient correction** — among sufficiently purpose-preserving
   corrections, prefer the smallest clear mechanism that supplies the distinct
   material protection needed. Do not add broad review rules or defensive prose
   when an existing mechanism, clarification, consolidation, or narrow control
   is sufficient.
8. **Tradeoff adjudication** — only among options that pass the purpose gate,
   compare direction and magnitude of user impact, likelihood, uncertainty,
   evidence strength, interactions with other decisions, context and operating
   complexity, drift risk, auditability, maintenance, reversibility, and
   importance under the user's confirmed priorities.
9. **Disposition** — assign exactly one current disposition:

```text
NO PROBLEM            No concrete material defect or purpose failure was established; close the attack.
ADOPTED               Challenger correction is stronger.
DEFENDED              The current purpose-preserving candidate remains stronger; no required correction is established.
RECONSTRUCTED         A stronger third result replaces both presented options.
USER DECISION REQUIRED Material user outcomes remain different without a sufficiently stronger answer.
RETURN TO SCOPE SHAPER The challenge changes the bounded package/initiative boundary.
OUT OF SCOPE           The challenge does not affect the current approved planning unit.
```

A reconstructed result is not a midpoint for the sake of agreement. It must be
better supported against the confirmed user outcome.

## Debate Continuity And Progress

Prefer the same Challenger conversation or resumable context for follow-ups so
the counterpart must answer Matt's defense and counterattack rather than restart
the review from scratch. Carry forward already-established context conversationally;
do not restate the full Intent Anchor, authority hierarchy, closed objections, or
unchanged evidence in every round. Send only the latest material candidate delta,
open objection, rebuttal, or new evidence needed for the next exchange. This is
current-invocation conversational continuity, not a workflow database, roster,
queue, ledger, or persistent IIS state.

After Matt responds, require the Challenger to do one of:

```text
CONCEDE       Close the objection after considering Matt's rebuttal.
MAINTAIN      Keep it open with materially new evidence or a new counterexample.
USER DECISION Show why the remaining difference is genuinely user-owned.
```

There is no fixed round count. Every further round must close a material
objection, add material evidence, add a material counterexample, identify a real
user-owned decision, or assess the latest reconstructed candidate. Repeating a
closed objection without new support is not progress.

`NO PROBLEM`, `NO MATERIAL OBJECTION`, and `CONCEDE` are stop conditions for
that attack unless later materially new evidence or a new counterexample reopens
it. Optional improvements that establish no material defect cannot keep the
debate open. Do not split one root cause or add review clauses merely to create
more findings.

If the designated counterpart is unavailable or refuses the protocol such that
no current compliant adversarial assessment can be obtained, do not let Matt
unilaterally declare victory. Return:

```text
ADVERSARIAL CONSENSUS: BLOCKED
Reason: <exact counterpart or evidence/protocol limit>
```

The user may retry the same counterpart, designate another counterpart, or
explicitly withdraw adversarial consensus for this planning unit.

## User Decision Return

When two materially different user results remain and neither is sufficiently
stronger under the confirmed priorities, do not compromise or silently choose.
Return the exact product decision with Matt's recommendation, the Challenger's
position, evidence strength, uncertainty, and material tradeoffs. After the user
answers, update the Intent Anchor when necessary and continue with the same
designated Challenger unless the user changes that designation or withdraws the
gate.

## Consensus Completion

Return `ADVERSARIAL CONSENSUS REACHED` only when all are true:

- the Challenger reviewed the latest complete candidate, not an obsolete draft;
- every material objection has an explicit closure;
- every alleged challenge has an explicit material-problem result and, when
  admitted, an explicit purpose-gate result;
- the Challenger states that no material objection remains;
- Matt directly confirms that no Challenger counterexample was ignored;
- Matt directly verifies every load-bearing local fact it relies on rather than
  adopting Challenger narration as fact;
- no `PURPOSE FAILURE` or `PURPOSE UNDERMINING` remains in the latest candidate;
- no unresolved user-owned product decision remains;
- the candidate does not conflict with current Scope, Behavior, UI, or
  verification authority;
- no clearly stronger material alternative remains unexamined;
- every adopted or reconstructed safeguard is a minimum-sufficient correction
  with distinct material protection rather than defensive rule growth; and
- no material candidate change occurred after the Challenger's final review.

Consensus is advisory planning closure, not final product authority. After
consensus, Matt presents the final integrated shared understanding, material
accepted/reconstructed changes, defended/rejected attacks, and intentionally
retained tradeoffs to the user for final approval. Only that approval may unlock
Behavior/UI authority finalization and `to-spec`.

## Invalidation And Live Changes

A current consensus is no longer current for its affected scope when the user
materially changes the intended outcome or priorities, the Intent Anchor,
Outcome, Scope, Non-Goals, Behavior/UI meaning, or verification contract; or when
new direct evidence defeats a load-bearing assumption. If adversarial consensus
is still requested, re-review the affected latest candidate with the designated
Challenger before final approval.

If the user explicitly withdraws adversarial consensus, stop new Challenger
work and return to ordinary Ask Matt completion conditions; existing findings
remain advisory context only. If the user changes the designated Challenger,
prior consensus is not the new counterpart's consensus: the new counterpart must
review the latest complete bounded candidate.

Current explicit user changes and current canonical IIS planning rules apply at
the next controllable planning boundary; invocation start does not freeze an old
or superseded orchestration contract.

## Non-Goals

Do not create a persistent debate record, workflow runtime, consensus database,
vote, majority rule, generic multi-agent council, finding quota, speculative
objection loop, optional-polish loop, duplicated Purpose-First rulebook, broad
review-rule accumulation, mandatory review for ordinary Ask Matt work, second
verification authority, implementation review role, or Challenger-owned product
policy. The gate exists only to strengthen the user's confirmed planning result
when the user explicitly asked for this exact process and exact counterpart.
