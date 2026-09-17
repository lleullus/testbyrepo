# PLAN-001: B1 Runtime Identity Closure

## 1. Authority, boundary, and target observation

This Plan is the execution method for `/home/user01/project/oracle/docs/planning/work/b1-self-contained/SCOPE.md` (`iis-scope/v1`, `Status: ready`, SHA-256 `c79de2f1f8e87d180da9fc2e5b5b556b110d00ab5951b167580b6838547db0ab`). It does not add product meaning or authorize implementation.

Bound product authority:

- `/home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md`, SHA-256 `b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6`.
- Bound transition source: `/home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md`, SHA-256 `6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9`, specifically Block `B1-RUNTIME-CLOSURE`, `GI-05`~`GI-08`, `GI-11`~`GI-12`, `PI-01`~`PI-04`, `PI-08`, `PI-12`, and `HA-01 Runtime identity closure`.
- No repository-investigation artifact was supplied.

The observable target is one atomic runtime cut in which the Python slot wrapper resolves an Oracle CLI without a personal HOME/NVM path, the same resolved CLI exposes the product-owned file-selection interface, the wrapper proves supported Node/release/protocol compatibility before a possible remote submission, and file-bearing requests still become exactly one compressed ZIP with preserved relative member paths. Missing, ambiguous, stale, or mismatched components must return a specific non-zero pre-submission rejection. File-free requests must not create a ZIP.

This Scope does not implement recovery attribution, the default `2h` policy/CI work of later Blocks, or clean-environment live Browser E2E. A non-submitting alternate-prefix smoke is required here; transformation completion remains outside this Scope.

## 2. Grounding

### EXISTING

1. **Personal executable default is on the live command path.** `oracle-browser-slots/oracle_browser_slots/runner.py:23,44-58,617-725` defines `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`, chooses it unless a constructor/environment override exists, and rejects an `argv[0]` that is not the chosen absolute path. `cli.py:85-135`, `allocator.py:43-57,59-153`, and `followup.py:907-910` construct `JobRunner` for public `run`, `submit`, and followup paths. Current `runner.py` SHA-256 is `f993b1ed0e3e5359f34c5d6dd7d6abf079dcc5390e0a6f858adb99e3ece2a1be`, matching the bound transition entry.
2. **Selector provenance is separately hard-coded.** `oracle-browser-slots/oracle_browser_slots/attachments.py:23,352-449,452-541` independently derives a sibling `node`, walks into `lib/node_modules/@steipete/oracle/dist/src/oracle/files.js` and `dist/src/cli/options.js`, and dynamically imports private exports. Current `attachments.py` SHA-256 is `2b802d2211360c749260a224c15ee42a88b83b6ef90fe5595f4e22e1346aa6f1`, matching the bound transition entry.
3. **The product already owns the selection semantics.** `src/cli/options.ts:10-71` merges `file/include/files/path/paths`, comma-splits, trims, and deduplicates literal paths by normalized absolute identity and patterns by raw pattern. `src/oracle/files.ts:27-227,232-452` resolves literals/directories/globs, exclusions, `.gitignore`, dotfile opt-in, default ignored directories, regular-file filtering, and stable no-match/error behavior. The implementation is compiled beneath the same `dist` tree as the browser CLI; the defect is the Python wrapper's private filesystem import, not absence of product-owned behavior.
4. **Single-ZIP ownership already exists in Python.** `attachments.py:366-449,600-680,683-737` selects before claim, preserves relative paths, rejects normalized member collisions, creates one deflated `oracle-attachments.zip`, rewrites all path-like inputs to one `--file`, forces attachment upload/wait policy, and creates no object when there are no file inputs. `PreparedAttachment` owns cleanup and manifest readback for the request lifetime.
5. **Current ordering is suitable for fail-closed preconditions.** `runner.py:60-164` validates before attachment preparation and claim for explicit `run`. `allocator.py:101-153` validates before attachment preparation/queue assignment for `submit` (the request-id reservation is local and not a remote effect). `runner.py:402-615` is the child process boundary. A runtime-compatibility rejection placed in command normalization therefore precedes ZIP creation, slot claim, child start, and remote Browser submission.
6. **Current package metadata supplies the declared contract.** `/home/user01/project/oracle/package.json:2-3,16-29,35-36,101-112` declares package `@steipete/oracle`, version `0.16.1`, `oracle -> dist/bin/oracle-cli.js`, shipped `dist/**/*`, and Node `>=24`. Its SHA-256 is `9fdd86af8557bca025be71011aa8f5440b6c7e8b181c3570da978a2fc4f4ec44`, matching the transition entry.
7. **Current environment observation is only entry evidence.** `node --version` returned `v24.18.0`; `which oracle` returned `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`; that path resolves to `/home/user01/project/oracle/dist/bin/oracle-cli.js`. This confirms the current coupling and a usable starting artifact, not portability or completion.
8. **Existing behavioral coverage is reusable.** `tests/test_slots.py:2993-3138` covers directory/glob/exclusion/ignore behavior, preserved relative ZIP members, deflate compression, collisions, and normalized command policy. `tests/test_slots.py:3184-3377` covers pre-claim selection failure, child failure cleanup, manifest failure, and sessionless dry-run. Many runner tests inject `TEST_ORACLE_CLI`; they must be migrated to the new runtime seam rather than preserved as a production bypass.
9. The exact Scope was checked with the canonical validator and returned `VALID`. This establishes structure/source binding only, not method admission or transition approval.

