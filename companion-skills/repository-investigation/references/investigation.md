# Repository Investigation Workflow

## 1. Invocation and objective

Bind the exact current user instruction and establish:

```text
Project Root:
Repository Root:
Investigation Objective:
Focus Target:
Decision Context:
Explicit Exclusions:
Execution Mode: DIRECT | SUBAGENT
Runtime Inspection Authority: read-only | <exact separately authorized effect>
Durable Artifact: yes | no
```

The Investigation Objective must be narrow enough that new evidence can change the answer. It may be broad enough to cross several repository areas when those areas jointly determine the same decision-relevant behavior.

Do not transform a planning or implementation recommendation into the investigation objective. Examples:

```text
Good:
Determine what this wrapper actually owns versus forwards, where current state is owned,
which readback is authoritative, and what alternate entry paths can bypass it.

Bad:
Prove that the wrapper should be replaced with architecture X.
```

If a supplied Project Root is missing/unreadable/wrong-target, return `BLOCKED`; do not silently inspect a parent or sibling repository and treat it as evidence for the requested target.

## 2. Repository binding

Before durable artifact writing, establish the observed repository state:

```text
Project Root:
Repository Root:
Git Branch:
Git HEAD:
Working Tree Before Artifact: clean | dirty
Relevant Modified Paths: None | <paths>
Relevant Untracked Paths: None | <paths>
Observed At: <offset-aware timestamp>
```

The Project Root is the product/planning root. The Repository Root is the Git root whose branch/HEAD/working tree binds source evidence. They may differ in a monorepo.

A dirty tree is not a failure. Record relevant changed paths because they are part of the current investigated target. The investigation artifact itself must not be counted as a pre-existing dirty path.

Do not create a repository-wide checksum/fingerprint layer or a separate persistent investigation controller. Use executor-owned fixed refs only when a durable handoff actually needs one.

## 3. Bounded reconnaissance

Lead first inspects only enough current primary evidence to map the connected surface:

- target project type and actual entrypoints;
- the named component/feature/wrapper and directly connected core dependencies;
- product/operator trigger surfaces;
- state/configuration/persistence/lifecycle sources likely relevant to the objective;
- current tests and documentation for those surfaces;
- observable/canonical readback surfaces; and
- plausible alternate registration, legacy, fallback, or bypass areas.

Reconnaissance is not the final investigation. Its purpose is to construct the smallest material frontier rather than spray workers across arbitrary directories.

## 4. Investigation frontier

Classify the four required concerns exactly once:

```text
Repository Investigation Frontier Entry

Area: FLOW_AND_READBACK | STATE_AND_AUTHORITY | ALTERNATE_PATHS | EVIDENCE_ALIGNMENT
Question:
Why Material:
Primary Evidence Plan:
Disposition: INVESTIGATE | COVERED_BY_OTHER_LANE | NOT_APPLICABLE
Reason:
```

### `FLOW_AND_READBACK`

Trace enough actual behavior to answer:

```text
entry/trigger -> relevant routing/processing/state transition -> observable result -> authoritative readback
```

Do not stop at a wrapper call or helper merely because it looks central. Establish whether the component owns, transforms, delegates, caches, or only forwards the material behavior.

### `STATE_AND_AUTHORITY`

Locate the current owners that can materially affect the answer:

- persistent data/state owner;
- lifecycle owner;
- configuration/precedence owner;
- public/external/persisted identity owner;
- canonical source of truth; and
- readback owner when different from mutation/processing ownership.

Avoid converting a current internal mechanism into a product requirement. This lane establishes facts, not future design.

### `ALTERNATE_PATHS`

Challenge the first model with the most plausible falsifying path. Depending on the repository, inspect one or more of:

- direct entrypoint bypassing the named wrapper;
- fallback or legacy implementation;
- plugin/dynamic registration;
- environment-specific routing/configuration;
- alternate API/CLI/UI/modality path;
- background/async path;
- compatibility shim; or
- adjacent owner that can produce the same observable result.

