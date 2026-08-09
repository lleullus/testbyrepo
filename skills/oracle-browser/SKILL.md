---
name: oracle-browser
description: Use when the user asks Oracle or Oracle Browser to review, inspect, verify, challenge, continue a saved consultation, or provide a second opinion on code, diffs, tests, documents, plans, or architecture, including requests in "데브스페이스 모드" (DevSpace mode) where files are accessed through the DevSpace MCP plugin instead of attachments. Runs stock Oracle through the managed WSL browser-slot wrapper, including single-ZIP attachments and same-conversation followups; do not use a Windows runtime or Bridge.
---

# Oracle Browser

Use the repository wrapper around stock Oracle as an advisory second-model
reviewer. Oracle receives only the prompt and files explicitly supplied to it.
Verify important findings against local source, tests, contracts, and runtime
evidence before presenting them as facts.

## Fixed Local Runtime

This machine uses WSL Linux Chrome over loopback CDP:

```bash
ORACLE_CLI="/home/user01/.nvm/versions/node/v24.18.0/bin/oracle"
ORACLE_SLOTS="/home/user01/project/oracle/oracle-browser-slots/bin/oracle-browser-slots"
```

Runtime identity:

- Oracle package: `@steipete/oracle@0.16.1`
- Linux Chrome: `/usr/bin/google-chrome`
- managed profiles: `/home/user01/.oracle/browser-profiles/slot-1` through `slot-5`
- sessions and artifacts: `/home/user01/.oracle/sessions`
- browser transport: local CDP at `127.0.0.1:19222` through `127.0.0.1:19226`
- wrapper state: `/home/user01/.oracle/browser-slots`

The wrapper selects or pins one managed slot, injects its `--remote-chrome`,
claims it atomically, and runs the canonical stock CLI without a shell. These
are local WSL Chrome endpoints, not a network Bridge.

## Required Execution Path

Before the first Oracle call in a task:

1. Run `"$ORACLE_CLI" --help --verbose` once for the session. Basic `--help`
   is intentionally curated; verbose help includes supported advanced browser
   controls such as `--browser-thinking-time`.
2. Run `"$ORACLE_SLOTS" status` and require at least one managed slot to be
   available. If a slot needs operator preparation, run
   `"$ORACLE_SLOTS" prepare --slot <id>` and require `사용 가능`.
3. Create one unique, stable context ID for the current OpenCode conversation
   before its first live Oracle request. Reuse that exact ID for every later
   followup in this OpenCode conversation; never reuse it across conversations.
4. For a non-trivial file set, run a dry-run before the live request.
5. Submit the live request through the wrapper with `--engine browser` and
   `--browser-model-strategy current`. Never invoke a live stock Oracle request
   directly.

Use a long shell-tool timeout such as `3600000` milliseconds for a live run.
The timeout belongs to the shell tool, not to Oracle's CLI arguments.

```bash
env -u ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS \
  "$ORACLE_SLOTS" submit \
  --request-id "<unique-request-id>" \
  --opencode-conversation-id "<current-opencode-conversation-id>" -- \
  "$ORACLE_CLI" \
  --engine browser \
  --browser-model-strategy current \
  -p "Review the supplied evidence. Lead with material findings, cite concrete evidence, and identify missing verification." \
  --file /absolute/path/to/file
```

The wrapper owns `--slug`, `--remote-chrome`, `--wait`, and browser archive
policy for context-aware calls. Do not pass those options unless a documented
wrapper command explicitly requires them. A context-aware initial request keeps
its conversation unarchived so a later request can continue it.

## Reasoning Level Routing

Pass `--browser-thinking-time` only when the user explicitly requests a
reasoning level. Prefer the ChatGPT UI intent names; stock Oracle normalizes
them to its canonical names:

- `instant` (`light`) uses slots 1 or 2;
- `medium` (`standard`) uses slots 1 or 2 first, then falls back to slots 3, 4, or 5;
- `high` (`extended`) prefers slots 3, 4, or 5, then falls back to slots 1 or 2;
- `extra-high` (`heavy`, also `extrahigh` or `xhigh`) uses slots 1 or 2;
- `pro` uses slots 1 or 2;
- omitting the option leaves the current UI effort unchanged and permits any
  managed slot.