### PROPOSED

1. Add one package-local runtime resolver (for example `oracle_browser_slots/runtime.py`) and one immutable `ResolvedOracleRuntime` value per wrapper invocation. It becomes the sole owner of Node path, Oracle entry path, package root/name/version, CLI SHA-256, selector protocol, and diagnostic readback. `runner.py` and `attachments.py` consume this value; neither discovers a second runtime.
2. Resolve candidates in a deterministic order: the Oracle entry under the product root derived from the installed wrapper location, then `shutil.which("oracle")`. Canonicalize every candidate with strict realpath resolution. There is no personal path, NVM version path, symlink-to-personal fallback, or silent selection of an arbitrary same-named executable.
3. Prove the candidate by locating its owning `package.json` and requiring `name == "@steipete/oracle"`, a non-empty version in the wrapper's explicit compatibility table, and `bin.oracle` to resolve to the exact selected entry. Resolve `node` from PATH, run the selected Node directly as `[resolved_node, resolved_oracle_entry, ...]`, require major version `>=24`, and require the CLI's `--version` readback to equal the owning package version. Record SHA-256 of the actual Oracle entry so readback identifies the artifact rather than relying on a version string alone.
4. Add a stable, non-submitting, machine-readable package interface to the Node CLI, under a named command such as `oracle runtime file-selection`. It statically calls the package's own `mergePathLikeOptions`, `dedupePathInputs`, and `readFiles`; it never accepts an import path from Python. A capability action returns schema/protocol plus the running package name/version. A selection action accepts JSON on stdin (`cwd` and the five path-input groups) and returns JSON containing the same identity and selected absolute file paths. Logs go to stderr and stdout contains one schema-valid response.
5. Replace `select_stock_files`'s generated JavaScript/private imports with a call through the already resolved runtime to that stable command. Require response schema `oracle-file-selection/v1` (or the implementation's single reviewed equivalent), package identity equal to the resolver readback, a string-only file list, and exit code 0. Any parse, identity, protocol, or selection error remains `AttachmentPreparationError` before claim. Keep `_build_selected_files`, collision checks, ZIP creation, command normalization, manifest, and cleanup ownership in Python.
6. Make caller syntax location-independent: accept the logical executable token `oracle` (and, if retained for compatibility, only an explicit path resolving to the already selected entry), then replace it with the validated `[node, entry]` process prefix internally. Remove `CANONICAL_ORACLE_CLI` and the production `ORACLE_BROWSER_SLOTS_ORACLE_CLI` bypass. Tests use an injected `ResolvedOracleRuntime`/resolver seam; production never treats an unproved test path as compatible.
7. The compatibility check includes the file-selection capability even for file-free `run`/`submit`, so a missing required component cannot survive until a later file-bearing request. Capability checking is cached only for the lifetime of the current wrapper process; every new public invocation re-resolves current files and PATH.
8. Preserve `prepare` and `status` as slot/Chrome state operations that do not create a child or ZIP. Their alternate-prefix smoke proves they contain no personal-path dependency. `run`, `submit`, and any existing path that creates `JobRunner` receive the same resolved runtime and fail closed before child start. Do not broaden this Scope into later-Block timeout, recovery, or CI policy.
9. Extend the packed/installed smoke so the actual staged Oracle artifact and staged Python wrapper run from another absolute prefix and HOME. Read back package name/version, CLI realpath/SHA-256, selector protocol, and selected files from that exact installed target. Source import or a source-only test is supporting evidence, not Block Exit evidence.

