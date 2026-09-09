---
name: purpose-first-review
description: Apply purpose-first review discipline to proposed changes, review findings, policy or skill edits, audit/security controls, and remediation suggestions. Use when deciding whether a change has a material problem, whether a finding is actionable, or whether added safeguards risk complexity, context bloat, instruction conflict, or drift. Explicitly conclude no problem when no material problem exists; treat the change's intended purpose as a gate before tradeoff analysis.
---

# Purpose-First Review

## First rule: safety and security are not a license for bloat or ignored tradeoffs

A safety, security, audit, or verification label establishes neither necessity
nor effectiveness and does not waive tradeoff analysis. Explain which plausible
failure an added control reduces beyond existing mechanisms, how it does so,
and why that benefit justifies the added complexity, context burden, friction
in normal operation, and maintenance cost.

Comply with applicable mandatory requirements, but do not treat them as
automatic justification for a particular implementation or extra controls.
Do not promote optional measures to mandatory requirements merely by
invoking safety or security.

Compare realistic approaches that meet mandatory requirements and sufficiently
preserve the necessary guarantees. Where additional protection does not justify
the added burden, narrow or replace the approach, or withdraw unnecessary
additions. More rules and reviews are not evidence of more safety.
Do not use this principle to introduce another review stage or standing
reporting obligation.

## Core rule

Review to determine whether a material problem exists, not to manufacture findings. If no material problem exists, conclude **NO PROBLEM** and stop. Do not add speculative caveats merely to make the review look thorough.

## Decision order

Apply these gates in order. Do not collapse them into one weighted cost-benefit judgment.

### 1. Establish the purpose

State the change's intended purpose in concrete terms:

- the failure mode it is meant to prevent or correct;
- the property or guarantee it is meant to preserve;
- the observable condition that would mean the change succeeds.

Judge the real behavior and system effect, not the stated label or good intention alone.

### 2. Establish whether a material problem exists

Treat something as a finding only when there is a concrete, plausible path showing that the current change introduces or materially worsens a problem and that the impact matters to correctness, safety, security, auditability, consistency, operability, or maintainability.

Do not create findings from:

- preference or style differences;
- the existence of a theoretically cleaner design;
- hypothetical failure without a plausible path;
- negligible impact;
- pre-existing problems the change did not materially worsen;
- imperfection by itself.

A better alternative does not make the current change defective.

### 3. Apply the purpose gate

Treat purpose as a pass condition, not as one weighted benefit among many costs.

Ask:

1. Does the change materially achieve its intended purpose?
2. Does the change itself undermine the core guarantee or success condition of that purpose?

If either answer fails, classify the issue as **PURPOSE FAILURE** or **PURPOSE UNDERMINING**. Do not offset that failure with unrelated benefits.

In particular, for audit, security, governance, or verification controls, consider complexity, duplicated instructions, context growth, instruction conflict, compliance instability, false assurance, and drift as purpose-undermining when they materially weaken the protection the change was introduced to provide.

Do not classify every small cost as purpose-undermining. The effect must materially weaken the purpose's core guarantee or success condition.

### 4. Evaluate tradeoffs only after the purpose gate passes

Compare only realistic options that preserve the purpose sufficiently. Include the proposed change, the current state, and practical alternatives when relevant.

Consider benefits and costs together, including:

- protection or correctness gained;
- failure probability and impact;
- implementation and operating complexity;
- context size and instruction interaction;
- drift or compliance risk;
- auditability and observability;
- maintenance burden;
- reversibility and blast radius;
- effects on normal paths.

Do not compare against an imaginary perfect solution. Do not recommend removing the purpose merely to eliminate a minor implementation cost.

## Minimum-sufficient-change rule

When multiple approaches preserve the purpose, prefer the smallest clear mechanism that provides sufficient protection.

Prefer, in order when applicable:

1. existing mechanisms already capable of enforcing the requirement;
2. clarification or consolidation of existing rules;
3. a narrow control at the layer where the failure occurs;
4. enforceable validation, permissions, input constraints, or execution-time controls;
5. broader/global instruction or context expansion only when narrower mechanisms are insufficient.

Do not add duplicate defensive prose, broad exception trees, or extra review rules without a distinct material protection benefit. More rules are not evidence of more safety.

## Review scope

Keep the review tied to the change and its purpose.

Separate:

- problems introduced by the change;
- problems materially worsened by the change;
- pre-existing unrelated problems;
- optional improvements.

Do not turn unrelated refactoring, wording cleanup, policy expansion, or architectural preference into required remediation.

## Finding discipline

For every blocking or required finding, provide:

- concrete trigger or condition;
- causal path from the change to the problem;
- material impact;
- relationship to the change's purpose;
- the smallest reasonable correction direction, if known;
- material tradeoffs introduced by that correction.

Do not require a complete fix design in order to recognize a real defect. Judge the defect and the proposed remedy separately.

Do not split one root cause into multiple findings merely to increase finding count.

## Verdicts

Use one of these outcomes:

### NO PROBLEM

Use when no material defect or purpose failure is established. State it plainly. Do not append speculative concerns that are not findings.

### NO PROBLEM — OPTIONAL IMPROVEMENT

If no material defect or purpose failure is established, conclude **NO PROBLEM** and stop. Use **NO PROBLEM — OPTIONAL IMPROVEMENT** only when the user explicitly requests improvement exploration and evidence shows that a concrete non-blocking improvement has meaningful benefit greater than its added complexity; make clear that it is not required. Otherwise, do not append unsolicited suggestions, including conditional suggestions framed as "if I were to change anything" or "if we had to improve it".

### REQUIRED CHANGE

Use when a concrete material defect exists, the change fails its purpose, materially undermines that purpose, violates a higher-authority invariant, or materially worsens risk versus the current state.

### CANNOT DETERMINE

Use only when information essential to the verdict is genuinely unavailable. State exactly what is missing and why it is necessary. Do not replace missing evidence with hypothetical findings.

## Anti-bloat stop rule

After reaching **NO PROBLEM**, do not continue searching for increasingly remote objections just to produce review content.

Before adding a new safeguard or review clause, ask whether it provides a distinct material protection that existing rules do not already provide. If not, do not add it.

Treat review-rule growth itself as a possible source of context bloat, conflict, and drift. The review discipline must not defeat its own purpose through defensive accumulation.

## Compact review format

Report in this order when useful:

1. Verdict
2. Purpose
3. Material finding(s), if any
4. Purpose-gate result
5. Tradeoffs, only if needed
6. Minimum required action, only if needed

If the verdict is **NO PROBLEM**, keep the report short.
