import { execFile } from "node:child_process";
import { readFile, realpath, stat } from "node:fs/promises";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { promisify } from "node:util";

const executeFile = promisify(execFile);

async function requireFile(path, label) {
  const canonical = await realpath(path);
  if (!(await stat(canonical)).isFile()) throw new Error(`${label} is not a file: ${canonical}`);
  return canonical;
}

async function requireDirectory(path, label) {
  const canonical = await realpath(path);
  if (!(await stat(canonical)).isDirectory()) throw new Error(`${label} is not a directory: ${canonical}`);
  return canonical;
}

export async function resolveCanonicalValidator(iisSkillsRoot) {
  const router = await requireFile(resolve(iisSkillsRoot, "iis-workflow/SKILL.md"), "IIS workflow router");
  const source = await readFile(router, "utf8");
  const marker = "### To Tickets";
  const start = source.indexOf(marker);
  if (start < 0) throw new Error("canonical IIS router has no To Tickets route");
  const remainder = source.slice(start + marker.length);
  const nextRoute = remainder.search(/^###\s+/m);
  const section = nextRoute < 0 ? remainder : remainder.slice(0, nextRoute);
  const target = section.match(/`([^`\n]+\/SKILL\.md)`/)?.[1];
  if (!target) throw new Error("canonical To Tickets route target is unresolved");
  const skillPath = await requireFile(isAbsolute(target) ? target : resolve(dirname(router), target), "To Tickets skill");
  return requireFile(join(dirname(skillPath), "validate_ticket.py"), "canonical Ticket validator");
}

async function validateTicket(validator, ticket) {
  try {
    const result = await executeFile("python3", [validator, ticket], {
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    });
    const stdout = result.stdout.trim();
    if (stdout !== "VALID") return { valid: false, result: stdout || "validator returned no result" };
    return { valid: true, result: "VALID" };
  } catch (error) {
    const stderr = typeof error?.stderr === "string" ? error.stderr.trim() : "";
    const stdout = typeof error?.stdout === "string" ? error.stdout.trim() : "";
    return { valid: false, result: stderr || stdout || (error instanceof Error ? error.message : String(error)) };
  }
}

function ticketStatus(content) {
  const matches = [...content.matchAll(/^Status:\s*(draft|ready|blocked|done)\s*$/gm)];
  if (matches.length !== 1) throw new Error(`Ticket top status is ambiguous: found ${matches.length}`);
  return matches[0][1];
}

export async function runTicketPreflight({ iisSkillsRoot, ticket, projectRoot, mode, diagnosticReverify = false }) {
  const validator = await resolveCanonicalValidator(iisSkillsRoot);
  const canonicalTicket = await requireFile(ticket, "canonical Ticket");
  const validation = await validateTicket(validator, canonicalTicket);
  if (!validation.valid) {
    return {
      proceed: false,
      validator,
      validatorResult: validation.result,
      workflow:
        mode === "IMPLEMENT"
          ? { completion: "BLOCKED", reason: `CANONICAL TICKET INVALID: ${validation.result}` }
          : { status: "NOT_STARTED", reason: `CANONICAL TICKET INVALID: ${validation.result}` },
      output:
        mode === "IMPLEMENT"
          ? `IMPLEMENT NOT STARTED\nTicket: ${canonicalTicket}\nReason: CANONICAL TICKET INVALID: ${validation.result}`
          : `VERIFICATION NOT STARTED\nTicket: ${canonicalTicket}\nReason: CANONICAL TICKET INVALID: ${validation.result}\nAC verdicts: Not issued`,
    };
  }

  const content = await readFile(canonicalTicket, "utf8");
  const status = ticketStatus(content);
  const projectRootMatches = [...content.matchAll(/^Project-Root:\s*(.+?)\s*$/gm)];
  if (projectRootMatches.length !== 1) throw new Error(`Ticket Project-Root is ambiguous: found ${projectRootMatches.length}`);
  const canonicalProjectRoot = await requireDirectory(projectRoot, "invocation Project Root");
  const ticketProjectRoot = await requireDirectory(projectRootMatches[0][1], "Ticket Project-Root");
  if (canonicalProjectRoot !== ticketProjectRoot) {
    const reason = `PROJECT ROOT MISMATCH: Ticket names ${ticketProjectRoot}; invocation names ${canonicalProjectRoot}`;
    return {
      proceed: false,
      validator,
      validatorResult: "VALID",
      status,
      workflow: mode === "IMPLEMENT" ? { completion: "BLOCKED", reason } : { status: "NOT_STARTED", reason },
      output:
        mode === "IMPLEMENT"
          ? `IMPLEMENT NOT STARTED\nTicket: ${canonicalTicket}\nReason: ${reason}`
          : `VERIFICATION NOT STARTED\nTicket: ${canonicalTicket}\nReason: ${reason}\nAC verdicts: Not issued`,
    };
  }
  if (mode === "IMPLEMENT" && status !== "ready") {
    return {
      proceed: false,
      validator,
      validatorResult: "VALID",
      status,
      workflow: { completion: "BLOCKED", reason: `IMPLEMENT requires Status: ready; observed ${status}` },
      output: `IMPLEMENT NOT STARTED\nTicket: ${ticket}\nReason: IMPLEMENT requires Status: ready; observed ${status}`,
    };
  }
  if (mode === "VERIFY" && status !== "ready" && !(status === "done" && diagnosticReverify)) {
    return {
      proceed: false,
      validator,
      validatorResult: "VALID",
      status,
      workflow: { status: "NOT_STARTED", reason: `verification status gate rejected ${status}` },
      output: `VERIFICATION NOT STARTED\nTicket: ${ticket}\nReason: verification status gate rejected ${status}\nAC verdicts: Not issued`,
    };
  }

  return { proceed: true, validator, validatorResult: "VALID", status, ticket: canonicalTicket, projectRoot: canonicalProjectRoot };
}