### UNRESOLVED

1. **Transition approval authority:** the bound `BASELINE-001.md` says `Status: DRAFT`, `Approved by: Pending`, `Approval scope: None`, and explicitly states that it grants no implementation authority. Its hash proves the bytes only. Therefore this Plan may be written and reviewed, but no product edit, artifact promotion, or Block execution is permitted until the caller supplies an approved transition authority or otherwise resolves the Scope's binding under the owning IIS authority. Smallest observation: direct readback of the exact approved baseline path/revision and its approval/continuation fields. Next owner: preparation lead / Scope-transition authority owner.
2. **Installed wrapper/product co-location:** current source layout supports product-root-relative resolution, while `pyproject.toml` packages only `oracle_browser_slots*` and the npm tarball ships `dist/**/*`; no current installed combined-unit readback was supplied. The first staging experiment must prove where the installed wrapper derives its product root and how a PATH Oracle candidate is tied to it. Until then, do not claim wheel/npm independent installation closure. If separate artifacts cannot share an attributable release identity without a new packaging contract, return the affected method to the Planner rather than accepting version equality alone.
3. **Exact selector protocol name and command spelling** are local implementation discretion only if they remain documented, non-submitting, package-owned, schema-versioned, and callable from the exact resolved CLI. A need to expose private file paths or to select through a different installation is a material refutation, not naming discretion.

## 3. Entry/read paths, owners, and lifetimes

### Entry and deciding paths

1. `oracle_browser_slots.cli.main()` parses `prepare`, `status`, `run`, `submit`, or `followup`.
2. `prepare`/`status` remain owned by `SlotService`; they do not resolve or launch Oracle merely to report local slot state.
3. `run` constructs `JobRunner`; `submit` constructs `AutoAllocator -> JobRunner`; existing followup construction also routes through `JobRunner`. Construction resolves and validates one runtime identity before command normalization.
4. `_validated_oracle_command` is the deciding reader for logical child identity and transport flags. It consumes `ResolvedOracleRuntime`, rejects a different executable, and produces the exact `[node, oracle-entry, arguments...]` child command.
5. `FileAttachmentPolicy.prepare` is the deciding reader for file intent. For file-bearing requests only, its selector calls the resolved CLI's stable file-selection command, validates the returned runtime identity, and hands selected paths to existing ZIP normalization. For file-free requests it returns `None` and writes nothing.
6. `execute_claimed` remains the only external child process boundary. The runtime check and file preparation have already completed before this boundary. Existing CDP/login pre-submit checks and slot ownership remain preserved; this Plan does not redefine them.

### Writers/readers and identity

