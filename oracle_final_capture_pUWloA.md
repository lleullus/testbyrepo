````md
# Implementation Plan: Log Trimmer CLI

## Target

Build a Python CLI tool:

```bash
python trim.py input.txt output.txt
````

It reads system logs, normalizes variable parts into placeholders, groups similar normalized patterns, counts occurrences, and writes a compressed pattern summary.

---

## Proposed File Structure

```text
.
├── trim.py
├── tests/
│   └── test_trim.py
└── README.md              # optional
```

Keep the first version as a single `trim.py` script with well-separated pure functions so it stays easy to test.

---

## Output Format

Use a simple text output:

```text
# Log Trimmer Output
# input_lines=12000
# exact_patterns=430
# grouped_patterns=92
# compression_ratio=99.23%
# threshold=0.85

COUNT    PATTERN
812      <TIMESTAMP> kubelet[<NUMBER>]: Started container <UUID>
433      pod/<DOMAIN> failed pulling image <PATH>: timeout after <NUMBER>s
91       node <IPV4> disk pressure changed from <WORD> to <WORD>
```

Initial placeholders:

```text
<TIMESTAMP>
<IPV4>
<IPV6>
<UUID>
<MAC>
<PATH>
<DOMAIN>
<NUMBER>
<HEX>
<WORD>
```

For v1, avoid over-normalizing every word. Only normalize high-confidence variable tokens.

---

# Bite-Sized TDD Task Plan

## Phase 1 — Test Harness Setup

### Task 1: Create baseline files

**Time:** 2-3 min
**Files:** `trim.py`, `tests/test_trim.py`

Create empty implementation and a minimal test file.

Expected starter structure in `trim.py`:

```python
def normalize_line(line: str) -> str:
    return line.rstrip("\n")
