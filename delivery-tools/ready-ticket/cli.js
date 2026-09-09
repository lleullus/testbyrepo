#!/usr/bin/env node
import fs from "node:fs";
import {
  captureVerification,
  checkPlanAdmission,
  currentReadyBundleIdentity,
  executeArgvNode,
  inspectAuthority,
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
    const common = {
      projectRoot: input.project_root,
      ticketPath: input.ticket_path,
      validatorPath: input.validator_path,
      executeArgv: executeArgvNode,
      bundleIdentity: currentReadyBundleIdentity(),
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
    throw new Error("CAPABILITY_UNAVAILABLE: protected finalization requires a host-accepted Ready verifier terminal");
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