- **Node/package metadata writers:** repository/package build owns `package.json`, compiled `dist`, and CLI version. The resolver is read-only.
- **Runtime identity reader:** the new resolver reads PATH, candidate realpath, owning `package.json`, Node version, CLI version/capability output, and entry bytes. It writes no durable product state. Its identity tuple is at least `{package_root_realpath, package_name, package_version, oracle_entry_realpath, oracle_entry_sha256, node_realpath, node_version, selector_protocol}`.
- **Selector:** the same Oracle entry is both the capability/selection reader and the later Browser CLI entry. Static package-relative imports keep selector and Browser implementation in one Node package root. No Python code names `dist/src/oracle/files.js` or `dist/src/cli/options.js`.
- **Attachment writer:** `FileAttachmentPolicy` writes one request-owned temporary directory/ZIP and later the existing session manifest. Its selected file list and relative paths are authoritative for ZIP content; CLI capability output is authoritative for runtime/selector identity.
- **External effect owner:** only the later Browser child can submit remotely. Resolver and selector commands are explicitly non-submitting. Runtime/selection failures must leave `child_started == false`; no remote readback is needed because no remote effect was attempted.

### Lifetime, interruption, and resumption

- A resolved runtime is immutable within one wrapper process/request. A new invocation re-resolves; no cross-process cache or persisted “last good” path is used.
- Selection reads current filesystem state. ZIP construction verifies file sizes as it writes. If inputs change, selection fails, ZIP creation fails, or interruption occurs, existing cleanup removes the request-owned temporary directory and no slot is claimed.
- A failure after child start retains the existing distinction between possible submission, manifest failure, and cleanup failure. This Scope must not reinterpret it or retry automatically.
- A changed PATH/package between separate invocations causes a fresh decision. A changed component during one invocation must fail on missing/readback mismatch rather than continue with a second candidate.
- Duplicate/late selector output is not state: one subprocess request accepts one schema-valid JSON response tied to the current runtime identity. There is no retry against another installation.

## 4. Implementation sequence (HA-01 atomic cut)

1. **Establish the stable Node boundary first.** In `bin/oracle-cli.ts` and a focused package-owned helper if needed, register the non-submitting runtime/file-selection command. Reuse the current TypeScript merge/dedupe/readFiles functions through static imports. Define one JSON request/response schema and capability action. Include package name/version in all success responses; errors return non-zero with structured reason and never fall through to prompt execution.
2. **Prove selector equivalence before removing the old path.** Run the fixture matrix in Conditional Bundle C2 against both the current selector and the new stable command. Compare exact selected relative paths and failures. This comparison is migration evidence only; the old private import is not final acceptance evidence.
3. **Introduce the single Python resolver.** Add the immutable runtime value and resolver with project-relative then PATH candidate ordering, strict package/bin ownership checks, Node `>=24`, CLI/package version check, capability/protocol check, and CLI fingerprint. Do not add a personal fallback, generic global package-layout search, or “best effort” warning mode.
4. **Cut runner command ownership over.** Inject the resolved runtime into `JobRunner`; update `cli.py`, `allocator.py`, and `followup.py` construction as needed so all child-producing paths share it. Normalize logical `oracle` to the validated Node+entry prefix. Remove `CANONICAL_ORACLE_CLI`, production use of `ORACLE_BROWSER_SLOTS_ORACLE_CLI`, and diagnostics instructing users to paste a canonical personal path.
5. **Cut attachment selection over in the same runnable cut.** Pass the same runtime into `FileAttachmentPolicy`; replace the dynamic JavaScript/import-path script with the stable CLI call and identity/schema validation. Remove `attachments.py`'s independent constant, Node sibling inference, and all private `dist/src/...` knowledge. Do not leave a fallback to the legacy selector.
6. **Preserve single-ZIP semantics.** Keep `_extract_file_arguments`, `_build_selected_files`, `normalize_zip_member_path`, `_create_compressed_zip`, `_normalize_file_command`, `PreparedAttachment` manifest/cleanup, and their failure ordering unless a parity defect requires a narrowly grounded correction. No original-file multi-upload fallback and no empty ZIP.
7. **Update focused behavioral tests and operator documentation.** Replace personal-path constants and test-only production environment override with logical `oracle` plus an injected validated-runtime seam. Document project-relative/PATH resolution, Node/release/protocol rejection diagnostics, and the stable selector command. Remove README claims that selection remains tied to a canonical NVM install.
8. **Build and stage the actual artifact.** Build the Node package once the source is final; install/package the wrapper using its existing packaging path; stage both at another absolute prefix/HOME without `/home/user01` or NVM in PATH. Record artifact hashes and resolved identity. If the existing packaging cannot form the claimed release unit, stop at the unresolved packaging boundary; do not substitute source checkout success.
9. **Run non-submitting smoke and handoff.** Exercise installed `status`, an authorized local `prepare --slot N`, file-free `run --dry-run`, and file-bearing `run --dry-run` on the same staged target. Inspect resolver identity, selector response, one ZIP/manifest readback, cleanup, exit codes, and absence of a new remote prompt. The final verifier, not the implementer, decides the Scope Acceptance result.

