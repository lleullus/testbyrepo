'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const REGISTRY_ENV = 'NODE_POLICY_CHECKER_REVIEWER_REGISTRY';
const REGISTRY_STATE = captureRegistry();

function resolveHostReviewerTransport(reviewer, projectRoot) {
  if (REGISTRY_STATE.error) {
    return { error: REGISTRY_STATE.error, reviewer: null };
  }
  const targetProblem = registryTargetProblem(projectRoot);
  if (targetProblem) {
    return { error: targetProblem, reviewer: null };
  }
  if (!validReviewerTransport(reviewer)) {
    return { error: 'No complete AI reviewer execution transport was supplied before admission.', reviewer: null };
  }

  const trusted = REGISTRY_STATE.reviewers.get(`${reviewer.id}\u0000${reviewer.model}`);
  if (!trusted) {
    return { error: 'The reviewer identity and model are not present in the host reviewer registry.', reviewer: null };
  }

  let suppliedKey;
  try {
    suppliedKey = crypto.createPublicKey(reviewer.publicKey);
  } catch (error) {
    return { error: `The reviewer transport public key is invalid: ${error.message}`, reviewer: null };
  }
  const suppliedDer = suppliedKey.export({ format: 'der', type: 'spki' });
  if (trusted.publicKeyDer.length !== suppliedDer.length || !crypto.timingSafeEqual(trusted.publicKeyDer, suppliedDer)) {
    return { error: 'The reviewer transport public key does not match the host reviewer registry.', reviewer: null };
  }

  const review = reviewer.review;
  return {
    error: null,
    reviewer: Object.freeze({
      id: trusted.id,
      kind: 'ai-semantic-reviewer',
      model: trusted.model,
      publicKey: crypto.createPublicKey({ key: trusted.publicKeyDer, format: 'der', type: 'spki' }),
      review(request) {
        return Reflect.apply(review, undefined, [request]);
      }
    })
  };
}

function captureRegistry() {
  const configuredPath = process.env[REGISTRY_ENV];
  if (!nonEmptyText(configuredPath)) {
    return registryFailure(`${REGISTRY_ENV} must identify the host reviewer registry before this module is loaded.`);
  }
  if (!path.isAbsolute(configuredPath) || path.normalize(configuredPath) !== configuredPath) {
    return registryFailure(`${REGISTRY_ENV} must be a canonical absolute file path.`);
  }

  let document;
  let identity;
  let canonicalPath;
  let descriptor = null;
  try {
    const pathMetadata = fs.lstatSync(configuredPath);
    canonicalPath = fs.realpathSync(configuredPath);
    if (!pathMetadata.isFile() || pathMetadata.isSymbolicLink() || canonicalPath !== configuredPath) {
      return registryFailure('The host reviewer registry must be a canonical, non-symlink regular file.');
    }
    descriptor = fs.openSync(configuredPath, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    const metadata = fs.fstatSync(descriptor);
    if (!metadata.isFile() || metadata.dev !== pathMetadata.dev || metadata.ino !== pathMetadata.ino) {
      return registryFailure('The host reviewer registry identity changed while it was being captured.');
    }
    if ((metadata.mode & 0o022) !== 0) {
      return registryFailure('The host reviewer registry must not be group- or world-writable.');
    }
    identity = Object.freeze({
      dev: metadata.dev,
      gid: metadata.gid,
      ino: metadata.ino,
      mode: metadata.mode,
      size: metadata.size,
      uid: metadata.uid
    });
    document = JSON.parse(fs.readFileSync(descriptor, 'utf8'));
  } catch (error) {
    return registryFailure(`The host reviewer registry could not be captured: ${error.message}`);
  } finally {
    if (descriptor !== null) {
      fs.closeSync(descriptor);
    }
  }

  if (!isPlainObject(document) || document.kind !== 'node-policy-checker-reviewer-registry' || !Array.isArray(document.reviewers)) {
    return registryFailure('The host reviewer registry has an invalid document contract.');
  }

  const reviewers = new Map();
  for (const [index, reviewer] of document.reviewers.entries()) {
    if (!isPlainObject(reviewer) || !nonEmptyText(reviewer.id) || !nonEmptyText(reviewer.model) || !nonEmptyText(reviewer.publicKey)) {
      return registryFailure(`Host reviewer registry entry ${index} is malformed.`);
    }
    const key = `${reviewer.id}\u0000${reviewer.model}`;
    if (reviewers.has(key)) {
      return registryFailure(`Host reviewer registry entry ${index} duplicates an identity and model.`);
    }
    let publicKey;
    try {
      publicKey = crypto.createPublicKey(reviewer.publicKey);
      if (publicKey.asymmetricKeyType !== 'ed25519') {
        throw new TypeError('Only Ed25519 reviewer keys are supported.');
      }
    } catch (error) {
      return registryFailure(`Host reviewer registry entry ${index} has an invalid public key: ${error.message}`);
    }
    reviewers.set(key, Object.freeze({
      id: reviewer.id,
      model: reviewer.model,
      publicKey,
      publicKeyDer: publicKey.export({ format: 'der', type: 'spki' })
    }));
  }
  return Object.freeze({ canonicalPath, error: null, identity, reviewers });
}

function registryFailure(error) {
  return Object.freeze({ canonicalPath: null, error, identity: null, reviewers: new Map() });
}

function registryTargetProblem(projectRoot) {
  if (!nonEmptyText(projectRoot)) {
    return 'The target project root is unavailable for host registry isolation.';
  }
  let canonicalRoot;
  try {
    canonicalRoot = fs.realpathSync(projectRoot);
    if (!fs.statSync(canonicalRoot).isDirectory()) {
      return 'The target project root is not a readable directory.';
    }
  } catch (error) {
    return `The target project root could not be canonicalized for host registry isolation: ${error.message}`;
  }
  const relative = path.relative(canonicalRoot, REGISTRY_STATE.canonicalPath);
  if (relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative))) {
    return 'The host reviewer registry must be outside the canonical target project root.';
  }
  return null;
}

function validReviewerTransport(value) {
  return isPlainObject(value) &&
    value.kind === 'ai-semantic-reviewer' &&
    nonEmptyText(value.id) &&
    nonEmptyText(value.model) &&
    nonEmptyText(value.publicKey) &&
    typeof value.review === 'function';
}

function nonEmptyText(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

module.exports = { resolveHostReviewerTransport };
