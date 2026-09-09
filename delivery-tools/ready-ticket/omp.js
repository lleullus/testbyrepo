import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  captureVerification,
  checkPlanAdmission,
  finalizeVerification,
  inspectAuthority,
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
    description: "Stateless Ready authority/admission checks and immutable verification binding capture. Does not intercept ordinary host tools.",
    parameters: z.object({
      action: z.enum(["inspect_authority", "check_plan_admission", "capture_verification"]),
      project_root: z.string(),
      ticket_path: z.string(),
      plan_review_path: z.string().optional(),
      stable_target_paths: z.array(z.string()).optional(),
      scenario_effect_paths: z.array(z.string()).optional(),
      binding_path: z.string().optional(),
    }),
    async execute(_callId, params, signal) {
      const common = {
        projectRoot: params.project_root,
        ticketPath: params.ticket_path,
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
    description: "Consume an immutable verification binding and verifier verdict; only this tool may perform the exact ready-to-done Ticket progression.",
    parameters: z.object({
      binding_path: z.string(),
      binding_sha256: z.string(),
      verdict: z.enum(["VERIFIED", "FAILED", "INCONCLUSIVE"]),
    }),
    async execute(_callId, params, signal) {
      const value = await finalizeVerification({
        bindingPath: params.binding_path,
        bindingSha256: params.binding_sha256,
        verdict: params.verdict,
        executeArgv: (argv, request = {}) => executeArgv(argv, { ...request, signal: request.signal ?? signal }),
        provenance,
      });
      if (value.ticket_progression === "COMPLETED" && value.progression_basis === "WRITE_PERFORMED_THIS_CALL") {
        provenance.set(`${params.binding_path}:${params.binding_sha256}`, value);
      }
      return resultText(value);
    },
  });

  return { provenance, bundleIdentity, validatorPath };
}

export default function readyTicketBoundaryTools(pi) {
  return installReadyBoundaryTools(pi);
}
