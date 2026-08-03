# Completion Record v3 — retired historical contract

`implementation-result-v3` is not an active publication contract.

Every new publish request using that protocol fails with `PROTOCOL_RETIRED` before SOURCE/RUNTIME
shape validation. There is no dual publication, fallback route, evidence adapter, or conversion to
`implementation-handoff-v1` or `verification-result-v1`.

The only supported operation is byte-preserving historical read of an already-existing immutable v3
artifact by its original `implementation:v3:<id>` ref. Historical read does not:

- establish current source or planning identity;
- create a workflow node or continuation edge;
- produce an ImplementationHandoff;
- certify an Acceptance Criterion;
- authorize remediation;
- copy a historical runtime observation into a VerificationRun.

Active callers must use:

```text
Implementation Lead -> implementation-handoff-v1
Verification Lead   -> verification-result-v1
```

This file remains only so repositories and audits that mention the retired format have an explicit
non-callable interpretation.
