# Offline Log Trimming Design

## Summary

This project builds a small offline log trimming utility that reads `input.txt` from the project root and writes a compressed, human-readable summary to `output.txt`.

The tool is designed for Windows execution inside a `venv`, uses only the Python standard library for the core path, and focuses on conservative compression of noisy infrastructure output.

Its primary job is not to “understand everything.” Its job is to reduce repeated noise while preserving the distinct events that matter.

The supported input families are:

- Linux event logs
- Kubernetes pod logs
- Pod-internal application logs
- Kubernetes component logs
- `kubectl get` style snapshot output
- `kubectl describe` style structured text

The main output form is a grouped block that looks like `pattern + sample + count`, with optional metadata such as first and last occurrence positions.

## Goals

- Read `input.txt` and produce `output.txt` in the same project folder.
- Run on Windows inside `venv` without requiring external LLM access.
- Use standard library only for the MVP.
- Group repeated log events by normalized pattern.
- Keep false merges low, even if that leaves some duplicates unmerged.
- Handle multiline logs, stack traces, and wrapped journal output.
- Handle JSON logs through structured parsing when possible.
- Treat `kubectl get`, `kubectl describe`, and event-stream logs as different source families.
- Produce output that a human can scan quickly and trust.

## Non-Goals

- Do not build a semantic log search engine.
- Do not try to infer full incident root cause.
- Do not perform fuzzy clustering across all lines by default.
- Do not require external services, embeddings, or LLM calls.
- Do not normalize away important semantic differences just to maximize compression.
- Do not turn `kubectl describe` output into ordinary line-by-line logs.

## Operating Assumptions

- The user places raw text into `input.txt`.
- The raw text may contain a mix of sources from the same capture session.
- The tool may need to process large files, so streaming behavior matters.
- The safest default is to under-merge rather than over-merge.
- Determinism matters: the same input should produce the same output.

## Source Families

The tool must recognize four broad source families.

### 1. Event Stream Logs

This includes:

- Linux syslog-like logs
- `journalctl` output
- Kubernetes component logs
- pod-internal application logs

These are the primary targets for `pattern + sample + count` compression.

### 2. JSON Logs

These are event logs encoded as JSON objects on one line or across wrapped lines.

The tool should parse them structurally when possible and build a grouping key from stable fields instead of raw string order.

### 3. Snapshot Output

This includes `kubectl get pod`, `kubectl get node`, and similar tabular output.

This family is not compressed like normal event logs. It is summarized as a grouped state snapshot.

### 4. Structured Descriptions

This includes `kubectl describe pod`, `kubectl describe node`, and similar sectioned text.

This family is summarized by section rather than by event similarity.

## Processing Pipeline

The tool uses a four-stage pipeline.

### Stage 1: Eventization

The input is first split into logical records.

For event streams, this means the tool must join continuation lines into the original event before any grouping logic runs.

This stage should recognize:

- timestamp-prefixed starts
- severity-prefixed starts
- JSON object starts
- known Kubernetes and journal prefixes
- continuation lines from stack traces or wrapped text

For snapshot and describe output, the logical record is usually a line or section boundary rather than a log event.

### Stage 2: Source Classification

Each logical record is assigned to a source family.

Classification should be conservative:

- if the tool is confident, use the specific family
- if not, fall back to generic text handling
- never force unrelated source families into one bucket just to increase compression

The classifier should prefer stability over cleverness.

### Stage 3: Normalization

Each record is normalized into a canonical grouping key.

Normalization should replace only high-confidence variable fields, such as:

- timestamps
- PIDs and TIDs
- UUIDs
- hashes
- IPs
- ports
- memory addresses
- long numeric IDs
- obvious pod suffixes and replica hashes

For JSON logs, normalization should happen on parsed fields, not on raw serialized text when parsing succeeds.

For event streams, normalization should preserve the core message text and component identity while stripping obvious variable values.