```

Add one smoke test that imports `normalize_line`.

**Done when:**

```bash
python -m unittest
```

passes.

---

### Task 2: Add CLI skeleton test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Write a failing test that:

1. Creates a temporary input log file.
2. Runs `python trim.py input.txt output.txt` using `subprocess`.
3. Asserts output file exists.
4. Asserts output contains `Log Trimmer Output`.

Use `tempfile.TemporaryDirectory`.

**Expected failure:** CLI does not exist yet.

---

### Task 3: Implement minimal CLI

**Time:** 3-5 min
**Files:** `trim.py`

Use `argparse`.

Required behavior:

```bash
python trim.py input.txt output.txt
```

Implementation can initially just write metadata and raw line count.

Functions to add:

```python
def parse_args(argv=None): ...
def run(input_path: str, output_path: str, threshold: float = 0.85) -> int: ...
def main(argv=None) -> int: ...
```

**Done when:** CLI smoke test passes.

---

## Phase 2 — Normalization

### Task 4: Add IPv4 normalization test

**Time:** 2-4 min
**Files:** `tests/test_trim.py`

Test:

```python
"connection from 10.20.30.40 failed"
```

becomes:

```python
"connection from <IPV4> failed"
```

**Expected failure:** IP not normalized.

---

### Task 5: Implement IPv4 normalization

**Time:** 2-4 min
**Files:** `trim.py`

Add regex replacement for IPv4 before number normalization.

Example regex:

```python
r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
```

Do not validate exact `0-255` range in v1.

---

### Task 6: Add UUID normalization test

**Time:** 2-4 min
**Files:** `tests/test_trim.py`

Test Kubernetes/container-style UUIDs:

```text
pod id 550e8400-e29b-41d4-a716-446655440000 restarted
```

Expected:

```text
pod id <UUID> restarted
```

---

### Task 7: Implement UUID normalization

**Time:** 2-4 min
**Files:** `trim.py`

Add UUID regex before generic hex/number replacement.

```python
r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
```

---

### Task 8: Add MAC address normalization test

**Time:** 2-4 min
**Files:** `tests/test_trim.py`

Input:

```text
device aa:bb:cc:dd:ee:ff disconnected
```

Expected:

```text
device <MAC> disconnected
```

Also test hyphen form if desired:

```text
aa-bb-cc-dd-ee-ff
```

---

### Task 9: Implement MAC normalization

**Time:** 2-4 min
**Files:** `trim.py`

Add regex:

```python
r"\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b"
```

Run before number replacement.

---

### Task 10: Add timestamp normalization tests

**Time:** 4-5 min
**Files:** `tests/test_trim.py`

Cover common log formats:

```text
2026-04-24T10:11:12Z kubelet started
2026-04-24 10:11:12 pod failed
Apr 24 10:11:12 node kubelet[123]: started
```

Expected each timestamp segment to become `<TIMESTAMP>`.

---

### Task 11: Implement timestamp normalization

**Time:** 4-5 min
**Files:** `trim.py`

Use regex-first approach.

Suggested patterns:

```python
ISO_TIMESTAMP = r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?\b"
SYSLOG_TIMESTAMP = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"
DATE_ONLY = r"\b\d{4}-\d{2}-\d{2}\b"
```

Use `python-dateutil` only if needed later. For v1, regex coverage is enough.

---

### Task 12: Add path normalization tests

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Test Linux/K8s paths:

```text
open /var/log/pods/ns_pod_uid/container/0.log failed
```

Expected:

```text
open <PATH> failed
```

Also test image-like paths carefully:

```text
pulling registry.io/team/image:v1
```

This may be handled by domain/path normalization separately.

---

### Task 13: Implement path normalization

**Time:** 3-5 min
**Files:** `trim.py`

Start with absolute Unix paths only:

```python
r"(?<!\S)/(?:[^\s:]+/)*[^\s:]+"
```

Avoid trying to parse every possible URI/path in v1.

---

### Task 14: Add domain normalization tests

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Test:

```text
lookup api.prod.example.com failed
pull image registry.k8s.io/pause:3.9
```

Expected:

```text
lookup <DOMAIN> failed
pull image <DOMAIN>/<WORD>:<NUMBER>    # or similar
```

Be careful: do not replace simple words like `node.local` unless desired.

---

### Task 15: Implement domain normalization

**Time:** 3-5 min
**Files:** `trim.py`

Add a conservative domain regex:

```python
r"\b(?=.{1,253}\b)(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"
```

Run after IP normalization so IPs do not become domains.

---

### Task 16: Add number normalization tests

**Time:** 2-4 min
**Files:** `tests/test_trim.py`

Test:

```text
container exited with code 137 after 300 seconds
```

Expected:

```text
container exited with code <NUMBER> after <NUMBER> seconds
```

Also cover decimals:

```text
latency 12.45 ms
```

Expected:

```text
latency <NUMBER> ms
```

---

### Task 17: Implement number normalization

**Time:** 2-4 min
**Files:** `trim.py`

Add regex:

```python
r"\b\d+(?:\.\d+)?\b"
```

Run this late, after IPs, timestamps, UUIDs, MACs, paths, and domains.

---

### Task 18: Add whitespace cleanup test

**Time:** 2-3 min
**Files:** `tests/test_trim.py`

Test that multiple spaces normalize to one space and leading/trailing whitespace is removed.

Input:

```text
"  pod    failed   with code  1  "
```

Expected:

```text
"pod failed with code <NUMBER>"
```

---

### Task 19: Implement whitespace cleanup

**Time:** 2-3 min
**Files:** `trim.py`

At the end of `normalize_line`:

```python
line = re.sub(r"\s+", " ", line).strip()
```

---

## Phase 3 — Exact Pattern Counting

### Task 20: Add exact counting test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Input lines:

```text
pod abc failed with code 1
pod def failed with code 2
node 10.0.0.1 ready
```

Expected normalized counts:

```text
pod abc failed with code <NUMBER> : 1
pod def failed with code <NUMBER> : 1
node <IPV4> ready : 1
```

At this point, do not group by similarity yet.

---

### Task 21: Implement `count_patterns`

**Time:** 3-5 min
**Files:** `trim.py`

Add:

```python
from collections import Counter

def count_patterns(lines: Iterable[str]) -> Counter[str]:
    counter = Counter()
    for line in lines:
        pattern = normalize_line(line)
        if pattern:
            counter[pattern] += 1
    return counter
