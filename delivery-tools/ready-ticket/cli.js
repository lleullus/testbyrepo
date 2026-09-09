#!/usr/bin/env node
import fs from "node:fs";
import {
  BOUNDARY_PROTOCOL,
  captureVerification,
  checkPlanAdmission,
  executeArgvNode,
  finalizeVerification,
  inspectAuthority,
  sealVerificationVerdict,
} from "./src/core.js";

function readPayload(argument) {
  const text = argument ?? fs.readFileSync(0, "utf8");
  if (!text.trim()) throw new Error("JSON input is required as argv[3] or stdin");
  return JSON.parse(text);
}

async function main() {
  const [surface, payloadArgument] = process.argv.slice(2);
  const input = readPayload(payloadArgument);
  if (surface === "ready_contract") {
    if (input.action === "seal_verdict") {
      return sealVerificationVerdict({
        bindingPath: input.binding_path,
        bindingSha256: input.binding_sha256,
        verdict: input.verdict,
        verdictPath: input.verdict_path,
      });
    }
    const common = {
      projectRoot: input.project_root,
      ticketPath: input.ticket_path,
      validatorPath: input.validator_path,
      executeArgv: executeArgvNode,
      bundleIdentity: input.bundle_identity ?? process.env.IIS_READY_BUNDLE_ID ?? "source",
    };
    if (input.action === "inspect_authority") return inspectAuthority(common);
    if (input.action === "check_plan_admission") return checkPlanAdmission({ ...common, planReviewPath: input.plan_review_path });
    if (input.action === "capture_verification") {
      return captureVerification({
        ...common,
        stableTargetPaths: input.stable_target_paths,
        scenarioEffectPaths: input.scenario_effect_paths,
        planReviewPath: input.plan_review_path,
        bindingPath: input.binding_path,
      });
    }
    throw new Error(`unknown ready_contract action: ${input.action}`);
  }
  if (surface === "ready_finalize") {
    return finalizeVerification({
      verdictPath: input.verdict_path,
      verdictSha256: input.verdict_sha256,
      executeArgv: executeArgvNode,
      bundleIdentity: input.bundle_identity ?? process.env.IIS_READY_BUNDLE_ID ?? "source",
      boundaryProtocol: BOUNDARY_PROTOCOL,
    });
  }
  throw new Error("surface must be ready_contract or ready_finalize");
}

try {
  const value = await main();
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
} catch (error) {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 1;
}
