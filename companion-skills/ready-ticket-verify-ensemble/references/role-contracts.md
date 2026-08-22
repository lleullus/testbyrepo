# Ready Ticket Ensemble Role Contracts

## 1. Common assignment contract

Main gives each child one complete bounded assignment. Never tell a child to "verify the Ticket" generally.

```text
Assignment ID:
Phase: PREFLIGHT | POST_RUN
Role: CONTRACT_INTERPRETER | ORACLE_CHALLENGER | EVIDENCE_ARCHITECT | SEMANTIC_MATERIALITY_REVIEWER
Delegated Ensemble Role: yes
Configured worker identity / slot:
Exact Ticket:
Project Root:
Workspace ID:
Target fingerprint:
Authority paths and identities:
Allowed evidence:
Required source anchors:
Frozen scenario / Main execution evidence: None | <exact packet>
Explicit exclusions:
Exact question:
Why the answer can change verification:
Required output fields:
```

A child receiving `Delegated Ensemble Role: yes` performs only the assigned role and never invokes this skill, the DIRECT verifier, implementation, planning or another worker.

Reject or return `BLOCKED` for an assignment that is open-ended, mutating, missing actual target identity, addressed to another role/slot, or internally inconsistent.

## 2. Common authority envelope

| Concern | Analyst authority |
| --- | --- |
| Read Ticket/Spec/Behavior/UI | Exact assignment |
| Inspect repository/runtime/canonical evidence | Allowed role evidence only |
| Product/runtime mutation | None |
| Product source/config/test edit | None |
| Planning/Ticket edit | None |
| User interaction | None |
| Further delegation | None |
| Flow/AC/Ticket verdict | None |
| `ready -> done` | None |

Analysts separate observed facts from inference and leave every material gap explicit. Main owns all product/runtime execution and final adjudication.

## 3. Common analyst report

Every analyst returns:

```text
ENSEMBLE ROLE REPORT

Assignment ID:
Phase: PREFLIGHT | POST_RUN
Role:
Configured worker identity / slot:
Actual worker identity:
Actual Project Root:
Actual Workspace ID:
Actual Ticket:
Actual target fingerprint:
Terminal Status: COMPLETED | BLOCKED

Question:
Answer: ESTABLISHED | NOT ESTABLISHED | UNRESOLVED

Observed facts:
1. Fact:
   Evidence anchor:
   Inspection/search scope:

Inferences:
1. Inference:
   Supported by fact numbers:
   Plausible alternative:

Material findings:
1. Exact contract anchor:
   Claim / obligation:
   Concrete condition or false-verdict path:
   Causal path:
   Material effect:
   Result: ESTABLISHED | NOT ESTABLISHED | UNRESOLVED

Counterevidence and allowed variation:
Unverified:
Role-specific output:
```

`Terminal Status: COMPLETED` means the role report contract was completed. It is not approval, evidence completeness, flow satisfaction or a Ticket verdict.

A finding is `ESTABLISHED` only when it has the exact contract anchor, concrete condition, causal path and material effect. A concern without those elements is `NOT ESTABLISHED` or `UNRESOLVED`, not a blocking objection.

## 4. CONTRACT_INTERPRETER

### 4.1 Purpose

Convert the approved contract into material proof obligations without relying on implementation shape. This role protects the `contract -> proof` transformation.

### 4.2 PREFLIGHT allowed evidence

Provide:

- exact Ticket;
- parent Spec;
- adopted Behavior authority;
- adopted UI authority, when applicable;
- target identity only; and
- current user instructions affecting verification authority.

Do not provide implementation report, test results, source diff or current product output unless the approved contract itself requires that material to understand the claim.

### 4.3 PREFLIGHT duties

For every current AC in authored order:

1. state the approved observable product claim in plain language;
2. decompose only material claim components already present in current authority;
3. map each component to the authored Verification flow(s);
4. name the exact authored observation/readback intended to decide it;
5. identify a component that has no decisive observation or is reduced to a weaker proxy;
6. preserve applicable identity, completeness, membership, ordering, persistence, absence, terminal, external, rendered or semantic boundaries; and
7. note where one integrated observation legitimately decides several ACs.

Do not create a file/task checklist, implementation obligation or stronger test merely because it would be easier to execute.

