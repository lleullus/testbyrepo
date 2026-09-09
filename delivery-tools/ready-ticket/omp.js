import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  BOUNDARY_PROTOCOL,
  captureVerification,
  checkPlanAdmission,
  finalizeVerification,
  inspectAuthority,
  sealVerificationVerdict,
} from "./src/core.js";

const resultText = value => ({ content: [{ type: "text", text: JSON.stringify(value, null, 2) }], details: value });

function bundleIdentityFromModule(options) {
  if (options.bundleIdentity) return options.bundleIdentity;
  if (process.env.IIS_READY_BUNDLE_ID) return process.env.IIS_READY_BUNDLE_ID;
  const bundleRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
  const manifest = path.join(bundleRoot, "bundle.json");
  if (fs.existsSync(manifest)) {
    try { return JSON.parse(fs.readFileSync(manifest, "utf8")).bundle_id ?? "source"; }
    catch { return "source"; }
  }
  return "source";
}

function requiredString(params, name, action) {
  const value = params[name];
  if (typeof value !== "string" || !value.trim()) throw new Error(`${name} is required for ${action}`);
  return value;
}

export function installReadyBoundaryTools(pi, options = {}) {
  const z = pi.zod;
  const bundleIdentity = bundleIdentityFromModule(options);
  const validatorPath = options.validatorPath ?? process.env.IIS_READY_VALIDATOR_PATH;
  const executeArgv = options.executeArgv ?? (async (argv, request = {}) => {
    if (!pi.exec) throw new Error("CAPABILITY_UNAVAILABLE: host structured exec missing");
    const raw = await pi.exec(argv[0], argv.slice(1), {
      cwd: request.cwd,
      signal: request.signal,
      timeout: request.timeout ?? 120000,
    });
    const interrupted = Boolean(raw.killed || request.signal?.aborted);
    return {
      exitCode: raw.code,
      interrupted,
      terminationState: interrupted ? "unknown" : "settled",
      stdout: raw.stdout ?? "",
      stderr: raw.stderr ?? "",
    };
  });
  const provenance = options.provenance ?? new Map();

  pi.registerTool({
    name: "ready_contract",
    loadMode: "essential",
    label: "Ready Contract",
    description: "Stateless Ready authority/admission checks plus immutable verification binding and verdict evidence capture. Does not intercept ordinary host tools.",
    parameters: z.object({
      action: z.enum(["inspect_authority", "check_plan_admission", "capture_verification", "seal_verdict"]),
      project_root: z.string().optional(),
      ticket_path: z.string().optional(),
      plan_review_path: z.string().optional(),
      stable_target_paths: z.array(z.string()).optional(),
      scenario_effect_paths: z.array(z.string()).optional(),
      binding_path: z.string().optional(),
      binding_sha256: z.string().optional(),
      verdict: z.enum(["VERIFIED", "FAILED", "INCONCLUSIVE"]).optional(),
      verdict_path: z.string().optional(),
    }),
    async execute(_callId, params, signal) {
      if (params.action === "seal_verdict") {
        return resultText(sealVerificationVerdict({
          bindingPath: requiredString(params, "binding_path", params.action),
          bindingSha256: requiredString(params, "binding_sha256", params.action),
          verdict: requiredString(params, "verdict", params.action),
          verdictPath: params.verdict_path,
        }));
      }
      const common = {
        projectRoot: requiredString(params, "project_root", params.action),
        ticketPath: requiredString(params, "ticket_path", params.action),
        validatorPath,
        executeArgv: (argv, request = {}) => executeArgv(argv, { ...request, signal: request.signal ?? signal }),
        bundleIdentity,
      };
      let value;
      if (params.action === "inspect_authority") {
        value = await inspectAuthority(common);
      } else if (params.action === "check_plan_admission") {
        value = await checkPlanAdmission({ ...common, planReviewPath: params.plan_review_path });
      } else {
        value = await captureVerification({
          ...common,
          stableTargetPaths: params.stable_target_paths,
          scenarioEffectPaths: params.scenario_effect_paths,
          planReviewPath: params.plan_review_path,
          bindingPath: params.binding_path,
        });
      }
      return resultText(value);
    },
  });

  pi.registerTool({
    name: "ready_finalize",
    loadMode: "essential",
    label: "Ready Finalize",
    description: "Consume an immutable verifier-owned verdict record; only this tool may perform the exact ready-to-done Ticket progression.",
    parameters: z.object({
      verdict_path: z.string(),
      verdict_sha256: z.string(),
    }),
    async execute(_callId, params, signal) {
      const value = await finalizeVerification({
        verdictPath: params.verdict_path,
        verdictSha256: params.verdict_sha256,
        executeArgv: (argv, request = {}) => executeArgv(argv, { ...request, signal: request.signal ?? signal }),
        provenance,
        bundleIdentity,
        boundaryProtocol: BOUNDARY_PROTOCOL,
      });
      if (value.ticket_progression === "COMPLETED" && value.progression_basis === "WRITE_PERFORMED_THIS_CALL") {
        provenance.set(`${params.verdict_path}:${params.verdict_sha256}`, value);
      }
      return resultText(value);
    },
  });

  return { provenance, bundleIdentity, validatorPath };
}

export default function readyTicketBoundaryTools(pi) {
  return installReadyBoundaryTools(pi);
}
