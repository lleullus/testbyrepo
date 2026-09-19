# <Title> Repository Investigation

Artifact-Type: repository-investigation
Format-Version: 1
Status: complete
Project-Root: <canonical absolute project root>
Repository-Root: <canonical absolute repository root>
Investigation-Slug: <lowercase-kebab-slug>
Investigation-Revision: INV-001
Observed-At: <offset-aware ISO-8601 timestamp>
Git-Branch: <branch or detached>
Git-Head: <commit sha>
Working-Tree-Before-Artifact: clean | dirty
Evidence-Authority: repository evidence only; not IIS planning authority

## Evidence Handoff

### Investigation Answer

Answer: <concise answer to the exact investigation objective>
Based On: <Finding/Inference ordinals>

### Observed Current Product State

- State: <directly observed current product/operator state>
  Supporting Findings: <Finding/Inference ordinals>

### Existing Product Surfaces And Readbacks

- Trigger: <trigger or inspection target>
  Observable surface: <surface>
  Authoritative readback: <actual product/canonical readback>
  Supporting Findings: <Finding/Inference ordinals>

### State And Authority

- Statement: <state/configuration/lifecycle/ownership fact>
  Supporting Findings: <Finding/Inference ordinals>

### Planning Constraint Candidates

- None

### Product Dependency Candidates

- None

### Material Unknowns

- None

### Load-Bearing Anchors

- A1 | SOURCE | <path> | <line/symbol> | <fixed snapshot ref or native Git identity> | ANCHOR_LOCAL

## Investigation Charter

### Original Request

<user request>

### Investigation Objective

<exact bounded question>

### Decision Context

<why the answer matters without importing a desired conclusion>

### Explicit Exclusions

- <excluded surface, or exact None>

## Repository Binding

Relevant Modified Paths:
- None

Relevant Untracked Paths:
- None

Connected Repository Surface:
- <entry/component/state/config/test/runtime/doc surface>

## Investigation Frontier

| Area | Question | Disposition | Result |
| --- | --- | --- | --- |
| FLOW_AND_READBACK | <question> | INVESTIGATE | <bounded result> |
| STATE_AND_AUTHORITY | <question> | INVESTIGATE | <bounded result> |
| ALTERNATE_PATHS | <question> | INVESTIGATE | <bounded result> |
| EVIDENCE_ALIGNMENT | <question> | INVESTIGATE | <bounded result> |

## Current System Model

### Entry And Execution Flow

<current evidence-grounded flow>

### State, Data And Lifecycle Ownership

<current evidence-grounded owners>

### Configuration And Extension Boundaries

<current precedence/registration/extension facts>

### Observable Results And Readbacks

<actual observable/canonical readback surfaces>

## Verified Findings

### Finding 1 — <title>

Classification: FACT
Statement: <directly observed fact>
Primary Evidence: A1
Counterevidence Checked: <counterpath/source checked>
Boundary / Limitation: <bounded limitation or None>
Planning Relevance Candidate: CURRENT_STATE | PLANNING_CONSTRAINT_CANDIDATE | PRODUCT_DEPENDENCY_CANDIDATE | ACCEPTANCE_SURFACE_CANDIDATE | DELIVERY_CONTEXT | NONE
Freshness Sensitivity: ANCHOR_LOCAL | SEARCH_UNIVERSE | RUNTIME_STATE | EXTERNAL_VERSION

## Inferences

None

## Alternate, Legacy And Bypass Paths

- <path checked and result, or exact None>

## Documentation, Tests And Runtime Alignment

- <alignment/contradiction finding, or exact None>

## Absence Claims

None

## Contradictions And Surprises

- <material contradiction/surprise, or exact None>

## Coverage Boundary

Inspected:
- <connected material surface>

Not Inspected:
- <surface, or exact None>

Why Current Coverage Is Sufficient Or Insufficient:
<materiality explanation>

## Completion

Investigation Completion: COMPLETE
Decision-Critical Unknowns: None
