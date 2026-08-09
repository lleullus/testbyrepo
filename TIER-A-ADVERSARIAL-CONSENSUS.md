# A Tier Adversarial Consensus

## Final Decision

A tier accepts exactly one validator-strengthening correction in
`verification-lead/coverage_gate.py`: canonical qualifier-source material used
for current-source validation and `challenge_fp` must preserve Markdown block
and list hierarchy.

The current `_selected_source` path applies `_normalize_markdown`, which flattens
sibling and nested list forms into identical content and source IDs. A change to
an approved Behavior authority's hierarchy can therefore leave the Canonical
Source Package, `raw_fingerprint`, `challenge_fp`, prior effective-PASS receipt,
approval mode, and approval ID unchanged.

No other A-tier validator or test change is accepted. This document records the
decision; it does not implement the correction.

## Review Frame

- Default: preserve the current design.
- A-tier acceptance threshold: a concrete current input-to-wrong-result path
  that violates the written contract.
- Accepted classes: fail-open, false-pass, false-reject, wrong authority
  binding, or stale acceptance.
- Excluded grounds: missing tests alone, theoretical malformed input, broad
  robustness, nicer errors, schema generalization, speculative parser
  ambiguity, or defense-in-depth.
- A local test change is justified only when it covers the exact reproduced
  defect path.
- Every Oracle turn received a fresh complete repository ZIP.

## Reproduced Defect

### Affected Path

- `verification-lead/coverage_gate.py::_normalize_markdown`
- `verification-lead/coverage_gate.py::_selected_source`
- `verification-lead/coverage_gate.py::_canonical_package`
- `verification-lead/coverage_gate.py::_fingerprints`
- `verification-lead/coverage_gate.py::_validate_envelope`
- `verification-lead/coverage_gate.py::_validate_receipt`
- `verification-lead/coverage_gate.py::approve`

### Minimal Input

Original approved authority hierarchy:

```markdown
- Trigger A
  - Result X
- Trigger B
  - Result Y
```

Changed hierarchy:

```markdown
- Trigger A
  - Result X
  - Trigger B
    - Result Y
```

`Trigger B` changes from a sibling of `Trigger A` to its child. This changes the
Markdown list tree and the binding of the trigger/result branch while retaining
the same textual tokens and order.

### Confirmed Current Result

Local execution against the current module produced:

```text
_normalize_markdown(before) = '- Trigger A - Result X - Trigger B - Result Y'
_normalize_markdown(after)  = '- Trigger A - Result X - Trigger B - Result Y'
normalized values equal     = True
selected source IDs equal   = True
```

The remaining stale-acceptance path follows directly from the current code:

1. `_selected_source` stores the normalized value as both source `content` and
   source-ID digest input.
2. `_canonical_package` places that selected source into `qualifier_sources` and
   hashes the package as `raw_fingerprint`.
3. `_fingerprints` includes the canonical package in `challenge_fp`.
4. `_validate_envelope` regenerates the same flattened canonical package and
   therefore does not report stale sources.
5. `_validate_receipt` sees the same `challenge_fp` and accepts the prior
   effective-PASS chain.
6. `approve` can retain the prior approval result and ID because the plan input
   also remains unchanged.

This is stale acceptance and a false pass, not merely an unfriendly error or a
missing test.

## Violated Contract

The current Verification Lead contract requires:

- the Challenger to inspect `raw canonical slices`;
- every materially distinct observable predicate and explicit trigger/result
  branch to be preserved; and
- Challenger attestation reuse only while its exact semantic input remains
  current.

Flattening sibling and nested list forms makes a changed authority hierarchy
invisible to both the Challenger input and freshness fingerprint.

The defect is independent of the S-tier wording decision. S did not create this
authority or freshness requirement.

## Accepted Correction Boundary

Correct only canonical qualifier-source representation and the directly
necessary citation comparison:

1. Preserve Markdown block boundaries, newlines, and leading indentation in the
   selected source after Unicode and line-ending normalization.