```

---

### Task 22: Add file streaming test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Test that `run()` reads input line-by-line and writes counts.

Use a small temp file.

Assert output contains:

```text
COUNT
<PATTERN>
```

and the expected count.

---

### Task 23: Implement streaming read/write path

**Time:** 3-5 min
**Files:** `trim.py`

In `run()`:

1. Open input file.
2. Call `count_patterns`.
3. Write metadata + sorted counts.

Sort by count descending, then pattern ascending.

---

## Phase 4 — Similarity Grouping

### Task 24: Add similarity function test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Test:

```python
similarity("pod failed pulling image", "pod failed pull image")
```

should be high enough.

Also test unrelated lines:

```python
similarity("pod failed", "node disk pressure")
```

should be low.

---

### Task 25: Implement similarity fallback

**Time:** 3-5 min
**Files:** `trim.py`

Use optional `rapidfuzz` if available, otherwise `difflib`.

```python
try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None
```

Implementation:

```python
def similarity(a: str, b: str) -> float:
    if fuzz is not None:
        return fuzz.ratio(a, b) / 100.0
    return difflib.SequenceMatcher(None, a, b).ratio()
```

Keep score as `0.0` to `1.0`.

---

### Task 26: Add grouping test at threshold 0.85

**Time:** 4-5 min
**Files:** `tests/test_trim.py`

Input pattern counts:

```python
{
    "pod <WORD> failed pulling image <DOMAIN>/<WORD>:<NUMBER>": 3,
    "pod <WORD> failed pull image <DOMAIN>/<WORD>:<NUMBER>": 2,
    "node <IPV4> disk pressure true": 5,
}
```

Expected:

* First two patterns group together.
* Third remains separate.
* Combined count is `5`.

---

### Task 27: Implement greedy grouping

**Time:** 4-5 min
**Files:** `trim.py`

Add:

```python
@dataclass
class PatternGroup:
    pattern: str
    count: int
    examples: list[str]
```

Algorithm:

1. Sort patterns by count descending.
2. For each pattern:

   * Compare against existing group representatives.
   * If similarity >= threshold, merge into that group.
   * Else create new group.
3. When merging:

   * Add count.
   * Keep the higher-count pattern as representative.
   * Store up to 3 examples.

This is simple and acceptable for MB to hundreds of MB because grouping happens on unique normalized patterns, not raw lines.

---

### Task 28: Add grouping threshold boundary test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Test that with threshold `0.90`, fewer patterns merge than with `0.80`.

This proves threshold behavior is meaningful.

---

### Task 29: Add CLI threshold option

**Time:** 3-5 min
**Files:** `trim.py`, `tests/test_trim.py`

Keep required CLI unchanged:

```bash
python trim.py input.txt output.txt
```

Add optional:

```bash
python trim.py input.txt output.txt --threshold 0.85
```

Validation:

* Accept only `0.80 <= threshold <= 0.90`.
* Default: `0.85`.

---

## Phase 5 — Better Variable Extraction

### Task 30: Add Kubernetes pod/container ID normalization tests

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Test common K8s-ish values:

```text
pod nginx-7d9f8c9b45-xk2aa started
container docker://abcdef1234567890 restarted
```

Expected:

```text
pod <ID> started
container docker://<HEX> restarted
```

or:

```text
pod <WORD> started
container docker://<HEX> restarted
```

Choose one simple placeholder strategy and make it consistent.

---

### Task 31: Implement hex/id normalization

**Time:** 3-5 min
**Files:** `trim.py`

Add regex for long hex strings:

```python
r"\b[0-9a-fA-F]{12,}\b"
```

Replace with `<HEX>`.

Run after UUID/MAC/IP, before generic number.

---

### Task 32: Add URL normalization test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Input:

```text
GET https://api.example.com/v1/users/123 failed
```

Expected:

```text
GET <URL> failed
```

or a structured alternative:

```text
GET <DOMAIN><PATH> failed
```

For compression, `<URL>` is simpler.

---

### Task 33: Implement URL normalization

**Time:** 3-5 min
**Files:** `trim.py`

Add:

```python
r"\bhttps?://[^\s]+"
```

Replace with `<URL>`.

Run before domain/path normalization.

---

## Phase 6 — Output Metadata

### Task 34: Add metadata calculation test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Given:

* input lines: 10
* grouped patterns: 3

Expected compression ratio:

```text
70.00%
```

Define compression ratio as:

```python
1 - grouped_patterns / input_lines
```

For empty input, use `0.00%`.

---

### Task 35: Implement metadata object

**Time:** 3-5 min
**Files:** `trim.py`

Add:

```python
@dataclass
class TrimStats:
    input_lines: int
    exact_patterns: int
    grouped_patterns: int
    threshold: float

    @property
    def compression_ratio(self) -> float:
        ...