The order above is the auto-allocation preference. An explicit `run --slot`
must still choose a compatible slot. Never lower, raise, or omit an explicitly
requested reasoning level merely to use an available slot, and never infer a
default reasoning level from a slot's maximum capability.

Do not invoke Oracle with `--browser-manual-login`, `--browser-chrome-path`, or
`--browser-keep-browser` on this WSL runtime. Oracle 0.16.1's bundled launcher
treats WSL as a Windows-Chrome environment, translating the Linux profile path
to UNC and selecting the WSL nameserver for CDP. The local Chrome process is
therefore launched or reused by wrapper `prepare` and passed to stock Oracle
through the supported `--remote-chrome` surface.

## Dry Run

Dry-run does not open a new tab or submit a prompt:

```bash
env -u ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS \
  "$ORACLE_SLOTS" run \
  --slot <available-slot-id> \
  --job-id "<unique-dry-run-id>" -- \
  "$ORACLE_CLI" \
  --dry-run summary \
  --engine browser \
  --browser-model-strategy current \
  -p "<task>" \
  --file /absolute/path/to/file
```

Require the control plan to say that Oracle will reuse an existing remote
Chrome session. Stop if it selects local Chrome launch, cookie copy, a remote
host service, or Bridge.

## File Selection

Attach the smallest file set that contains the truth:

- use absolute canonical paths whenever practical;
- attach source, tests, contracts, schemas, configuration, and concise runtime
  evidence that directly bear on the question;
- use repeated `--file` options or supported globs and explicit exclusions;
- run `--dry-run summary --files-report` for a large or uncertain bundle;
- never attach `.env`, credentials, browser profiles, cookies, auth databases,
  private keys, tokens, or unrelated user data;
- the wrapper applies stock Oracle file selection, creates one deflated ZIP,
  and passes only that ZIP to stock Oracle;
- the wrapper does not apply its own source-file or generated-ZIP size cap, but
  browser, ChatGPT, operating-system, disk, and memory limits still apply;
- inspect the stored attachment manifest when a file-bearing request has an
  ambiguous upload or submission result.

Reading a local file is not equivalent to attaching it. If Oracle must inspect
the file, include it with `--file` or quote the required evidence in the prompt.
DevSpace mode is the only exception: do not attach those files as a ZIP; see the
next section.

## DevSpace Mode (데브스페이스 모드)

Trigger: the user says "데브스페이스 모드" or instructs "데브스페이스
플러그인으로 접근해" and supplies absolute paths. In this mode Oracle reads the
files through the DevSpace MCP plugin inside ChatGPT instead of the wrapper ZIP
attachment.

Preconditions before the first live request:

1. Verify DevSpace health: `systemctl --user is-active devspace-http.service`
   must return `active` and `curl --fail --silent --show-error http://127.0.0.1:8787/healthz`
   must succeed. If unhealthy, ask the user to
   start it through the devspace-launcher skill flow and do not submit.
2. Resolve every supplied path with `realpath` and require it to sit inside one
   of the allowed roots: `/home/user01/project`,
   `/mnt/d/개발방법론/개발방법론`, `/tmp`, or `/home/user01/.codex/skills`.
   Refuse any other path.

Submission:

- Do not pass `--file` for DevSpace-mode files; they must not be ZIP-attached.
- In the prompt, explicitly instruct ChatGPT to read the listed absolute paths
  through the DevSpace MCP plugin, and list each absolute path.
- In every initial and followup prompt, explicitly instruct ChatGPT to perform
  the investigation itself. It must not read or invoke the `oracle-browser`
  skill, run the Oracle CLI or browser-slot wrapper, ask another Oracle, or
  delegate the work to a DevSpace subagent. DevSpace tools may be used only to
  inspect the listed paths and gather evidence for the current answer.
- Never include the owner password, `auth.json`, tokens, or OAuth credentials in
  the prompt; the plugin depends on ChatGPT-side owner-password OAuth approval.
- The dry run, slot, and wrapper requirements above still apply unchanged.

Because plugin reads depend on ChatGPT-side MCP approval, verify important
findings against the local files afterward as usual.

## Prompt Contract

Oracle starts without project context. A useful request should include:

- the exact decision or review question;
- project and runtime constraints;
- relevant entry points and boundaries;
- observed behavior and verbatim errors;
- prior attempts and unresolved hypotheses;
- requested output format and evidence standard;
- explicit instruction not to modify files when review-only behavior is wanted.

