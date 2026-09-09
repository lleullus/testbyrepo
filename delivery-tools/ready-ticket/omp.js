import {
  currentReadyBundleIdentity,
  BOUNDARY_PROTOCOL,
  captureVerification,
  checkPlanAdmission,
  finalizeVerification,
  inspectAuthority,
} from "./src/core.js";

const resultText = value => ({ content: [{ type: "text", text: JSON.stringify(value, null, 2) }], details: value });


function requiredString(params, name, action) {
  const value = params[name];
  if (typeof value !== "string" || !value.trim()) throw new Error(`${name} is required for ${action}`);
  return value;
}

export function installReadyBoundaryTools(pi, options = {}) {
  const z = pi.zod;
  const bundleIdentity = currentReadyBundleIdentity();
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

  pi.registerTool({
    name: "ready_contract",
    loadMode: "essential",
    label: "Ready Contract",
    description: "Stateless Ready authority/admission checks plus immutable verification binding capture. Does not intercept ordinary host tools.",
    parameters: z.object({
      action: z.enum(["inspect_authority", "check_plan_admission", "capture_verification"]),
      project_root: z.string().optional(),
      ticket_path: z.string().optional(),
      plan_review_path: z.string().optional(),
      stable_target_paths: z.array(z.string()).optional(),
      scenario_effect_paths: z.array(z.string()).optional(),
      binding_path: z.string().optional(),
    }),
    async execute(_callId, params, signal) {
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
    description: "Consume one host-accepted Ready verifier terminal; only this tool may perform the exact ready-to-done Ticket progression.",
    parameters: z.object({
      terminal_handle: z.string(),
    }),
    async execute(_callId, params, signal, _onUpdate, ctx) {
      const previous = pi.pi.resolveReadyVerifierFinalization(params.terminal_handle, ctx.agentId, ctx.sessionId);
      if (previous) return resultText(previous);
      const terminal = pi.pi.resolveReadyVerifierTerminal(params.terminal_handle, ctx.agentId, ctx.sessionId);
      const value = await finalizeVerification({
        verdictRecordPath: options.verdictRecordPath?.() ?? pi.pi.readyVerifierVerdictRecordPath(params.terminal_handle, ctx.agentId, ctx.sessionId),
        acceptedTerminal: terminal,
        executeArgv: (argv, request = {}) => executeArgv(argv, { ...request, signal: request.signal ?? signal }),
        bundleIdentity,
        boundaryProtocol: BOUNDARY_PROTOCOL,
        recordResult: result => pi.pi.recordReadyVerifierFinalization(
          params.terminal_handle,
          ctx.agentId,
          ctx.sessionId,
          result,
        ),
      });
      return resultText(value);
    },
  });
  pi.on("session_shutdown", (_event, ctx) => {
    pi.pi.releaseReadyVerifierTerminalsForSession(ctx.agentId, ctx.sessionId);
  });


  return { bundleIdentity, validatorPath };
}

export default function readyTicketBoundaryTools(pi) {
  return installReadyBoundaryTools(pi);
}