```

---

### Task 36: Add full output format test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Assert output contains:

```text
# input_lines=
# exact_patterns=
# grouped_patterns=
# compression_ratio=
# threshold=
COUNT    PATTERN
```

Do not assert the whole file exactly. Keep tests resilient.

---

### Task 37: Implement final writer

**Time:** 3-5 min
**Files:** `trim.py`

Add:

```python
def write_output(output_path: str, groups: list[PatternGroup], stats: TrimStats) -> None:
    ...
```

Write groups sorted by count descending.

---

## Phase 7 — stdin Support

### Task 38: Add stdin behavior test

**Time:** 4-5 min
**Files:** `tests/test_trim.py`

Run:

```bash
python trim.py - output.txt
```

Pass input via `subprocess.run(input=...)`.

Expected output file exists and contains patterns.

---

### Task 39: Implement stdin support

**Time:** 3-5 min
**Files:** `trim.py`

If input path is `-`, read from `sys.stdin`.

Keep output path required.

---

## Phase 8 — Error Handling

### Task 40: Add missing input file test

**Time:** 3-5 min
**Files:** `tests/test_trim.py`

Run with nonexistent input path.

Expected:

* non-zero exit code
* stderr contains useful error
* output file is not created

---

### Task 41: Implement file error handling

**Time:** 3-5 min
**Files:** `trim.py`

Catch:

```python
FileNotFoundError
PermissionError
OSError
```

Print to stderr and return `1`.

Do not swallow unexpected exceptions in pure functions.

---

### Task 42: Add invalid threshold test

**Time:** 2-4 min
**Files:** `tests/test_trim.py`

Run:

```bash
python trim.py input.txt output.txt --threshold 0.5
```

Expected non-zero exit from argparse.

---

### Task 43: Implement threshold validation

**Time:** 2-4 min
**Files:** `trim.py`

Use a custom argparse type:

```python
def threshold_value(value: str) -> float:
    parsed = float(value)
    if not 0.80 <= parsed <= 0.90:
        raise argparse.ArgumentTypeError("threshold must be between 0.80 and 0.90")
    return parsed
```

---

## Phase 9 — Performance Safety

### Task 44: Add large-ish synthetic test

**Time:** 4-5 min
**Files:** `tests/test_trim.py`

Generate 10,000 lines in a temp file:

```text
2026-04-24T10:00:00Z pod app-1 failed with code 1
2026-04-24T10:00:01Z pod app-2 failed with code 2
...
```

Assert:

* CLI completes.
* output exists.
* grouped pattern count is much lower than input lines.

Do not make this test too slow.

---

### Task 45: Avoid storing raw lines

**Time:** 3-5 min
**Files:** `trim.py`

Ensure implementation only keeps:

* total line count
* `Counter` of normalized patterns
* grouped pattern list

Do not store all input lines in memory.

---

### Task 46: Cap examples per group

**Time:** 2-4 min
**Files:** `trim.py`

If examples are included, store max 3 examples per group.

This prevents large memory growth from many near-duplicate patterns.

---

## Phase 10 — Documentation

### Task 47: Add README usage

**Time:** 3-5 min
**Files:** `README.md`

Document:

```bash
python trim.py input.txt output.txt
python trim.py input.txt output.txt --threshold 0.85
cat input.txt | python trim.py - output.txt
```

Explain placeholders and output metadata.

---

### Task 48: Add design notes to README

**Time:** 3-5 min
**Files:** `README.md`

Document:

* Regex normalization order matters.
* Similarity grouping runs on unique normalized patterns, not raw logs.
* `rapidfuzz` is optional.
* Fallback uses `difflib`.
* Intended scale: MB to hundreds of MB, not GB-scale streaming analytics.

---

## Phase 11 — Final Verification

### Task 49: Run unit tests

**Time:** 2-5 min

Command:

```bash
python -m unittest
```

Expected: all tests pass.

---

### Task 50: Run CLI manually with sample logs

**Time:** 3-5 min

Create:

```text
2026-04-24T10:11:12Z kubelet[123]: Started container 550e8400-e29b-41d4-a716-446655440000
2026-04-24T10:11:13Z kubelet[456]: Started container 550e8400-e29b-41d4-a716-446655440001
Apr 24 10:11:14 node kubelet[999]: Failed pulling image registry.k8s.io/pause:3.9
Apr 24 10:11:15 node kubelet[998]: Failed pulling image registry.k8s.io/pause:3.8
```

Run:

```bash
python trim.py sample.log trimmed.log
```

Expected:

* output has metadata
* repeated forms are counted
* compression ratio is greater than 0

---

### Task 51: Check dependency boundary

**Time:** 2-3 min

Search imports manually.

Allowed:

```python
argparse
collections
dataclasses
difflib
re
sys
pathlib
typing
```

Optional:

```python
rapidfuzz
dateutil
```

Reject:

```python
pandas
numpy
asyncio
threading
multiprocessing
database clients
```

---

# Suggested Implementation Order

Use this sequence:

1. CLI skeleton
2. Normalization regexes
3. Exact pattern counting
4. Output writer
5. Similarity grouping
6. Metadata
7. stdin and error handling
8. Performance guardrails
9. README

This keeps the tool useful early, then adds grouping after the core normalization/counting path is stable.

---

# Core Function List

`trim.py` should end up with roughly these functions/classes:

```python
@dataclass
class PatternGroup:
    pattern: str
    count: int
    examples: list[str]


