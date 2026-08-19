import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { markTicketDone, ticketSha256 } from "../.pi/lib/ticket-transition.mjs";

const ACCEPT_VALIDATOR = `
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
statuses = [line for line in text.splitlines() if line.startswith("Status: ")]
if len(statuses) == 1 and statuses[0] in {"Status: ready", "Status: done"}:
    print("VALID")
    raise SystemExit(0)
print("INVALID", file=sys.stderr)
raise SystemExit(1)
`;

const REJECT_DONE_VALIDATOR = `
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
if "Status: ready" in text and "Status: done" not in text:
    print("VALID")
    raise SystemExit(0)
print("DONE REJECTED", file=sys.stderr)
raise SystemExit(1)
`;

async function fixture(validatorSource = ACCEPT_VALIDATOR) {
  const root = await mkdtemp(join(tmpdir(), "iis-ticket-transition-"));
  const ticket = join(root, "TICKET-001.md");
  const validator = join(root, "validator.py");
  const content = "# Ticket\n\nStatus: ready\n\n## Scope\n\nExact scope\n";
  await Promise.all([writeFile(ticket, content, "utf8"), writeFile(validator, validatorSource, "utf8")]);
  return { root, ticket, validator, content };
}

test("markTicketDone changes only the exact ready status after hash and validator checks", async () => {
  const data = await fixture();
  try {
    const result = await markTicketDone({
      ticket: data.ticket,
      validator: data.validator,
      expectedSha256: ticketSha256(data.content),
    });
    const after = await readFile(data.ticket, "utf8");
    assert.equal(after, data.content.replace("Status: ready", "Status: done"));
    assert.equal(result.beforeSha256, ticketSha256(data.content));
    assert.equal(result.afterSha256, ticketSha256(after));
    assert.equal(result.status, "done");
  } finally {
    await rm(data.root, { recursive: true, force: true });
  }
});

test("markTicketDone rejects a stale expected hash without mutation", async () => {
  const data = await fixture();
  try {
    await assert.rejects(
      markTicketDone({ ticket: data.ticket, validator: data.validator, expectedSha256: "0".repeat(64) }),
      /Ticket changed before guarded done transition/,
    );
    assert.equal(await readFile(data.ticket, "utf8"), data.content);
  } finally {
    await rm(data.root, { recursive: true, force: true });
  }
});

test("markTicketDone restores exact content when post-transition validation fails", async () => {
  const data = await fixture(REJECT_DONE_VALIDATOR);
  try {
    await assert.rejects(
      markTicketDone({
        ticket: data.ticket,
        validator: data.validator,
        expectedSha256: ticketSha256(data.content),
      }),
      /rollback restored the exact pre-transition content/,
    );
    assert.equal(await readFile(data.ticket, "utf8"), data.content);
  } finally {
    await rm(data.root, { recursive: true, force: true });
  }
});
