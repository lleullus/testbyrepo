# Oracle Browser Slots

This repository provides five explicitly selected WSL Linux Chrome slots for
Oracle Browser. It does not identify the ChatGPT account in a profile or compare
accounts between slots.

## Commands

Run the repository-local entry point directly:

```bash
./bin/oracle-browser-slots prepare --slot 1
./bin/oracle-browser-slots status --slot 1
./bin/oracle-browser-slots status
./bin/oracle-browser-slots run --slot 1 --job-id example-001 -- \
  /home/user01/.nvm/versions/node/v24.18.0/bin/oracle \
  --engine browser --remote-chrome 127.0.0.1:19222 \
  --browser-model-strategy current -p "<task>"
./bin/oracle-browser-slots submit --request-id example-auto-001 -- \
  /home/user01/.nvm/versions/node/v24.18.0/bin/oracle \
  --engine browser --browser-model-strategy current -p "<task>"

# Record an initial session as owned by one exact OpenCode conversation.
./bin/oracle-browser-slots submit --request-id example-context-001 \
  --opencode-conversation-id "<current-opencode-conversation-id>" -- \
  /home/user01/.nvm/versions/node/v24.18.0/bin/oracle -p "<task>"

# Continue the newest eligible session owned by that OpenCode conversation.
./bin/oracle-browser-slots followup --request-id example-followup-001 \
  --opencode-conversation-id "<current-opencode-conversation-id>" -- \
  /home/user01/.nvm/versions/node/v24.18.0/bin/oracle -p "<follow-up>"

# An explicit eligible parent takes precedence over implicit selection.
./bin/oracle-browser-slots followup --request-id example-followup-002 \
  --opencode-conversation-id "<current-opencode-conversation-id>" \
  --parent-session-id "<oracle-session-id>" -- \
  /home/user01/.nvm/versions/node/v24.18.0/bin/oracle -p "<follow-up>"
```

Every command writes structured JSON. A status record contains `slot_id`,
`port`, `profile_dir`, `status`, `checked_at`, `reason`, and
`operator_action`. An occupied record additionally contains `job_id` and
`started_at`. The state values are `미준비`, `사용 가능`, `점유 중`, and
`사용 불가`.

`prepare` launches or reuses a loopback CDP Chrome at the fixed slot port and
opens ChatGPT in that slot's fixed profile. It returns exit code `0` only when
the resulting status is `사용 가능`; the JSON output explains login, CDP, or
preparation failures and the required operator action.

`run` requires an explicit slot, job ID, and stock Oracle argv after `--`. The
executable must be the canonical `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`;
the wrapper never accepts a basename or shell/env wrapper. It never passes the
command through a shell. It claims the slot atomically, runs one child, and
releases the claim after success, non-zero exit, spawn failure, or Ctrl-C
interruption. Lifecycle records are newline-delimited JSON on stderr so the
child command's stdout and stderr remain available to the operator.

The child receives these environment variables:

- `ORACLE_BROWSER_SLOT_ID`
- `ORACLE_BROWSER_SLOT_PORT`
- `ORACLE_BROWSER_REMOTE_CHROME` with the value `127.0.0.1:<slot-port>`

The stock Oracle example above consumes the deterministic slot 1 endpoint.
For slot 2 use `--slot 2` and `--remote-chrome 127.0.0.1:19223`; for slot 3 use
`127.0.0.1:19224`; for slot 4 use `127.0.0.1:19225`; for slot 5 use
`127.0.0.1:19226`. Missing `--engine browser`,
`--browser-model-strategy current`, or `--remote-chrome` values are injected
for the selected slot. Conflicting or duplicate values and alternate transport
options are rejected before claim. A second request for an occupied slot is
rejected immediately.
If the runner disappears, its PID and Linux `/proc/<pid>/stat` starttime remain
in the occupancy record; status and run will mark the slot `사용 불가` until an
explicit `prepare` recovers it.

`submit` accepts a request ID and the same canonical stock Oracle argv without a
slot. It claims the first available slot in 1, 2, 3, 4, 5 order, injects that slot's
fixed `--remote-chrome`, and emits lifecycle JSONL on stderr. When all usable
slots are occupied it emits a FIFO queue record and waits without automatic
expiry. `submit` accepts no caller-supplied `--remote-chrome`; the selected
slot endpoint is always authoritative. Ctrl-C or SIGTERM cancels a waiting
request or safely stops a running child without retrying it elsewhere.

`--opencode-conversation-id` is optional for ordinary `run` and `submit`. When
present, the wrapper gives the stock run a unique session slug, waits for that
canonical child to terminate, and atomically records the exact OpenCode
conversation ID and originating managed slot/profile in the stock session's
`meta.json`. The ID must come from the caller's current OpenCode conversation;
the wrapper never infers ownership from a session filename, current directory,
or unrelated global sessions. Without this option, existing `run` and `submit`
argv and behavior are unchanged. For context-aware requests, the wrapper owns
`--browser-archive` and passes `never`; callers cannot override that policy.

`followup` requires that durable OpenCode conversation ID. Without
`--parent-session-id`, it selects the newest eligible session carrying that
exact ID. An eligible parent is a browser session whose canonical Oracle child
has terminated and whose stable ChatGPT `/c/<id>` identity and exact managed
origin slot/profile can be read back. `completed`, `error`, `cancelled`, and
ChatGPT archive labels do not by themselves include or exclude a session. An
actually active session or one missing conversation/origin evidence is
ineligible. An explicit parent is tried exclusively; an ineligible explicit ID
fails without falling back to the implicit candidate. No eligible parent means
failure before a child is spawned or a prompt is submitted, never a new-chat
fallback.