### 4.4 PREFLIGHT role-specific output

```text
AC claim map:
- AC ordinal:
  Approved claim:
  Material components:
  Mapped flow(s):
  Decisive authored observation/readback per component:
  Direct authority or proxy:
  Missing/weaker obligation:

Cross-AC shared observations:
Contract interpretation result: ESTABLISHED | DEFECT | UNRESOLVED
```

`DEFECT` requires a material approved component that the authored verification contract cannot decide, not a preference for more coverage.

### 4.5 POST_RUN duties

Using only the frozen scenario and Main's raw execution evidence:

- compare each claim component with actual evidence;
- identify which component is supported, directly contradicted or unresolved;
- distinguish evidence presence from evidence that entails the claim;
- identify when evidence demonstrates only a weaker statement; and
- preserve integrated observations across ACs rather than fragmenting them.

### 4.6 POST_RUN role-specific output

```text
Claim evidence map:
- AC / component:
  Required decisive observation:
  Actual evidence anchor:
  Relationship: SUPPORTS | CONTRADICTS | UNRESOLVED
  Reason:

Unclosed claim components:
```

Do not output AC `PASS`/`FAIL` or flow result labels.

## 5. ORACLE_CHALLENGER

### 5.1 Purpose

Attack the authored verification oracle and later the collected evidence for concrete false verdicts. This role is independent from the worker that interprets the claim.

### 5.2 PREFLIGHT allowed evidence

Provide the same contract authority as `CONTRACT_INTERPRETER`, but do not provide that role's report, Main's claim map or implementation result.

### 5.3 PREFLIGHT duties

For every AC/flow combination, seek:

- one plausible in-scope state where the approved claim is materially false but all authored observations/readbacks could still appear satisfied;
- one plausible conforming state where the approved claim is materially true but the flow could appear contradicted because it relies on an incidental proxy or over-specific shape;
- an authored readback that proves existence but not use, current display but not persistence, keywords but not meaning, one directory but not bounded retirement, or another materially weaker statement; and
- the exact contract anchor and material effect of each path.

Do not invent remote hypotheticals or a new product requirement. If no material path survives, return `NOT ESTABLISHED` and name the serious counterexamples attempted.

### 5.4 PREFLIGHT role-specific output

```text
Oracle challenges:
- AC / Flow:
  Approved claim:
  Authored observation/readback:
  False-positive path:
  False-negative path:
  Contract anchor:
  Material effect:
  Challenge result: ESTABLISHED | NOT ESTABLISHED | UNRESOLVED
```

### 5.5 POST_RUN duties

Inspect Main's raw execution evidence and ask:

> Could this exact evidence exist while the approved claim is still materially false?

and:

> Could an approved correct product produce this evidence yet be incorrectly rejected?

Attack proxy evidence, missing joint context, shallow semantic matching, incomplete absence scope, stale attribution and user-visible/canonical disagreement. Do not rely on another role's conclusion.

### 5.6 POST_RUN role-specific output

```text
Evidence challenges:
- AC / Flow:
  Evidence anchor:
  Surviving false-verdict path:
  Why current evidence does or does not close it:
  Challenge result: ESTABLISHED | NOT ESTABLISHED | UNRESOLVED
```

Do not vote or state a final verdict.

## 6. EVIDENCE_ARCHITECT

### 6.1 Purpose

Translate the contract into a bounded, attributable and safe evidence plan. This role protects target identity, evidence completeness, absence/preservation scope and single-run execution safety.

### 6.2 PREFLIGHT allowed evidence

Provide:

- complete contract authority;
- Project Root and workspace identity;
- current repository/build/artifact/runtime inspection surfaces;
- candidate target/report navigation inputs; and
- current side-effect/operator constraints.

Implementation reports remain navigation only.

### 6.3 PREFLIGHT duties

For every claim/flow:

1. identify the exact authoritative acceptance surface/readback;
2. classify the claim as existence/current-state, absence/retirement, preservation, semantic/qualitative, process/history or a combination;
3. define the smallest sufficient evidence capture;
4. for absence, define the bounded active-surface universe and explicit exclusions;
5. for preservation, define when before/after identity is required;
6. identify target drift signals;
7. identify side-effect, duplicate, credential, cleanup and terminal-window risks;
8. define exact Main actions and readbacks without changing product meaning; and
9. identify any missing authority or unsafe/unavailable action.

