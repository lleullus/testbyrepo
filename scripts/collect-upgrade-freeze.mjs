#!/usr/bin/env node

import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = resolve(root, 'html', 'package.json');
const defaultOutputPath = resolve(root, 'docs', 'upgrade', 'dependency-freeze.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const userAgent = 'ttyd-maintenance-upgrade-audit';

let checkOnly = false;
let outputPath = defaultOutputPath;
const args = process.argv.slice(2);
for (let index = 0; index < args.length; index += 1) {
  const arg = args[index];
  if (arg === '--check') {
    checkOnly = true;
  } else if (arg === '--output') {
    const value = args[index + 1];
    if (!value) throw new Error('--output requires a path');
    outputPath = resolve(process.cwd(), value);
    index += 1;
  } else if (arg === '--help') {
    console.log('usage: node scripts/collect-upgrade-freeze.mjs [--check] [--output PATH]');
    process.exit(0);
  } else {
    throw new Error(`unknown argument: ${arg}`);
  }
}

if (checkOnly && outputPath !== defaultOutputPath) {
  throw new Error('--check is read-only and cannot be combined with --output');
}

async function json(url) {
  const response = await fetch(url, {headers: {'User-Agent': userAgent}});
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${url}`);
  }
  return response.json();
}

async function npmVersion(name, version = 'latest') {
  const data = await json(`https://registry.npmjs.org/${encodeURIComponent(name)}/${encodeURIComponent(version)}`);
  return {
    version: data.version,
    engines: data.engines ?? null,
    peerDependencies: data.peerDependencies ?? null,
    deprecated: data.deprecated ?? null,
    integrity: data.dist?.integrity ?? null,
    shasum: data.dist?.shasum ?? null,
    tarball: data.dist?.tarball ?? null,
  };
}

async function githubLatestRelease(repo) {
  try {
    const data = await json(`https://api.github.com/repos/${repo}/releases/latest`);
    return {
      tag: data.tag_name,
      name: data.name,
      publishedAt: data.published_at,
      url: data.html_url,
    };
  } catch (error) {
    return {error: String(error)};
  }
}

async function githubIssue(repo, number) {
  const data = await json(`https://api.github.com/repos/${repo}/issues/${number}`);
  return {
    number,
    title: data.title,
    state: data.state,
    stateReason: data.state_reason ?? null,
    milestone: data.milestone?.title ?? null,
    url: data.html_url,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    closedAt: data.closed_at ?? null,
  };
}

const direct = {
  ...(manifest.dependencies ?? {}),
  ...(manifest.devDependencies ?? {}),
};
const packages = {};
for (const name of Object.keys(direct).sort()) {
  packages[name] = {
    current: direct[name],
    latest: await npmVersion(name),
  };
}

const nodeIndex = await json('https://nodejs.org/dist/index.json');
const activeLts = nodeIndex.find(entry => entry.lts);
const yarn = await npmVersion('@yarnpkg/cli-dist');
const ts6 = await npmVersion('typescript', '6.0.3');
const tsEslintParser = await npmVersion('@typescript-eslint/parser');
const prettier = await npmVersion('prettier');
const xtermRelease = await json('https://api.github.com/repos/xtermjs/xterm.js/releases/tags/6.0.0');
const xtermKnownIssues = await Promise.all([
  githubIssue('xtermjs/xterm.js', 5489),
  githubIssue('xtermjs/xterm.js', 6063),
  githubIssue('xtermjs/xterm.js', 6067),
]);
const lwsTags = await json('https://api.github.com/repos/warmcat/libwebsockets/tags?per_page=20');

const native = {
  zlib: await githubLatestRelease('madler/zlib'),
  jsonC: await githubLatestRelease('json-c/json-c'),
  libuv: await githubLatestRelease('libuv/libuv'),
  mbedTls: await githubLatestRelease('Mbed-TLS/mbedtls'),
  openssl: await githubLatestRelease('openssl/openssl'),
  libwebsockets: {
    latestReleaseApi: await githubLatestRelease('warmcat/libwebsockets'),
    recentTags: lwsTags.map(tag => ({name: tag.name, sha: tag.commit.sha})),
  },
};

const verifiedNativeArchives = {
  zlib132: {
    url: 'https://zlib.net/zlib-1.3.2.tar.gz',
    sha256: 'bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16',
  },
  jsonC019: {
    url: 'https://s3.amazonaws.com/json-c_releases/releases/json-c-0.19.tar.gz',
    sha256: '37ad0249902e301bd9052bf712e511fcc6acff4ecaad4b5900aad9ce564e26de',
  },
  libuv1521: {
    url: 'https://dist.libuv.org/dist/v1.52.1/libuv-v1.52.1.tar.gz',
    sha256: '66d511b9e6e334c0e62279eb234fbfb2b3110b1479c09b95b44c7afca8cff9e7',
  },
  mbedTls367: {
    url: 'https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-3.6.7/mbedtls-3.6.7.tar.bz2',
    sha256: 'a7e8bcbec0e6f761b4af24f25677626b35f762f68eef79c08677a363212d11f6',
  },
  mbedTls420: {
    url: 'https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-4.2.0/mbedtls-4.2.0.tar.bz2',
    sha256: '2bed9d713b4668f76553b097e72b8aa30bc8f112a940d7ae228d524bbde6ffea',
  },
  openssl361: {
    url: 'https://www.openssl.org/source/openssl-3.6.1.tar.gz',
    sha256: 'b1bfedcd5b289ff22aee87c9d600f515767ebf45f77168cb6d64f231f518a82e',
  },
  openssl402: {
    url: 'https://www.openssl.org/source/openssl-4.0.2.tar.gz',
    sha256: '736b467530f916737b7031310ccb21d8218c6229e61e8e160cd1d3458cd543a8',
  },
  libwebsockets457: {
    url: 'https://github.com/warmcat/libwebsockets/archive/refs/tags/v4.5.7.tar.gz',
    sha256: 'd08df7634da0a377a4e077400ed6b2d1d25cf0b239e89397cd39432c5eb437ac',
  },
  libwebsockets458: {
    url: 'https://github.com/warmcat/libwebsockets/archive/refs/tags/v4.5.8.tar.gz',
    sha256: 'b6ade658f4af3a823d0dc806ae5ef0623f0f4f5e2aeb895a0f77c4783840c30e',
  },
  libwebsockets500: {
    url: 'https://github.com/warmcat/libwebsockets/archive/refs/tags/v5.0.0.tar.gz',
    sha256: 'f853c6582101cfcee3a5a9e28ae92ab19d9735c5f31f0bb2e9794b5106123962',
  },
};

const freeze = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  source: {
    head: execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim(),
    packageManifestSha256: createHash('sha256').update(readFileSync(manifestPath)).digest('hex'),
    registry: 'https://registry.npmjs.org/',
    nodeReleaseIndex: 'https://nodejs.org/dist/index.json',
    githubApi: 'https://api.github.com/',
  },
  current: {
    packageManager: manifest.packageManager,
    nodeEngine: manifest.engines?.node ?? null,
    nativePins: {
      zlib: '1.3.2',
      jsonC: '0.19',
      tlsBackend: 'mbedtls',
      mbedTls: '3.6.7',
      libuv: '1.52.1',
      libwebsockets: '4.5.8',
      muslToolchainRelease: '2021-11-23',
    },
    previousNativePins: {
      zlib: '1.3.1',
      jsonC: '0.17',
      tlsBackend: 'mbedtls',
      mbedTls: '2.28.5',
      libuv: '1.44.2',
      libwebsockets: '4.3.3',
      muslToolchainRelease: '2021-11-23',
    },
  },
  toolchainCandidates: {
    nodeActiveLts: activeLts,
    yarnLatest: yarn,
    typescriptLatest: packages.typescript.latest,
    typescriptCompatibleCandidate: ts6,
    typescriptEslintParserLatest: tsEslintParser,
    prettierLatest: prettier,
  },
  xterm6: {
    core: packages['@xterm/xterm'].latest,
    officialReleaseUrl: xtermRelease.html_url,
    releasePublishedAt: xtermRelease.published_at,
    releaseBodySha256: createHash('sha256').update(xtermRelease.body ?? '').digest('hex'),
    canvasRendererRemoved: (xtermRelease.body ?? '').includes('Remove the canvas renderer'),
    viewportImplementationChanged: (xtermRelease.body ?? '').includes('viewport/scroll bar works very differently'),
    knownIssues: xtermKnownIssues,
    packageCandidates: Object.fromEntries(
      Object.entries(packages).filter(([name]) => name.startsWith('@xterm/')),
    ),
  },
  npmPackages: packages,
  nativeCandidates: native,
  verifiedNativeArchives,
  decisions: {
    node: {
      target: manifest.engines?.node ?? null,
      currentOfficialLts: activeLts?.version ?? null,
      status: 'phase7-pinned-phase10-deployed',
      reason: 'The maintained frontend is pinned to the Phase 7 Node 24.20 generation; CI must follow the repository pin rather than an unbounded latest alias.',
    },
    yarn: {
      target: manifest.packageManager,
      registryLatest: yarn.version,
      status: 'phase7-pinned-phase10-deployed',
      reason: 'The repository packageManager field is authoritative and immutable installs must preserve the zmodem patch.',
    },
    typescript: {
      latest: packages.typescript.latest.version,
      targetCandidate: ts6.version,
      status: 'latest-blocked-by-peer-range',
      reason: `@typescript-eslint/parser ${tsEslintParser.version} declares TypeScript >=4.8.4 <6.1.0, so TypeScript ${packages.typescript.latest.version} is not an admissible lint-stack target.`,
    },
    xterm: {
      deployed: manifest.dependencies['@xterm/xterm'],
      registryLatest: packages['@xterm/xterm'].latest.version,
      status: 'phase8-validated-phase10-deployed',
      reason: 'xterm 6.0.0 and its selected addons passed the strengthened browser/mobile/touch/renderer gates and were deployed in Phase 10; future upgrades remain separately gated.',
    },
    canvasAddon: {
      current: manifest.dependencies['@xterm/addon-canvas'] ?? null,
      registryLatest: packages['@xterm/addon-canvas']?.latest.version ?? null,
      status: manifest.dependencies['@xterm/addon-canvas'] ? 'remove-for-xterm6' : 'removed-in-phase8',
      reason: 'xterm.js 6.0.0 removed the legacy canvas renderer; the Phase 8 migration no longer declares @xterm/addon-canvas.',
    },
    native: {
      status: 'phase9-validated-phase10-deployed',
      selected: {
        zlib: '1.3.2',
        jsonC: '0.19',
        libuv: '1.52.1',
        tlsBackend: 'mbedtls',
        mbedTls: '3.6.7',
        libwebsockets: '4.5.8',
      },
      reproducibleBinarySha256: '2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8',
      reason: 'The selected x86_64-musl combination passed the complete native and browser regression suite, reproduced byte-identically, and was deployed in Phase 10. New native versions are drift signals only until separately approved.',
    },
  },
};

