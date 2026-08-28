#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const {
  initializeCanonicalZeroLineage
} = require('../kernel/pipeline/artifact-pipeline');
const {
  createVerificationArtifactStore
} = require('../kernel/persistence/verification-artifact-store');

function parseArgs(argv) {
  const options = {
    project: process.cwd(),
    change: null,
    json: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--project') options.project = argv[++index];
    else if (value === '--change') options.change = argv[++index];
    else if (value === '--json') options.json = true;
    else throw new Error(`zero-lineage:unknown-argument:${value}`);
  }
  if (!options.change) throw new Error('zero-lineage:change-required');
  return options;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function readJsonl(file) {
  return fs.readFileSync(file, 'utf8')
    .split(/\r?\n/)
    .filter((line) => line.trim() !== '')
    .map((line) => JSON.parse(line));
}

function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const projectRoot = fs.realpathSync(path.resolve(options.project));
  const changeRoot = path.join(
    projectRoot,
    'openspec',
    'changes',
    options.change
  );
  const verificationRoot = path.join(changeRoot, 'verify');
  const gateInput = readJson(path.join(verificationRoot, 'v2', 'gate-input.json'));
  const generations = readJsonl(
    path.join(verificationRoot, 'v2', 'generations.jsonl')
  );
  const activeGeneration = generations.findLast((entry) => (
    entry.id === gateInput.generation_id
  ));
  if (!activeGeneration) {
    throw new Error('zero-lineage:active-generation-missing');
  }
  if (gateInput.change_id !== options.change) {
    throw new Error('zero-lineage:change-mismatch');
  }

  const store = createVerificationArtifactStore({
    changeRoot,
    root: verificationRoot
  });
  const result = initializeCanonicalZeroLineage(store, {
    changeId: options.change,
    currentFingerprints: activeGeneration.fingerprints
  });
  const output = {
    ok: result.ok,
    status: result.status,
    change_id: options.change,
    generation_id: activeGeneration.id,
    initialized: result.initialized,
    preserved: result.preserved,
    blockers: result.blockers,
    fallback_used: false
  };
  process.stdout.write(
    options.json
      ? `${JSON.stringify(output, null, 2)}\n`
      : `${output.status}: ${options.change}\n`
  );
  if (!result.ok) process.exitCode = 1;
  return output;
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

module.exports = {
  main,
  parseArgs
};