The parent origin slot is authoritative for `followup`. If occupied, the caller
waits only for that slot without automatic expiry and can cancel with Ctrl-C,
SIGTERM, or SIGHUP. If that slot is unprepared or unavailable, the request fails
with its recovery action and never checks or claims another slot. Once claimed,
the wrapper invokes the canonical stock CLI with `--followup <parent-session-id>`
and the fixed origin `--remote-chrome`; stock Oracle performs the ChatGPT
automation and creates a separate child session.

When an otherwise eligible parent was archived, `followup` restores that exact
ChatGPT conversation through the originating slot's CDP session after claiming
the slot and passing pre-submit readiness. It requires the same stable
`/c/<id>` URL and a usable composer before stock Oracle starts. A failed restore
releases that claim without spawning stock Oracle, submitting a prompt, or
falling back to another slot.

The final `session_persisted` JSONL record contains `authoritative_readback`.
The same durable contract is under `oracle_browser_slots.followup` in
`$ORACLE_HOME_DIR/sessions/<child-session-id>/meta.json`: `selection_mode`,
`parent_session_id`, `child_session_id`, `original_slot`, expected/actual
conversation ID and URL, prompt submission, completion, result log paths/hash,
and verification. The parent file is not modified. Stock lineage remains in
`options.followupSessionId`, so normal stock lookup still shows the chain and
answer:

```bash
/home/user01/.nvm/versions/node/v24.18.0/bin/oracle session "<child-session-id>"
/home/user01/.nvm/versions/node/v24.18.0/bin/oracle session "<child-session-id>" --path
```

The response stays in stock Oracle's output/model log or transcript rather than
being duplicated into metadata; the custom `result` object records its paths,
byte count, and SHA-256. A successful child becomes the newest eligible implicit
parent for the next call because it inherits the exact OpenCode conversation and
origin-slot evidence.

When `run` or `submit` receives `--file` (or one of its stock aliases), the
wrapper reuses stock Oracle 0.16.1 file selection, creates one deflated ZIP,
and passes only that ZIP to the canonical Oracle child. Source and generated-ZIP
size preflight caps are not applied by this wrapper; operating-system, disk,
memory, browser, and ChatGPT limits still apply. Conflicting browser attachment
and bundle flags are overridden for that request. A successful or attempted
session-backed file-bearing run stores
`artifacts/oracle-browser-slots-attachments.json` under the stock session
directory and points to it from `meta.json`; sessionless validation commands
such as `--dry-run` still report and clean up the generated ZIP but do not
require a session manifest. The generated ZIP is removed after the child
exits, including failure and interruption paths.

## Runtime boundaries

Defaults match the WSL Oracle Browser runtime:

- Chrome: `/usr/bin/google-chrome` (or `CHROME_PATH`)
- Ports: `127.0.0.1:19222` through `127.0.0.1:19226`
- Profiles: `~/.oracle/browser-profiles/slot-1` through `slot-5`
- State: `~/.oracle/browser-slots`

Tests and non-production runs can isolate the runtime with:

- `ORACLE_BROWSER_SLOTS_STATE_ROOT`
- `ORACLE_BROWSER_SLOTS_PROFILE_ROOT`
- `ORACLE_BROWSER_SLOTS_CHROME_PATH`
- `ORACLE_BROWSER_SLOTS_PORT_BASE`
- `ORACLE_BROWSER_SLOTS_CDP_START_TIMEOUT`
- `ORACLE_BROWSER_SLOTS_CDP_REQUEST_TIMEOUT`
- `ORACLE_BROWSER_SLOTS_QUEUE_POLL_INTERVAL`
- `ORACLE_BROWSER_SLOTS_ORACLE_CLI` for an explicit absolute-path test binary only

## Slot-wise ChatGPT workspace URLs

Set `ORACLE_BROWSER_SLOTS_CHATGPT_URLS` to a JSON object whose keys are slot IDs
(`"1"` through `"5"`) and whose values are ChatGPT workspace URLs:

```bash
export ORACLE_BROWSER_SLOTS_CHATGPT_URLS='{"3":"https://chatgpt.com/g/g-p-xxxx/project"}'
```

Rules:

- When a mapped slot is selected by `run` or auto-assigned by `submit`, the
  wrapper injects `--chatgpt-url <mapped-url>` into the stock Oracle argv so the
  request runs in that slot's workspace. Unmapped slots keep the exact original
  argv.
- A caller-supplied `--chatgpt-url` or `--browser-url` always wins; the wrapper
  does not inject in that case. The two aliases are one logical option: at most
  one occurrence, no duplicate or cross-alias values, and no empty or option-like
  value.
- `followup` never injects a workspace URL; it resumes the parent conversation.
- `prepare` opens the mapped URL as the initial tab only when Chrome is freshly
  launched for that slot; an existing Chrome session is left unchanged.
- Valid URLs are `https` only, on `chatgpt.com` or `chat.openai.com`, without a
  custom port or credentials. Path and query are preserved.
- Any configuration error fails closed: every command (including `status` and
  `followup`) exits with code 2 and an explanatory error.

The legacy `ORACLE_BROWSER_SLOTS_CHATGPT_URL` remains launcher-only (initial tab
when a slot has no explicit mapping); it is never injected into `run`/`submit`
argv.

The state file is per slot and includes an `occupancy` object with the job ID,
start time, owner PID, and owner process starttime. State transitions use a
per-slot file lock for read/check/write operations; the lock is released before
the child command runs. Automatic submit admission additionally uses one
short-lived allocator lock and an atomic queue file. Queue entries contain the
waiter's PID and Linux process starttime; dead waiters are purged and never
recovered.
