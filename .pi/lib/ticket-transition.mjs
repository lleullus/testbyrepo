import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { promisify } from "node:util";

const executeFile = promisify(execFile);

export function ticketSha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

async function validate(validator, ticket) {
  const result = await executeFile("python3", [validator, ticket], {
    encoding: "utf8",
    maxBuffer: 1024 * 1024,
  });
  if (result.stdout.trim() !== "VALID") {
    throw new Error(result.stderr.trim() || result.stdout.trim() || "canonical Ticket validator failed");
  }
}

export async function markTicketDone({ ticket, validator, expectedSha256, signal }) {
  signal?.throwIfAborted();
  const before = await readFile(ticket, "utf8");
  const beforeSha256 = ticketSha256(before);
  if (beforeSha256 !== expectedSha256) throw new Error("Ticket changed before guarded done transition");

  await validate(validator, ticket);
  const readyMatches = before.match(/^Status: ready$/gm) ?? [];
  if (readyMatches.length !== 1) throw new Error(`expected exactly one Status: ready line; found ${readyMatches.length}`);
  const after = before.replace(/^Status: ready$/m, "Status: done");

  signal?.throwIfAborted();
  await writeFile(ticket, after, "utf8");
  try {
    await validate(validator, ticket);
    const persisted = await readFile(ticket, "utf8");
    if (persisted !== after) throw new Error("Ticket changed during post-transition validation");
  } catch (error) {
    const current = await readFile(ticket, "utf8");
    let rollback = "not attempted because the Ticket changed concurrently";
    if (current === after) {
      await writeFile(ticket, before, "utf8");
      rollback = "restored the exact pre-transition content";
    }
    throw new Error(
      `post-transition validation failed; rollback ${rollback}: ${error instanceof Error ? error.message : String(error)}`,
    );
  }

  return {
    ticket,
    beforeSha256,
    afterSha256: ticketSha256(after),
    status: "done",
  };
}
