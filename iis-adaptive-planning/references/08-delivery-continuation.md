# Delivery Continuation Outside Adaptive Planning

## Ownership versus request continuity

Keep two boundaries separate:

1. **IIS Adaptive Planning ownership** ends at one approved Spec plus its validated complete Ready Ticket Set.
2. **The user's current execution envelope** may be broader and may already authorize implementation, verification, correction, and terminal `done` progression.

Therefore this is valid when the user explicitly authorized the whole route:

```text
Outer caller / current user execution envelope
  -> IIS Adaptive Planning
     -> Scope Shaper
     -> current INC
     -> Ask Matt / Behavior / UI
     -> approved Spec
     -> validated Ready Ticket Set
     -> Adaptive Planning terminal boundary
  -> ready-ticket-implement
  -> ready-ticket-verify
  -> done when the verifier establishes VERIFIED and performs its guarded transition
```

The delivery calls are not actions performed **by** Adaptive Planning. They are separate skill invocations performed by the outer caller under authority already present in the user's current request.

## When continuation needs no new user prompt

After Adaptive Planning reaches Ready Tickets, continue directly into delivery only when the current user request already and unambiguously authorizes that delivery scope.

Examples of sufficient current authority:

- `Adaptive로 계획하고 구현/검증까지 해서 done으로 만들어.`
- `이 목표를 어댑티브로 끝까지 처리해. 계획 문제가 나오면 알아서 reshape하고 다시 구현/검증해.`
- an equivalent exact instruction that includes current planning plus implementation and verification.

In those cases, do not insert a new approval ceremony solely because the owning skill changes at the Ready Ticket boundary.

If the current request authorizes only planning, stop after Ready Tickets. Do not infer delivery authority from Adaptive activation, the Mandate, a Ready Ticket, or the fact that implementation appears safe/easy.

## Delivery skill authority remains intact

Before each delivery phase, discover and use the current installed skill contract.

- `ready-ticket-implement` owns exact Ready Ticket implementation and implementer self-check.
- `ready-ticket-verify` owns fresh verification, final verdict, and guarded `ready -> done` progression.

Adaptive does not weaken their admission gates, status rules, evidence rules, auditor configuration, or terminal semantics.

## Auditor configuration

Do not invent auditors merely because the outer route is autonomous.

When the user did not request audit coverage and supplied no count, let each current delivery skill apply its own normal default. Under the current contracts this means:

```text
ready-ticket-implement: Auditor Count 0
ready-ticket-verify: AC Runtime Auditor Count 0
```

If the user explicitly supplied an auditor count/configuration, preserve that exact authority. Adaptive Mandate authority does not select, increase, decrease, or substitute delivery auditors.

## Verification outcome routing

After implementation, verification is not assumed to produce `done`.

Route fresh verification evidence by its actual result and the Adaptive triage contract:

```text
VERIFIED
  -> ready-ticket-verify owns guarded ready -> done

IMPLEMENTATION_DEFECT
  -> if the user execution envelope authorizes correction, outer caller invokes ready-ticket-implement again on the still-ready Ticket
  -> then fresh ready-ticket-verify

VERIFICATION_MECHANISM_DEFECT
  -> correct the verification-owned setup/mechanism without changing product authority
  -> fresh ready-ticket-verify when current authority permits

CONTRACT_OVERREACH
  -> if adaptive correction is authorized, outer caller re-enters IIS Adaptive Planning
  -> owning planning leaf corrects Ticket/Spec authority as required
  -> fresh valid Ready Ticket(s)
  -> separate implementation/verification again as needed

CURRENT_INCREMENT_MISMATCH
  -> if adaptive correction is authorized, outer caller re-enters IIS Adaptive Planning at Scope Shaper
  -> reshape current planning unit against actual state
  -> fresh Ready Ticket Set
  -> separate implementation/verification again as needed

INCONCLUSIVE
  -> obtain only the missing evidence/condition owned by the current contract
  -> do not manufacture implementation or planning changes
```

Do not retroactively turn an earlier verifier failure into PASS after planning changes. Fresh planning authority requires fresh delivery/verification evidence.

## Continuous end-to-end loop

When the user explicitly authorized end-to-end adaptive delivery and adaptive correction, the outer caller may continue this loop without repeated user confirmation while every action remains inside that authority:

```text
Adaptive Planning
  -> Ready Ticket Set
  -> Implement / Verify current Tickets
       -> implementation defect -> Implement -> Verify
       -> verification mechanism defect -> fresh Verify path
       -> planning defect -> Adaptive Planning correction -> Ready Ticket Set -> delivery
       -> unresolved user-owned product trade-off -> return to user
       -> all current Tickets VERIFIED -> done
            -> CURRENT_INCREMENT -> stop success continuation
            -> BOUNDED_OUTCOME | MANDATE_OUTCOME
                 -> fresh actual-state outcome check
                      -> MANDATE_SATISFIED -> stop
                      -> NEXT_INCREMENT_REQUIRED -> Scope Shaper -> new INC -> Adaptive Planning -> delivery
                      -> USER_DECISION_REQUIRED -> return to user
```

This is **not** a new IIS workflow engine. It is the outer caller consuming separate existing skills under one explicit user request and returning planning evidence to Adaptive only when planning owns the correction.

## Successful current-Increment continuation

Do not treat one Ticket's `done` as delivery of the whole current Increment. Success re-entry is eligible only after every current canonical Ticket in the current approved Spec's Ready Ticket Set has reached exact `done` through its owning verification lifecycle.

Then apply the active Mandate's Continuation Authority:

```text
CURRENT_INCREMENT
  -> success continuation ends here

BOUNDED_OUTCOME | MANDATE_OUTCOME
  -> inspect fresh actual product state and authoritative readback
  -> evaluate the applicable outcome
       -> MANDATE_SATISFIED
       -> NEXT_INCREMENT_REQUIRED
       -> USER_DECISION_REQUIRED
```

- `MANDATE_SATISFIED`: the applicable bounded or Mandate outcome is actually satisfied. End the broader Adaptive execution even if an old Work Package list or provisional horizon still contains ideas.
- `NEXT_INCREMENT_REQUIRED`: the applicable outcome is not yet satisfied and current authority resolves the direction. Re-enter IIS Adaptive Planning, then Scope Shaper against fresh actual state. Scope Shaper selects exactly one new current Increment; it does not automatically admit the next previously listed WP/INC.
- `USER_DECISION_REQUIRED`: the applicable outcome is not yet satisfied but current authority leaves a material user-owned product trade-off. Return only that decision.

A `NEXT_INCREMENT_REQUIRED` cycle must be based on fresh actual product state or other material new authority/evidence created since the prior construction cycle. Do not repeatedly replay the same provisional plan without a changed state/evidence basis.

If the outer user's current execution envelope also authorizes delivery through the applicable continuation boundary, it may consume the newly produced Ready Ticket Set through the separate delivery skills and repeat this success loop. Continuation Authority by itself remains planning authority and does not create delivery authority.

## Hard boundaries

Even under an end-to-end execution envelope:

- Adaptive Planning does not become implementation or verification authority.
- Delivery skills do not rewrite Scope, Spec, Ticket meaning to make verification pass.
- The outer caller does not infer deployment, credentials, production/shared external mutation, destructive action, or other authority not actually present in the request/contract.
- A material user-owned product trade-off outside the Mandate returns to the user.
- `done` belongs to the verifier's current guarded terminal transition, not to Adaptive Planning or implementation self-check.
