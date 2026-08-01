#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { diagnoseProject } = require('./index');

function run(argv, output, errorOutput) {
  let showDetails = false;
  let targetDirectory = null;

  for (const argument of argv) {
    if (argument === '--details' || argument === '-d') {
      showDetails = true;
    } else if (argument === '--help' || argument === '-h') {
      output.write('Usage: node-policy-checker [--details] <project-directory>\n');
      return { exitCode: 0 };
    } else if (!targetDirectory) {
      targetDirectory = argument;
    } else {
      errorOutput.write('Usage: node-policy-checker [--details] <project-directory>\n');
      return { exitCode: 2 };
    }
  }

  if (!targetDirectory) {
    errorOutput.write('Usage: node-policy-checker [--details] <project-directory>\n');
    return { exitCode: 2 };
  }

  const result = diagnoseProject(path.resolve(targetDirectory));
  output.write(`${showDetails ? JSON.stringify(result.details, null, 2) : formatSummary(result)}\n`);
  return { exitCode: result.verdict === 'PASS' ? 0 : result.verdict === 'FAIL' ? 1 : 2, result };
}

function formatSummary(result) {
  const risks = result.summary.mainRisks;
  const riskText = risks.length === 0
    ? 'none observed.'
    : risks.map((risk) => risk.message).join(' ');
  return [
    `Verdict: ${result.summary.verdict}`,
    result.summary.observedResponsibility,
    `Main risks: ${riskText}`
  ].join('\n');
}

if (require.main === module) {
  const outcome = run(process.argv.slice(2), process.stdout, process.stderr);
  process.exitCode = outcome.exitCode;
}

module.exports = { run };