### Stage 4: Grouping and Rendering

The normalized key is used as the primary grouping key.

Groups are emitted in descending count order, with optional secondary ordering by source family or severity if that improves readability.

The rendered output should show:

- canonical pattern
- total count
- representative sample
- optional alternate sample
- optional metadata such as first seen and last seen

## Source-Specific Behavior

### Event Stream Behavior

For Linux, journal, pod-internal, and component logs:

- join continuation lines before grouping
- normalize high-variance tokens
- group by exact normalized key
- keep representative samples instead of every raw example

This is the main compression path.

### JSON Behavior

For JSON logs:

- attempt `json.loads`
- if parsing succeeds, derive the grouping key from stable fields
- ignore incidental field order
- ignore request IDs, trace IDs, timestamps, and similar noise fields unless they are required to distinguish the message
- fall back to text-mode normalization if JSON parsing fails

### Snapshot Behavior

For `kubectl get` style output:

- classify by workload family when possible
- group by state signature, not just by raw line text
- keep differences in readiness, status, restarts, and node assignment visible
- summarize repeated pods from the same deployment as sibling entries under one parent group

This means pods from the same deployment may be grouped together, but only if their state signature is still distinguishable inside the summary.

### Describe Behavior

For `kubectl describe` style output:

- summarize by section
- preserve important subsections such as `Conditions`, `Events`, `Labels`, and `Annotations`
- do not flatten the document into ordinary log lines

## Output Contract

The output file must be readable without additional tooling.

The preferred block format is:

```text
[count] canonical pattern
sample: ...
sample: ...
first_seen: ...
last_seen: ...
```

For snapshot and describe families, the block format should adapt to the family instead of forcing them into the event log template.

The output must remain deterministic and stable for the same input.

The output should be written only after successful processing.

If the input file is missing, the tool should fail clearly and avoid creating a misleading partial output.

## Guardrails

- Prefer under-merging to over-merging.
- Keep grouping rules explainable.
- Keep source-family boundaries intact.
- Make multiline reconstruction happen before grouping.
- Keep the MVP standard-library-only.
- Avoid broad fuzzy clustering in the first version.
- Avoid hidden side effects outside `output.txt`.

## Validation Criteria

The design is correct if the following are true:

- event logs compress into `pattern + sample + count` blocks
- multiline logs remain intact as single logical events
- JSON logs group by stable fields when parsing succeeds
- `kubectl get` output is summarized as a snapshot, not as a raw log stream
- `kubectl describe` output is summarized by section
- unrelated sources are not merged just because they share a few tokens
- the same input always yields the same output

## Test Strategy

The implementation must be covered by small fixture-based tests.

### Event Stream Tests

Cover:

- stack traces
- wrapped lines
- timestamp-prefixed records
- repeated event families with different variable tokens

### JSON Tests

Cover:

- stable-key grouping
- field-order independence
- fallback when parsing fails

### Snapshot Tests

Cover:

- repeated pod rows from one deployment
- state differences that must stay visible
- `kubectl get pod` and `kubectl get node` distinctions

### Describe Tests

Cover:

- section preservation
- event list retention
- labels and annotations handling

### Anti-Merge Tests

Cover intentionally different pairs such as:

- timeout vs connection refused
- crash loop vs healthy running state
- permission denied vs disk full

These tests matter because false merges are the main quality risk.

## Risks

- Over-normalization could collapse distinct failures into one bucket.
- Under-normalization could leave too many groups and reduce usefulness.
- Snapshot output could be misread as event logs if source boundaries are weak.
- JSON parsing failures could fragment groups if the fallback path is not conservative.

## Definition of Done

The project is done when:

- `input.txt` can be processed end to end on Windows inside `venv`
- `output.txt` is generated reliably
- the main compression path uses standard library only
- source families remain separated
- tests prove that multiline handling, JSON handling, and anti-merge behavior work as intended