No intermediate runnable candidate may combine the new resolver with the old private selector, or the new selector with the personal CLI. Development commits may be smaller, but promotion, smoke, and verifier handoff occur only after both sides of `HA-01` are closed.

## 5. Failure and diagnostic contract

Before ZIP creation, claim, or child launch, return exit code `2` (or the existing typed precondition rejection code) with the failed fact and corrective action for each of:

- neither product-relative nor PATH `oracle` exists;
- candidate realpath cannot be attributed to one `@steipete/oracle` package root or its `bin.oracle` does not name that entry;
- Node is absent, unparseable, or major version is below 24;
- CLI `--version` differs from owning package metadata or the release is outside the wrapper's explicit compatibility table;
- capability command is absent, non-zero, malformed, wrong schema/protocol, or reports a different package identity;
- selection fails, returns malformed/non-string paths, or changes identity relative to preflight;
- selection is empty for a file-bearing request, member paths collide after normalization, or ZIP creation/readback fails.

Diagnostics may include resolved non-secret paths, versions, protocol, and hashes. They must not suggest installing under `/home/user01`, selecting another unproved global package, setting a bypass environment variable, or retrying after possible remote submission. A capability or dry-run success is not evidence of a remote Browser result.

## 6. Implementer self-check and discriminating readbacks

The implementer runs focused checks only; project-wide format/lint/build/test belongs to the integration owner.

1. **Static removal/read-path check**
   ```bash
   cd /home/user01/project/oracle
   grep -R -n -E '/home/user01/|CANONICAL_ORACLE_CLI|dist/src/oracle/files\.js|dist/src/cli/options\.js' \
     oracle-browser-slots/oracle_browser_slots oracle-browser-slots/bin oracle-browser-slots/README.md
   ```
   Expected: no production/runtime/documentation dependency. Test fixture text is allowed only when asserting rejection and must not be executed as fallback.
2. **Focused Python behavior**
   ```bash
   cd /home/user01/project/oracle/oracle-browser-slots
   python3 -m pytest tests/test_slots.py -k 'runtime_resolution or runtime_precondition or stock_selection or one_and_many_files or normalized_member_collision or sessionless_dry_run'
   ```
   Required observations: project-relative and PATH resolution converge on the attributed entry; mismatched package/bin/version/protocol and Node 23 reject before claim/Popen; Node 24 passes; file-free produces no ZIP; directory/glob/exclusion/dedupe/ignore fixtures select the expected paths; file-bearing output contains one deflated ZIP with preserved relative names.
3. **Focused Node selector checks**
   ```bash
   cd /home/user01/project/oracle
   pnpm vitest run tests/cli/runtimeFileSelection.test.ts
   ```
   Required observations: capability and selection output one schema-valid JSON document; package identity equals `package.json`; selection reuses current merge/dedupe/readFiles behavior; malformed input and no-match exit non-zero; no Browser/session/prompt path is entered.
4. **Actual build and identity readback**
   ```bash
   cd /home/user01/project/oracle
   pnpm run build
   node dist/bin/oracle-cli.js --version
   node dist/bin/oracle-cli.js runtime file-selection --capability --json
   sha256sum package.json dist/bin/oracle-cli.js
   ```
   Expected: Node/package/CLI version and protocol agree, and the fingerprint recorded for smoke is the exact built entry later executed. A build success alone is insufficient.