The goal is not exhaustive negative testing. Stop when the material counterpath question is decided or bounded.

### `EVIDENCE_ALIGNMENT`

Compare the decision-relevant current sources that claim to describe the same behavior:

- source/configuration;
- tests and their actual assertions;
- documentation/contracts;
- generated artifacts when authoritative; and
- authorized runtime/canonical readback when current behavior is load-bearing.

Record a contradiction when they disagree materially. Do not choose the most convenient source merely to create a single narrative.

Select operational/history sources only when they could change the current answer: Git history, issue/ticket, ADR, incident record, logs, observability, error tracking, analytics or relevant conversation records within current read access. For a guard introduced after an incident, compare the historical failure and rationale with current code/runtime constraints; evidence that a past decision existed does not establish its present validity or a permanent product requirement. Reuse the existing anchors and `FACT`/`INFERENCE`/`UNKNOWN` distinction to record source, query scope, observation/retrieval time, contradictions and limits. No new connector, evidence kind or obligatory source matrix is needed; skip sources irrelevant to the objective.

## 5. Evidence anchors

Every load-bearing fact references one or more named anchors. Use compact anchor records:

```text
A1 | SOURCE | <project/repo-relative path> | <line/symbol> | <fixed snapshot ref or native Git identity> | ANCHOR_LOCAL
A2 | SEARCH | <bounded search universe> | <query/method> | <Git identity> | SEARCH_UNIVERSE
A3 | TEST | <path::test> | <assertion/observation> | <fixed snapshot ref or native Git identity> | ANCHOR_LOCAL
A4 | RUNTIME | <read-only command/inspection> | <environment + readback> | <target identity> | RUNTIME_STATE
A5 | DOC | <path/section or external source> | <version/retrieval> | <identity> | EXTERNAL_VERSION
```

Supported freshness sensitivity values:

- `ANCHOR_LOCAL` — positive fact depends on specific file/symbol/config anchors.
- `SEARCH_UNIVERSE` — absence or alternate-path claim depends on a bounded set of entry/config/export/registration surfaces.
- `RUNTIME_STATE` — fact depends on current environment/runtime/canonical state.
- `EXTERNAL_VERSION` — fact depends on an external/document version or retrieval date.

Do not treat the investigation artifact itself as the authoritative readback for a product claim.

## 6. Fact, inference, unknown

### Fact

A `FACT` is directly supported by current inspectable evidence.

Record:

```text
Finding:
Statement:
Primary Evidence: <anchor ids>
Counterevidence Checked:
Boundary / Limitation:
Planning Relevance Candidate:
Freshness Sensitivity:
```

Allowed planning-relevance candidates:

```text
CURRENT_STATE
PLANNING_CONSTRAINT_CANDIDATE
PRODUCT_DEPENDENCY_CANDIDATE
ACCEPTANCE_SURFACE_CANDIDATE
DELIVERY_CONTEXT
NONE
```

These labels are navigation hints for a later owner. They are not IIS authority.

### Inference

An inference must cite supporting Finding numbers and one plausible alternative:

```text
Inference:
Statement:
Supported By:
Plausible Alternative:
Evidence Needed To Disprove:
Planning Relevance Candidate:
```

Do not promote an inference to Fact because multiple workers repeat it.

### Unknown

Keep a material gap explicit:

```text
Unknown:
Impact: DECISIVE | NON_DECISIVE
Why unresolved:
Smallest evidence action that could close it:
```

A `DECISIVE` unknown prevents `COMPLETE`.

## 7. Absence claims

Never write a global absence claim from an unspecified search.

Every material absence claim states:

```text
Claim:
Search Universe:
Method:
Result:
Boundary:
```

The result should normally be phrased as `not found within <bounded universe>` rather than `does not exist` unless the repository/runtime has an authoritative complete registry whose current state decides global absence.

## 8. SUBAGENT execution

Use SUBAGENT only from explicit current user selection.