For code review, require findings first, ordered by severity, with concrete file
and line references. Ask Oracle to distinguish confirmed defects, inferences,
and missing runtime verification.

## Sessions And Recovery

Keep the reported session ID. Inspect the existing session before considering a
retry:

```bash
env -u ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS \
  "$ORACLE_CLI" status --hours 72

env -u ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS \
  "$ORACLE_CLI" session <session-id> --render
```

If a run times out, disconnects, or returns an ambiguous submission state, do
not start a duplicate. Reattach to the stored session first. Retry only when
the existing session proves that no prompt was submitted or when the user asks
for a genuinely new run.

For an ordinary followup request in the same OpenCode conversation, do not ask
the user to find a session ID. Let the wrapper select the newest eligible
parent carrying the current context ID:

```bash
env -u ORACLE_BROWSER_INACTIVITY_TIMEOUT_SECONDS \
  "$ORACLE_SLOTS" followup \
  --request-id "<unique-followup-request-id>" \
  --opencode-conversation-id "<same-current-opencode-conversation-id>" -- \
  "$ORACLE_CLI" \
  --engine browser \
  --browser-model-strategy current \
  -p "<follow-up question>"
```

Use `--parent-session-id <session-id>` only when the user explicitly names a
parent. An ineligible explicit parent must fail without fallback. The wrapper
pins followup to the parent's originating slot, waits only when that slot is
occupied, restores an archived parent when needed, and never switches slots.

Do not confuse managed followup eligibility with chat existence. A rejection
for missing context or origin metadata does not mean the parent session or
ChatGPT conversation is absent. Check the parent `meta.json`, transcript, stable
`/c/<id>` URL, and live tab before reporting what is missing.

For a legacy parent that has a completed answer and stable chat URL but lacks
`oracle_browser_slots` origin metadata:

1. Finalize it with `oracle session <id> --render` and prepare its known slot.
2. Never forge session metadata or pass `--followup` through `run`/`submit`.
3. Only when the user explicitly requests that exact chat, open and verify the
   exact URL in the known slot, dry-run `--browser-tab <url>`, then use managed
   `run` with that exact tab and the current conversation context ID.
4. Verify the child completed on the same URL and report that this is verified
   chat continuity, not authoritative wrapper followup lineage.

After success, require the final `session_persisted.authoritative_readback` to
show the selected parent, distinct child, original slot, matching conversation
ID/URL, submitted prompt, completed result, and `verification.ok: true`. Read the
child once through stock `oracle session <child-id> --render` when an independent
stored-session readback is useful.

## Model Selection

The Oracle CLI itself defaults to `select`, but this skill hard-fixes its
default to `current`: every invocation must pass
`--browser-model-strategy current`. This keeps the model already selected in
ChatGPT and avoids picker automation. Do not omit the flag or silently change
it to `select`.

Do not claim a specific actual ChatGPT model solely from Oracle's default model
field. Report model-selection evidence exactly as stored in the session
metadata; `verified: false` means the active model label was not verified.

## Deep Research

Deep Research mode is not used by this skill. Never pass
`--browser-research deep`; detailed investigations must use the normal browser
request path with `--browser-model-strategy current`.

## Failure Handling

- If `prepare` or `status` fails, report the exact slot and operator action and
  stop. Do not delete locks, edit slot state, or launch a competing profile.
- If authentication is missing, ask the user to sign into ChatGPT in that
  managed WSL slot profile; do not copy cookies from Windows.
- If the selected followup slot is unavailable, do not use another slot.
- If submission is ambiguous, inspect/harvest the stored session before any
  retry. Do not duplicate a prompt whose submission cannot be disproved.
- Do not patch the installed Oracle package or its dependencies.
- Do not create a Windows Oracle runtime, Windows Chrome profile, `oracle-go`,
  `oracle-plus`, `oracle serve`, or Bridge fallback.

## Reporting

After a successful run, report:

- the Oracle session ID and completion status;
- the actual answer or prioritized findings;
- the parent and child session IDs for a followup;
- the attached file set and single-ZIP manifest at a safe summary level;
- the selected managed slot and local CDP endpoint;
- same-conversation and authoritative-readback status for a followup;
- model-selection verification status;
- the transcript or output path when one was created;
- any claim that still needs local verification.