2. Use the structure-preserving value for `qualifier_sources[*].content`, source
   ID derivation, `raw_fingerprint`, and therefore `challenge_fp`.
3. Keep tolerant qualifier citation matching by comparing normalized
   `source_text` against a separate prose-normalized view of the preserved
   source content.

Do not change:

- Ticket denominator-root ownership or extraction;
- Unit, qualifier-binding, Coverage Edge, or Scenario semantics;
- Challenger authority or attestation schemas;
- approval modes or approval authority;
- scope-containment rules;
- durable artifact formats;
- route-index behavior; or
- legacy parser behavior.

Do not add a generalized Markdown parser or make the validator decide the
meaning of a hierarchy. The correction only ensures that changed structure is
visible to the independent Challenger and invalidates prior attestation.

## Accepted Test Boundary

Add one focused regression case to the existing behavior-workflow test module.
The test should:

1. construct a valid envelope, effective-PASS receipt, and approval using an
   approved Behavior authority;
2. change one authority list branch from sibling to nested;
3. prove that the rebuilt `challenge_fp` changes; and
4. prove that the prior receipt can no longer produce approval.

The assertion should cover behavior, not a fixed digest or private normalized
string representation.

No unrelated malformed-input, schema, parser, or coverage tests are authorized.

## Tradeoff

Preserving source structure can invalidate receipts for semantically neutral
format changes such as harmless line wrapping or whitespace cleanup. That can
increase Challenger calls and partially reduce the S-tier receipt-reuse benefit.

The conservative decision accepts occasional unnecessary rechallenge rather
than stale acceptance of changed authority hierarchy. A future narrowing may
reduce over-invalidation only if it cannot restore sibling/nested collisions or
hide Challenger-visible structure.

Session-temporary envelopes and receipts require no durable migration.

## Rollback Or Narrowing Triggers

Narrow or roll back the implementation approach if it:

- changes Ticket denominator-root extraction or Unit semantics;
- makes unchanged active examples fail a fresh `build`;
- breaks currently valid single-line or multiline qualifier citations;
- introduces a durable artifact or schema migration;
- adds semantic scope judgment to the validator; or
- invalidates changes without preserving the changed hierarchy in
  Challenger-visible canonical content.

Never restore the sibling/nested normalization collision.

## Rejected A Candidates

| Candidate | Disposition | Reason |
| --- | --- | --- |
| Generic malformed-input hardening | Rejected | No reproduced wrong authoritative result. |
| Tests added only for absent coverage | Rejected | Test absence does not prove current behavior is wrong. |
| Nicer error messages | Rejected | No authority, freshness, or acceptance defect. |
| Broader schemas or semantic Markdown parsing | Rejected | Expands validator authority and maintenance without necessity. |
| S-tier wording translated into gate-code changes | Rejected | S receipt reuse requires no gate API or behavior change. |
| Route-index persistence | Excluded | B-tier concern. |
| Legacy parser tolerance | Excluded | B-tier concern. |

## Evidence And Sessions

- A/B ChatGPT conversation:
  `https://chatgpt.com/c/6a78a6ea-6748-83ee-8762-13187a198385`
- Provisional no-change session: `slots-context-iistiera-2504ad1b89`
- Final adversarial followup: `slots-followup-iistiera-b8b5a8a971`
- Same-conversation authoritative readback: verified
- Managed browser: slot 1, local CDP `127.0.0.1:19222`
- Reasoning selection: Pro, verified by the browser control
- Model selection: current selected model requested as GPT-5.6 Sol; exact active
  model label was not independently verified by Oracle metadata
- Final Oracle attachment: one generated ZIP with 146 files, 1,101,033 selected
  bytes, and SHA-256
  `2e20f129e6e6cf2515586930fcab0290b511df8017eaed3fc24f9e4429df80cc`
- Local confirmation: current `_normalize_markdown` and `_source_id` collide for
  the sibling and nested reproducers above

## Consensus Status

No material A-tier disagreement remains. A accepts only this reproduced
hierarchy-freshness defect and its single focused regression path. The decision
does not certify all validators as defect-free and does not imply any B-tier
disposition.
