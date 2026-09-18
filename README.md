# logtrim 3.0.0

A zero-runtime-dependency, disk-backed log pattern analyzer. Python 3.10+.
Direct execution does not require installation. Building a wheel uses setuptools.

## Run

```sh
python -m unittest discover -s tests -v
python trim.py app.log report.json --format json
python -m logtrim analyze app.log report.html --format html --top 2000
cat app.log | python -m logtrim - - --format jsonl
python -m logtrim diff before.log after.log -o diff.json --format json --changes-only
python -m logtrim explain --line 'ORA-00600 peer 2001:db8::1'
```

Optional installation: `python -m pip install .`, then use `logtrim`.
With an existing setuptools installation, `--no-build-isolation` avoids fetching
build requirements. Neither the installed application nor its tests need third-party libraries.

## Implemented behavior

JSON-object/JSONL, strict logfmt, Klog and plain-text inputs share a parser-first
normalizer. Non-overlapping span replacement protects Java/Python exception names,
error codes, versions and HTTP request routes. IP candidates are validated.
Unknown numeric literals and unqualified domain-like words remain literal.
Known numeric fields and duration tokens retain count/min/max/mean statistics.
JSON field types, keys and ordering are canonicalized without regex-editing raw JSON.

Greedy leader assignment replaces Union-Find. A fixed-depth typed-path index,
relaxed prefix and token-count fallback each receive a bounded query quota.
The total comparisons per new exact pattern never exceeds `--max-candidates`.
Different static literals never fuzzy-merge. Only compatible typed slots generalize.
The immutable original leader and current template must both pass the threshold.
Ambiguous matches create a new cluster. This is Drain-inspired, not canonical Drain.

All exact identities and cluster aggregates reside in a private temporary SQLite
file, not an in-memory dictionary of all patterns. Input and output are streamed;
only one bounded event, a bounded exact cache and bounded candidates are retained.
`--work-dir`, `--cache-size`, `--sqlite-cache-kib`, `--max-event-bytes`,
`--max-event-lines`, `--max-tokens`, `--max-input-bytes` and `--max-clusters`
control resources. Optional limits use 0 for unlimited. Disk consumption still
grows with unique patterns. These are structural bounds, not a hard RSS guarantee.
SQLite state is deleted on context exit; checkpoint/resume is not implemented.

Counts are exact for accepted logical events; candidate retrieval is approximate
and can under-merge. Input order can affect clusters. For the same ordered input
and configuration, assignments repeat; timing diagnostics naturally differ.
The numeric threshold is not equivalent to v2's SequenceMatcher threshold.
No optional similarity package is imported or allowed to change decisions.

Multiline auto mode reconstructs common Python/Java traces and indented wrapped
lines. Each input file is a separate source. Use `--multiline off` for unrelated
indented records. Interleaved streams must be demultiplexed before this tool.
Pretty-printed multiline JSON and every stack-trace dialect are not guaranteed.
Oversized records stop processing rather than silently splitting/dropping data.
Blank physical lines are counted separately and do not become events.

Timestamp offsets are converted to UTC. Naive timestamps assume UTC unless
`--timezone-minutes` specifies an offset. Yearless Syslog/Klog timestamps remain
unknown unless `--syslog-year` is supplied. There is no automatic year rollover.

Diff freezes baseline templates and matches current events against that model.
New current clusters are learned separately. Smoothed per-event rates identify
NEW, RESOLVED, SURGED, DROPPED and STABLE changes; this is descriptive comparison,
not a statistical significance test. Rarity is -log2(cluster frequency).
`--rare-max-count` filters analyze output. Reports sort by total count.
Filtering and `--top` affect output only, not summary totals.

## Custom JSON rules

Save as rules.json and pass `--rules rules.json`:

```json
{"version":1,"rules":[
  {"id":"order-id","pattern":"\\bord_[A-Z0-9]{6}\\b","placeholder":"ORDER_ID"},
  {"id":"keep-code","pattern":"\\bACME-\\d{6}\\b","action":"preserve"}
]}
```

Rules apply to free-text/string values after structured field policies.
Actions: replace (default), preserve, redact. Rule IDs must be unique; placeholders
must match `[A-Z][A-Z0-9_]*`. Empty matches and malformed rules are rejected.
Only trusted regex rules should be loaded: stdlib re has no execution timeout.
YAML, arbitrary executable plugins, LSH, native acceleration and TUI are not included.

## Safety and API

Samples default to none. `--sample-mode redacted` stores a normalized sample;
`raw` explicitly stores original text. Recognized secret fields are masked, but
unrecognized secrets can still appear in patterns: review rules before sharing.
URL credentials are removed with the URL. Text control characters and HTML are
escaped. HTML is self-contained with a hash-based script CSP and local filtering.
Large HTML reports should use `--top` to limit browser memory.

File inputs recognize gzip/bzip2/xz by magic bytes. Compressed stdin is not decoded;
pipe it through the appropriate decompressor. Decoding defaults to UTF-8 strict;
`--decode-errors replace` counts affected lines. The line reader needs a byte-LF-compatible
encoding; convert UTF-16/UTF-32 to UTF-8 before input. Output files are atomically replaced
only after successful analysis and rendering. Input/output aliases are rejected.
Exit codes: 0 success (including closed output pipe), 1 I/O, 2 config/usage,
3 resource limit, 130 interruption. Existing reports survive failures.

Use `with Analyzer(Config(...)) as a: a.ingest(lines)` and iterate `a.rows()` inside
the context. `extract_pattern`, `parse_timestamp`, `group_logs` and the legacy
`trim.py input output` entry point are retained. The v3 JSON schema intentionally
changes; templates are available as both pattern strings and typed-token lists.
`format_output` is a small-result convenience wrapper; the CLI uses streaming render.