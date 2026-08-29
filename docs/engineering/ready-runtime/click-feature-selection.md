# Click Feature Selection

## Provenance

- Local reference checkout: `/home/user01/project/click-upstream`
- Confirmed plugin version in `.codex-plugin/plugin.json`: `0.17.0`
- No local `v0.20*` tag was present when implementation started.
- Extraction style: behavior-level reimplementation; no Click source file is copied into this repository.
- License of the reference project: MIT.

The original plan mentioned the Click v0.20 line. The available reference and its published plugin metadata identify v0.17.0, so this implementation records the version actually inspected rather than inventing a later provenance point.

## Selected behavior

Only these execution-control meanings are carried over:

1. observation identity is normalized and recorded;
2. a successful identical observation at the same mutation revision is not re-run;
3. repository-wide inventory is bounded and disallowed after active implementation begins;
4. successful mutation advances an implementation-local revision and makes older evidence stale;
5. ambiguous shell text is not guessed to be read-only; explicit argv runners are used instead;
6. state writes are atomic and guarded by a bounded lock.

Selected parity references in Click v0.17.0:

- observation state and output bounds: `hooks/click_gate.py` observation helpers
- root inventory guard: `_prepare_observation` and related tests
- mutation revision: verification state `mutation_revision`
- structured capability execution: inspect/mutate runners using argv without a shell
- state persistence and locking: `_write_json` and `_state_lock`

## Explicitly not selected

The Ready runtime does not import or recreate:

- Click execution-contract schema
- contract approval or opaque contract id
- Always ON / Manual preference modes
- bypass/cancel UX
- Fix skill
- code-review mode
- Click planning flow
- quick/focused/full verification budgets
- verification-unit accounting
- browser/final-verification evidence meter
- a global guard for arbitrary software changes

Ready Ticket, Parent Spec, Behavior Authority and approved UI authority remain the product contract. The runtime only enforces observable execution discipline around that existing contract.
