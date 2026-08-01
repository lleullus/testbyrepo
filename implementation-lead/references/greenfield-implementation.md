# Greenfield Implementation

Greenfield mutation is authorized only when the ready Ticket explicitly requires initialization and
defines the package/public identity, target root, initial behavior, required source/config/test seed,
and allowed mutation envelope. Absence of files is not mutation authority.

Before the initialization Worker, Implementation Lead must have a complete pre-initialization Baseline
Capsule and an immutable ownership snapshot. Dispatch the selected Worker only for the exact
initialization envelope. Preserve any pre-existing user files and do not infer dependency, toolchain,
generated output, or package identity choices that planning leaves unresolved.

After the Worker, inspect every created path, public/export identity, lockfile provenance, callers,
Canonicals, tests, and integration boundaries. The initialization task becomes `IMPLEMENTED` from
source review only. A later independent Verification Lead invocation may consume the original Capsule;
it is not part of this invocation's completion state.