5. **Alternate-prefix staged smoke**
   - Install the built Node artifact and Python wrapper into a disposable prefix not beneath `/home/user01`; set a disposable `HOME`; construct PATH only from that prefix plus declared system tools, with no NVM directory, source checkout, or compatibility symlink.
   - Run `oracle-browser-slots status`, then `prepare --slot N` only on an operator-authorized spare local slot, then wrapper `run --slot N ... -- oracle --dry-run json` once without files and once with a fixture directory/glob/exclusion set.
   - Read back the resolved Node/Oracle realpaths, package name/version, CLI SHA-256, selector protocol, selected relative paths, ZIP member list/count, child exit, ZIP cleanup, and slot state. Confirm exactly one ZIP for the file-bearing run and no ZIP for the file-free run.
   - Compare the remote conversation/user-turn count before and after; it must not increase. Dry-run output or exit 0 alone does not establish this no-submit boundary.
6. **Controlled fail-closed smoke**
   - Repeat resolution with PATH missing Node, a Node 23 fixture, a wrong `oracle`, an owning-package version mismatch, and a selector-protocol mismatch.
   - For each, assert non-zero rejection plus specific diagnostics and read back: no ZIP/temp residue, no slot claim/queue assignment caused by the command, `child_started == false`, and unchanged remote prompt count.
7. **Verifier handoff**
   Hand off exact Scope/Thesis/transition hashes; source revision; staged package/tarball/wrapper identities; resolved runtime tuple; focused check outputs; alternate-prefix commands; ZIP member/readback; failure cases; and any remaining packaging/authority limit. Do not label Block 1 or the transformation complete from self-checks.

Mocks/fakes may isolate unrelated slot/CDP behavior in focused unit tests, but they cannot prove Node/release resolution, the selector boundary, installed alternate-prefix behavior, ZIP contents, or no-submit readback. Those boundaries use the actual built/staged components.

## 7. Conditional first-work bundles

### C0 — Transition authority gate

- `plan_anchor`: `PLAN-001 §2 UNRESOLVED item 1`
- `permitted_initial_work`: Read-only inspection of the exact transition authority and any superseding approved revision supplied by the caller; Plan review may proceed.
- `discriminating_observation`: An exact project-local baseline/revision directly states approval scope covering `B1-RUNTIME-CLOSURE`, or the owning authority explicitly resolves why this ready Scope may execute despite the bound source's `DRAFT/Pending/None` fields.
- `dependent_work_not_yet_permitted`: All product/test edits, builds intended as release candidates, staging promotion, and local Browser/slot effects.
- `response_if_refuted`: Stop implementation; preserve this Plan as useful method evidence and return the authority conflict to the preparation lead / Scope-transition authority owner. Do not edit Thesis or Scope to manufacture approval.

### C1 — Resolvable installed release unit

- `plan_anchor`: `PLAN-001 §2 PROPOSED items 1-3 and §4 steps 3-4`
- `permitted_initial_work`: After C0 is satisfied and Plan is independently admitted, implement the read-only resolver/capability probe and run it against the current project-relative entry, current PATH symlink, and a disposable alternate prefix; do not switch production callers yet.
- `discriminating_observation`: All accepted candidates resolve to an owning `@steipete/oracle` package whose `bin.oracle` names the exact entry; Node is `>=24`; CLI/package versions agree; capability identity/protocol agrees; the resolver emits one artifact fingerprint. A candidate from another package/root is rejected.
- `dependent_work_not_yet_permitted`: Removal of old runner/selector paths, production caller cutover, and claims that independently installed Python/npm artifacts form one release unit.
- `response_if_refuted`: Stop the resolver cutover and return to the Plan owner. Choose a new explicit packaging/provenance method within the same Scope only after fresh review; do not relax to version-only identity, a personal fallback, or global-layout search.

### C2 — Stable selector parity

