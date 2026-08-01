# Declarative Planning Smoke

Executed: 2026-07-29

## Boundary

- Reused the existing disposable CLI at
  `/home/user01/project/matt/verification/smoke-workspaces/flow-1/disposable-cli`.
- Did not modify the disposable CLI, its tests, its existing `.scratch/`
  artifacts, product code, or existing examples.
- Did not create a fixture, validator, schema, planning artifact, Ticket, or
  implementation task for this smoke.
- This is a manual planning-dialogue smoke of `grill-with-docs`, `to-spec`, and
  `to-tickets`. The recorded decisions below are the observed planning outputs;
  no implementation was started.

## Verified Fixture Facts

- `main.go` parses `--config <path>` and checks the selected path with
  `os.Stat`; it contains no parser path responsible for a missing-file result.
- Its missing-file branch writes `configuration file not found` to stderr and
  returns `0`.
- `main_test.go` fixes the current missing-file exit code, exact stderr, and the
  existing-config success path.
- From the disposable CLI directory, `go version && go test ./...` passed with
  `go version go1.21.13 linux/amd64`.
- `go run . --config missing-config.yaml` returned exit code `0` with exact
  stderr `configuration file not found`.
- `go run . --config go.mod` returned exit code `0` and stdout
  `configuration loaded`.

## Scenario A: Suspected Cause Is Not A Contract

Planning input:

> Change a missing configuration file to exit with code 2. The parser handling
> seems to be the cause. Preserve the existing error text and the normal
> configuration path.

Observed planning result:

- `grill-with-docs` verified the direct `os.Stat` missing-file branch instead
  of asking the user to validate the parser claim.
- The shared contract fixed exit code `2`, exact error-text preservation, and
  normal configuration-path preservation.
- Neither a parser change nor a presumed root cause appeared in the Spec
  Requirement, Implementation Constraint, Ticket Goal, or Acceptance Criteria.
- `to-tickets` produced one desired-state Ticket. It did not split source and
  test changes into separate Tickets.

Result: pass.

## Scenario B: Explicit Technical Boundary Is Preserved

Planning input:

> Existing external callers use `--config`; do not change that flag. Change the
> missing-configuration result to exit code 2 while preserving the error text.

Observed planning result:

- The externally used `--config` invocation remained an explicit
  Implementation Constraint and preserved Acceptance Criterion.
- The result did not remove the constraint merely because it is technical; it
  is an intentionally fixed external compatibility boundary.
- No internal function, module, or test seam was made normative.

Result: pass.

## Scenario C: Unknown Mechanism Does Not Block Approval

Planning input:

> The desired exit code, error-text preservation, and normal-path preservation
> are clear. We have not chosen a function, file, or focused test seam.

Observed planning result after the test operator explicitly approved the
declarative contract:

- The Spec was eligible for `approved` status because the observable outcome,
  preserved behavior, boundaries, non-goals, and completion evidence were
  clear.
- Files, functions, and focused test seams did not appear in `Open Questions`.
- One outcome-focused Ticket was eligible for `ready`; its Verification named
  the observable CLI and test boundary without prescribing an internal seam.

Result: pass.

## Scenario D: Material Feasibility Uncertainty Blocks Approval

Planning input:

> The CLI must return exit code 2 for a missing configuration file, but source,
> tests, build configuration, invocation environment, and every external
> system are Non-Goals.

Observed planning result:

- The verified baseline returns `0`, so the result cannot change inside the
  stated mutation boundary.
- Matt did not invent a technical path or silently weaken the Non-Goals.
- The Spec remained `draft` pending a scope or feasibility decision, and no
  ready Ticket was produced.

Result: pass.

## Scenario E: Observable Precision Survives Declarative Planning

Reused Flow 1's existing product decision: missing configuration must return
exit code `2`; stderr remains `configuration file not found`; an existing
configuration continues to load successfully.

Observed planning result:

- The desired outcome and Acceptance Criteria retained the exact exit code,
  error text, and normal-path behavior.
- The result did not reduce those requirements to a vague request such as
  "improve error handling."

Result: pass.

## Conclusion

The smoke distinguishes provisional internal explanations from the declarative
contract, retains deliberate external technical constraints, permits approval
when only the implementation mechanism is unknown, and fails closed when no
feasible path is known inside the agreed boundary.
