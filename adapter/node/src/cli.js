#!/usr/bin/env node
'use strict';

const path = require('node:path');
const { admitChange, diagnoseProject } = require('./index');

function run(argv, output, errorOutput) {
  if (argv[0] === 'admit') {
    return runAdmission(argv.slice(1), output, errorOutput);
  }
  return runDiagnosis(argv, output, errorOutput);
}

function runDiagnosis(argv, output, errorOutput) {
  let showDetails = false;
  let targetDirectory = null;

  for (const argument of argv) {
    if (argument === '--details' || argument === '-d') {
      showDetails = true;
    } else if (argument === '--help' || argument === '-h') {
      output.write(diagnosisUsage());
      return { exitCode: 0 };
    } else if (!targetDirectory) {
      targetDirectory = argument;
    } else {
      errorOutput.write(diagnosisUsage());
      return { exitCode: 2 };
    }
  }

  if (!targetDirectory) {
    errorOutput.write(diagnosisUsage());
    return { exitCode: 2 };
  }

  const result = diagnoseProject(path.resolve(targetDirectory));
  output.write(`${showDetails ? JSON.stringify(result.details, null, 2) : formatDiagnosisSummary(result)}\n`);
  return { exitCode: exitCodeFor(result.verdict), result };
}

function runAdmission(argv, output, errorOutput) {
  let showDetails = false;
  let targetDirectory = null;
  let request = null;

  for (const argument of argv) {
    if (argument === '--details' || argument === '-d') {
      showDetails = true;
    } else if (argument === '--help' || argument === '-h') {
      output.write(admissionUsage());
      return { exitCode: 0 };
    } else if (!targetDirectory) {
      targetDirectory = argument;
    } else if (request === null) {
      request = argument;
    } else {
      errorOutput.write(admissionUsage());
      return { exitCode: 2 };
    }
  }

  if (!targetDirectory || request === null) {
    errorOutput.write(admissionUsage());
    return { exitCode: 2 };
  }

  const result = admitChange({ projectDirectory: path.resolve(targetDirectory), request });
  output.write(`${showDetails ? JSON.stringify(result.details, null, 2) : formatAdmissionSummary(result)}\n`);
  return { exitCode: exitCodeFor(result.verdict), result };
}

function formatDiagnosisSummary(result) {
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

function formatAdmissionSummary(result) {
  const risks = result.summary.mainRisks;
  const responsibility = result.summary.selectedResponsibility;
  const responsibilityText = responsibility
    ? `${responsibility.ownerPath} (${responsibility.responsibility})`
    : 'none established.';
  const riskText = risks.length === 0
    ? 'none observed.'
    : risks.map((risk) => risk.message).join(' ');
  const lines = [
    `Verdict: ${result.summary.verdict}`,
    `Selected change responsibility: ${responsibilityText}`,
    `Main risks: ${riskText}`
  ];

  if (result.questions.length > 0) {
    lines.push('Unresolved nontechnical questions:');
    lines.push(...result.questions.map((question) => `- ${question}`));
  }
  return lines.join('\n');
}

function exitCodeFor(verdict) {
  return verdict === 'PASS' ? 0 : verdict === 'FAIL' ? 1 : 2;
}

function diagnosisUsage() {
  return 'Usage: node-policy-checker [--details] <project-directory>\n';
}

function admissionUsage() {
  return 'Usage: node-policy-checker admit [--details] <project-directory> "<request>"\n';
}

if (require.main === module) {
  const outcome = run(process.argv.slice(2), process.stdout, process.stderr);
  process.exitCode = outcome.exitCode;
}

module.exports = { run };