- `plan_anchor`: `PLAN-001 §2 PROPOSED items 4-5 and §4 steps 1-2`
- `permitted_initial_work`: Add the non-submitting Node selector protocol and compare it with the current selector on disposable fixtures covering ordered aliases, comma inputs, duplicate literals/patterns, literal file/directory, `*`/`**`, exclusions, nested `.gitignore`, default ignored directories, explicit ignored-directory request, hidden-file opt-in, missing path, empty selection, and paths outside cwd. No Browser run or prompt submission.
- `discriminating_observation`: Both selectors return the same ordered selected relative paths or the same failure class for every fixture; protocol output reports the same package identity as the selected CLI and produces no session/prompt artifact.
- `dependent_work_not_yet_permitted`: Deleting the old selector, changing Python attachment selection, or claiming preservation of existing file intent.
- `response_if_refuted`: Keep the old production path only as unmodified evidence, stop dependent mutation, and return the semantic mismatch to the Plan owner. If the desired semantics themselves must change, return to Scope/Thesis ownership rather than choosing the easier output.

### C3 — HA-01 cutover and pre-submission failure ordering

- `plan_anchor`: `PLAN-001 §4 steps 3-7 and §5`
- `permitted_initial_work`: After C1/C2 support, perform the resolver plus selector cutover in one source target and run focused real-component tests. Keep any intermediate commit non-promotable.
- `discriminating_observation`: `run` and `submit` with supported runtime reach the intended child command; each manipulated missing/mismatched precondition rejects before ZIP/claim/Popen; file-bearing input creates one ZIP and file-free input creates none; source/runtime searches find no personal path or private-module import.
- `dependent_work_not_yet_permitted`: Staged artifact promotion, verifier handoff, Block Exit claim, or work on Block 2.
- `response_if_refuted`: Stop promotion, preserve resolved identity and failure evidence, remove no safety gate, and return changed ownership/interface/failure ordering to the Plan owner for revision and fresh independent review.

### C4 — Alternate-prefix installed readback

- `plan_anchor`: `PLAN-001 §4 steps 8-9 and §6 items 4-7`
- `permitted_initial_work`: Stage the exact built Node artifact and wrapper at a disposable alternate prefix/HOME; run capability, status/authorized prepare, and file-free/file-bearing dry-runs only. No live prompt submission.
- `discriminating_observation`: Actual installed paths are outside the personal NVM/source location; resolver/selector/browser entry share the recorded release identity; the expected selected set becomes one ZIP; no-file produces no ZIP; mismatch cases fail before child; remote prompt count is unchanged.
- `dependent_work_not_yet_permitted`: Scope verification verdict, Block 1 Exit/continuation claim, production/registry deployment, live Browser E2E, or any later Block.
- `response_if_refuted`: Stop use/promotion of the candidate, retain artifact/runtime/ZIP/slot evidence, classify any unexpected remote effect before cleanup, and return packaging/provenance defects to the Plan owner. Product-meaning differences return to Scope/Thesis ownership.

## 8. Local discretion and return-to-review conditions

Implementers may choose private class/function names, exact diagnostic wording, JSON field ordering, and an equivalent single selector command spelling. They may refactor focused test helpers and retain constructor injection if it cannot bypass production validation. Do not add a generic plugin system, runtime registry, telemetry layer, daemon, persistent cache, fallback chain, or new package manager.

Stop affected work and obtain a revised Plan plus fresh independent review if any of these changes: runtime/selector ownership, accepted release identity, selector protocol compatibility, package co-location strategy, pre-submit ordering, file-selection semantics, ZIP cardinality/path meaning, or the authoritative installed readback. Return to Scope shaping if the current observable result or Non-Goals must change. Return to Thesis ownership if supported-environment, failure, or product-meaning policy must change.

The independent Plan Reviewer owns `ADMIT/REVISE/EVIDENCE_NEEDED`. This Plan's existence and hash do not admit implementation, verify Acceptance, mark the Scope done, authorize deployment, or authorize Block 2.