@dataclass
class TrimStats:
    input_lines: int
    exact_patterns: int
    grouped_patterns: int
    threshold: float

    @property
    def compression_ratio(self) -> float:
        ...


def normalize_line(line: str) -> str:
    ...


def count_patterns(lines) -> tuple[Counter[str], int]:
    ...


def similarity(a: str, b: str) -> float:
    ...


def group_patterns(pattern_counts: Counter[str], threshold: float) -> list[PatternGroup]:
    ...


def write_output(output_path: str, groups: list[PatternGroup], stats: TrimStats) -> None:
    ...


def run(input_path: str, output_path: str, threshold: float = 0.85) -> int:
    ...


def main(argv=None) -> int:
    ...
```

---

# Regex Replacement Order

Use this order to avoid corrupting specific values before they are recognized:

```text
1. URL
2. TIMESTAMP
3. UUID
4. MAC
5. IPV4
6. IPV6
7. PATH
8. DOMAIN
9. HEX
10. NUMBER
11. WHITESPACE CLEANUP
```

Reason: generic number replacement would otherwise break IPs, timestamps, UUIDs, MACs, and versions.

---

# Test Strategy Summary

## Unit Tests

Cover:

* individual placeholder normalization
* replacement order
* exact pattern counting
* similarity scoring
* grouping threshold behavior
* metadata calculation
* output formatting

## CLI Tests

Cover:

* normal file input/output
* stdin input with `-`
* invalid input file
* invalid threshold
* optional `rapidfuzz` absence fallback indirectly through `difflib`

## Performance Tests

Cover:

* 10,000 synthetic lines
* no raw line accumulation
* meaningful compression ratio

---

# Acceptance Criteria Mapping

| Acceptance Criteria                         | Plan Coverage      |
| ------------------------------------------- | ------------------ |
| `python trim.py input.txt output.txt` works | Tasks 2-3, 22-23   |
| Output contains counts                      | Tasks 20-23, 36-37 |
| Variables normalized                        | Tasks 4-19, 30-33  |
| Similar logs grouped at 80-90%              | Tasks 24-29        |
| Tests pass                                  | Tasks 1-51         |
| Compression ratio metadata                  | Tasks 34-37        |
| Handles MB to hundreds of MB                | Tasks 44-46        |
| No heavy dependencies                       | Task 51            |

---

# Definition of Done

The implementation is complete when:

```bash
python -m unittest
```

passes and this command:

```bash
python trim.py input.txt output.txt
```

produces an output file containing:

```text
# Log Trimmer Output
# input_lines=
# exact_patterns=
# grouped_patterns=
# compression_ratio=
# threshold=

COUNT    PATTERN
```

with normalized patterns and occurrence counts.

```
```
