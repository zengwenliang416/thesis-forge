'use strict';

const assert = require('node:assert/strict');

const MODES = new Set(['inspect', 'validate', 'build']);

function runFlow(mode, outcomes = {}) {
  if (!MODES.has(mode)) throw new Error(`Unknown mode: ${mode}`);

  const result = {
    mode,
    status: 'running',
    stages: [],
    diagnostics: [],
    networkRequired: false,
    aiCredentialsRequired: false,
    productionWriteAttempted: false,
    existingOutputPreserved: true,
    outputReplaced: false,
  };

  result.stages.push('parse');
  if (outcomes.parse === 'error') {
    result.status = 'failed';
    result.diagnostics.push('parse-error');
    return result;
  }

  if (mode === 'inspect') {
    result.stages.push('inspect-result');
    result.status = 'succeeded';
    return result;
  }

  result.stages.push('validate');
  if (outcomes.validation === 'error') {
    result.status = 'failed';
    result.diagnostics.push('validation-error');
    return result;
  }
  if (outcomes.validation === 'warning') {
    result.diagnostics.push('validation-warning');
  }

  if (mode === 'validate') {
    result.status = 'succeeded';
    return result;
  }

  result.stages.push('compile');
  if (outcomes.compile === 'error') {
    result.status = 'failed';
    result.diagnostics.push('compile-error');
    return result;
  }

  result.stages.push('render-temporary');
  if (outcomes.render === 'error') {
    result.status = 'failed';
    result.diagnostics.push('render-error');
    return result;
  }

  result.stages.push('validate-package');
  if (outcomes.package === 'error') {
    result.status = 'failed';
    result.diagnostics.push('package-error');
    return result;
  }

  result.stages.push('atomic-replace');
  result.productionWriteAttempted = true;
  result.existingOutputPreserved = false;
  result.outputReplaced = true;
  result.status = 'succeeded';
  return result;
}

function verifyPrototype() {
  const inspect = runFlow('inspect');
  assert.deepEqual(inspect.stages, ['parse', 'inspect-result']);
  assert.equal(inspect.productionWriteAttempted, false);

  const warningValidation = runFlow('validate', { validation: 'warning' });
  assert.equal(warningValidation.status, 'succeeded');
  assert.deepEqual(warningValidation.diagnostics, ['validation-warning']);

  const fatalBuild = runFlow('build', { validation: 'error' });
  assert.deepEqual(fatalBuild.stages, ['parse', 'validate']);
  assert.equal(fatalBuild.productionWriteAttempted, false);
  assert.equal(fatalBuild.existingOutputPreserved, true);

  const successfulBuild = runFlow('build');
  assert.deepEqual(successfulBuild.stages, [
    'parse',
    'validate',
    'compile',
    'render-temporary',
    'validate-package',
    'atomic-replace',
  ]);
  assert.equal(successfulBuild.outputReplaced, true);

  const failedRender = runFlow('build', { render: 'error' });
  assert.equal(failedRender.status, 'failed');
  assert.equal(failedRender.outputReplaced, false);
  assert.equal(failedRender.existingOutputPreserved, true);

  for (const result of [inspect, warningValidation, fatalBuild, successfulBuild, failedRender]) {
    assert.equal(result.networkRequired, false);
    assert.equal(result.aiCredentialsRequired, false);
  }

  return {
    ok: true,
    verifiedCases: [
      'inspect-is-read-only',
      'warning-only-validation-succeeds',
      'fatal-validation-stops-build',
      'successful-build-replaces-output-last',
      'render-failure-preserves-existing-output',
      'core-flows-require-no-network-or-ai-credentials',
    ],
  };
}

module.exports = { runFlow, verifyPrototype };

if (require.main === module) {
  process.stdout.write(`${JSON.stringify(verifyPrototype(), null, 2)}\n`);
}