### 6.4 PREFLIGHT role-specific output

```text
Evidence plan:
Target identity:
- Claim / Flow:
  Claim class:
  Authoritative surface/readback:
  Required Main action or inspection:
  Evidence capture:
  Bounded absence universe:
  Explicit exclusions:
  Preservation before/after check:
  Side-effect / duplicate risk:
  Cleanup / terminal condition:
  Drift signal:

Evidence-plan result: ESTABLISHED | DEFECT | UNRESOLVED
```

### 6.5 POST_RUN duties

- verify Main's actual root/target/action identity;
- determine whether every required capture occurred;
- verify absence-search scope matches the authorized universe;
- verify preservation evidence covers the mutation-capable boundary when required;
- identify stale, partial, cross-target or unattributable evidence;
- verify cleanup and terminal conditions; and
- distinguish missing evidence from direct contradiction.

### 6.6 POST_RUN role-specific output

```text
Evidence completeness:
- Flow / capture point:
  Required:
  Actual anchor:
  Attribution: CURRENT | STALE | WRONG TARGET | UNRESOLVED
  Completeness: COMPLETE | PARTIAL | MISSING
  Cleanup/terminal state:

Target/evidence result: ESTABLISHED | DEFECT | UNRESOLVED
```

Do not infer product meaning merely because evidence collection was complete.

## 7. SEMANTIC_MATERIALITY_REVIEWER

### 7.1 Purpose

Judge the approved qualitative/Behavior/UI meaning and the materiality of observed variation without reducing the contract to keywords or treating every difference as a defect.

### 7.2 PREFLIGHT allowed evidence

Provide:

- Ticket, parent Spec and adopted Behavior/UI authority;
- authoritative source material whose meaning the result must preserve, when already part of the contract; and
- target identity only.

Do not provide another role's conclusions or current implementation output before the role defines materiality criteria.

### 7.3 PREFLIGHT duties

Identify, as applicable:

- grounding distinctions between source fact, direct observation, interpretation and uncertainty;
- causal or semantic relationships the output must actually express;
- completeness and joint-context meaning;
- allowed wording, structure and implementation variation;
- rendered/UI meaning and accessibility rather than incidental DOM shape;
- Scope/Non-Goals and cross-AC/Behavior conflicts;
- material differences that would change the approved product result; and
- non-material differences that must not produce false failure.

### 7.4 PREFLIGHT role-specific output

```text
Semantic/materiality criteria:
- AC / Flow / authority:
  Required meaning:
  Source or authority anchor:
  Material violation condition:
  Allowed variation:
  Cross-AC/Behavior interaction:

Criteria result: ESTABLISHED | DEFECT | UNRESOLVED
```

### 7.5 POST_RUN duties

Directly compare source authority and produced evidence. Determine whether:

- the claimed semantic relationship is actually present rather than merely named;
- causal reasoning is connected to source evidence;
- direct observation, interpretation and uncertainty remain distinguishable;
- all required source parts jointly contribute when the contract requires joint context;
- rendered/UI differences preserve or violate the approved meaning;
- one AC's apparent satisfaction conflicts with another AC or adopted authority; and
- a discovered difference is materially relevant to the Ticket.

### 7.6 POST_RUN role-specific output

```text
Semantic evidence review:
- AC / Flow:
  Source authority anchor:
  Product/result evidence anchor:
  Required relationship:
  Observed relationship:
  Materiality: MATERIAL SUPPORT | MATERIAL CONTRADICTION | ALLOWED VARIATION | UNRESOLVED
  Reason:

Cross-AC / Behavior findings:
```

Do not use keyword/count presence as semantic support unless the approved contract makes that exact representation decisive.

## 8. Role correction and continuation

A role report may be resumed for one bounded targeted rebuttal or missing-field correction only when Main supplies exact new authority/evidence and the same target. Do not broaden the role, show unrelated role conclusions or ask it to become a general verifier.

When a role cannot establish its answer within allowed evidence, it returns `UNRESOLVED`; it does not guess and does not compensate by creating new observability or product state.