const driftSummary = {
  generatedAt: freeze.generatedAt,
  repository: {
    nodeEngine: manifest.engines?.node ?? null,
    packageManager: manifest.packageManager,
    typescript: manifest.devDependencies.typescript,
    eslint: manifest.devDependencies.eslint,
    xterm: manifest.dependencies['@xterm/xterm'],
  },
  registry: {
    nodeActiveLts: activeLts?.version ?? null,
    yarn: yarn.version,
    typescript: packages.typescript.latest.version,
    eslint: packages.eslint.latest.version,
    xterm: packages['@xterm/xterm'].latest.version,
  },
  native: {
    selected: freeze.current.nativePins,
    latestMetadata: {
      zlib: native.zlib.tag ?? native.zlib.error,
      jsonC: native.jsonC.tag ?? native.jsonC.error,
      libuv: native.libuv.tag ?? native.libuv.error,
      mbedTls: native.mbedTls.tag ?? native.mbedTls.error,
      openssl: native.openssl.tag ?? native.openssl.error,
      libwebsocketsRecentTags: native.libwebsockets.recentTags.slice(0, 5).map(tag => tag.name),
    },
  },
  policy: 'Drift is informational. Version changes require a separate compatibility change and the applicable regression gates.',
};

if (checkOnly) {
  console.log(JSON.stringify(driftSummary, null, 2));
} else {
  writeFileSync(outputPath, `${JSON.stringify(freeze, null, 2)}\n`);
  console.log(outputPath);
}