Create workers only for frontier questions that materially benefit from separate context and can be investigated independently. There is no required number of workers. If the user explicitly asks for three parallel models, create at most three useful independent lanes; do not duplicate the same question solely to fill all slots.

Each assignment contains:

```text
REPOSITORY INVESTIGATION WORKER ASSIGNMENT

Project Root:
Repository Root:
Investigation Objective:
Lane Area:
Lane Question:
Why Material:
Allowed Evidence:
Required Source Anchors:
Explicit Exclusions:
Preferred Conclusion: None
Other Worker Findings: Not supplied
Delegated Investigator: yes
```

Workers remain read-only and do not write the durable artifact.

Worker result:

```text
REPOSITORY INVESTIGATION WORKER RESULT

Actual Project Root:
Actual Repository Root:
Lane Area:
Question:
Inspected Scope:
Observed Facts:
Inferences:
Counterevidence And Boundary Conditions:
Absence Search Boundaries:
Material Unknowns:
Evidence Anchors:
Worker Completion: COMPLETE | PARTIAL | BLOCKED
```

### Fan-in

Lead validates actual roots and assigned lane before using a worker result. A result from another root is not partial evidence for the requested repository.

Lead then:

1. directly reopens every anchor that will be load-bearing in the final answer/handoff;
2. preserves attributable contradictions and counterexamples;
3. merges duplicate facts without counting agreement as confidence;
4. reclassifies worker prose into final Fact/Inference/Unknown categories;
5. resolves or preserves worker disagreement from primary evidence rather than voting; and
6. performs a final counterpath challenge against the integrated model.

One bounded follow-up is allowed when it closes a specific material evidence gap. Do not create debate rounds, confidence polling, or a standing research roster.

## 9. Coverage and completion

Before `COMPLETE`, answer:

```text
Inspected:
Not Inspected:
Why Current Coverage Is Sufficient:
Decision-Critical Unknowns: None
```

Coverage is sufficient when additional inspection outside the stated boundary has no concrete plausible path to change the investigation answer or the later decision context. This is a materiality judgment, not an exhaustive-file-count threshold.

Completion meanings:

- `COMPLETE`: every material frontier concern is closed/bounded, load-bearing anchors are attributable/current enough for handoff, deliberate counterpath challenge completed, and no DECISIVE unknown remains.
- `PARTIAL`: useful evidence exists but one or more DECISIVE unknowns remain or a material lane could not close.
- `BLOCKED`: correct target, read access, required current readback, or safe attribution cannot be established.

## 10. Durable artifact procedure

When a durable artifact is required:

1. capture Git/working-tree binding **before** artifact creation;
2. choose one lowercase kebab-case investigation slug describing the question, not an implementation solution;
3. run `tools/prepare_investigation_workspace.py --project-root <root> --investigation-slug <slug>`;
4. use only its returned `artifactPath`;
5. write the complete artifact from the template;
6. never modify an earlier `INV-NNN.md` to make history look current;
7. run `tools/validate_investigation.py <artifactPath>` and require exact `VALID`;
8. if validation fails, correct only the current artifact's serialization/evidence-contract defect; if the defect reveals missing evidence, return to the exact investigation lane instead of fabricating content.

A later fresh investigation produces the next `INV-NNN.md`. Do not create `LATEST.md`, a mutable current pointer, an evidence database, or an investigation workflow ledger.

## 11. Terminal result

Return exactly one terminal result:

```text
REPOSITORY INVESTIGATION RESULT

Project Root:
Repository Root:
Investigation Objective:
Execution Mode: DIRECT | SUBAGENT
Repository Binding:
Investigation Frontier:
Investigation Answer:
Observed Current Product State:
Material Facts:
Material Inferences:
Contradictions / Surprises:
Material Unknowns:
Coverage Boundary:
Durable Artifact: None | <absolute path>
Artifact Validation: NOT_APPLICABLE | VALID
Investigation Completion: COMPLETE | PARTIAL | BLOCKED
```

Do not automatically invoke IIS/Adaptive, implementation, remediation, review, or verification after this result.
