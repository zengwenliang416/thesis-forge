'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  makeFollowupRun
} = require('../kernel/pipeline/production-runner');

const failureId = `failure-${'f'.repeat(64)}`;
const rootRunId = 'run-root';
const rootAttemptId = 'attempt-root';

function testCase(id) {
  return {
    id,
    preconditions: [],
    runner: {},
    steps: [],
    assertions: []
  };
}

function context(overrides = {}) {
  return {
    snapshot: {
      change_id: 'change-successor',
      id: 'snapshot-successor',
      snapshot_hash: 'a'.repeat(64)
    },
    runtimeStatus: {
      runtime_version: '2.0.0-alpha.2'
    },
    codeSha: 'b'.repeat(40),
    testSha: 'c'.repeat(64),
    environmentHash: 'd'.repeat(64),
    kernelVersion: '2.0.0-alpha.2',
    generationId: 'generation-successor',
    parentGenerationId: 'generation-parent',
    ...overrides
  };
}

function repairIdentity(value) {
  return {
    case_snapshot_hash: value.snapshot.snapshot_hash,
    code_sha: value.codeSha,
    test_sha: value.testSha,
    environment_hash: value.environmentHash,
    runtime_version: value.runtimeStatus.runtime_version,
    kernel_version: value.kernelVersion
  };
}

function rootHistory() {
  return {
    runs: [{
      id: rootRunId,
      kind: 'initial',
      change_id: 'change-successor',
      failure_id: null,
      origin_run_id: null,
      parent_run_id: null,
      case_ids: ['case-repaired'],
      generation_id: 'generation-parent'
    }],
    attempts: [{
      id: rootAttemptId,
      run_id: rootRunId,
      case_id: 'case-repaired',
      kind: 'initial',
      sequence: 1
    }],
    failures: [{
      id: failureId,
      change_id: 'change-successor',
      status: 'open',
      run_id: rootRunId,
      case_id: 'case-repaired'
    }]
  };
}

test('retest may bind the direct parent generation root attempt', () => {
  const value = context();
  const result = makeFollowupRun(
    value,
    testCase('case-repaired'),
    '2026-08-27T14:30:00.000Z',
    {
      kind: 'retest',
      parentAttemptId: rootAttemptId,
      failureId,
      repairIdentity: repairIdentity(value)
    },
    rootHistory()
  );

  assert.equal(result.ok, true);
  assert.equal(result.identity.run.generation_id, 'generation-successor');
  assert.equal(result.identity.run.origin_run_id, rootRunId);
  assert.equal(result.identity.run.parent_run_id, rootRunId);
});

test('retest rejects a root outside the direct parent generation', () => {
  const value = context({
    parentGenerationId: 'generation-unrelated'
  });
  const result = makeFollowupRun(
    value,
    testCase('case-repaired'),
    '2026-08-27T14:31:00.000Z',
    {
      kind: 'retest',
      parentAttemptId: rootAttemptId,
      failureId,
      repairIdentity: repairIdentity(value)
    },
    rootHistory()
  );

  assert.equal(result.ok, false);
  assert.equal(
    result.blockers[0].id,
    'verification-production:followup-failure-lineage-invalid'
  );
});

test('regression remains bound to the successor generation retest', () => {
  const value = context();
  const retest = makeFollowupRun(
    value,
    testCase('case-repaired'),
    '2026-08-27T14:32:00.000Z',
    {
      kind: 'retest',
      parentAttemptId: rootAttemptId,
      failureId,
      repairIdentity: repairIdentity(value)
    },
    rootHistory()
  );
  const retestAttempt = {
    ...retest.identity.attempt,
    run_id: retest.identity.run.id,
    case_id: 'case-repaired'
  };
  const history = rootHistory();
  history.runs.push(retest.identity.run);
  history.attempts.push(retestAttempt);

  const result = makeFollowupRun(
    value,
    testCase('case-regression'),
    '2026-08-27T14:33:00.000Z',
    {
      kind: 'regression',
      parentAttemptId: retestAttempt.id,
      failureId,
      repairIdentity: repairIdentity(value)
    },
    history
  );

  assert.equal(result.ok, true);
  assert.equal(result.identity.run.generation_id, 'generation-successor');
  assert.equal(result.identity.run.parent_run_id, retest.identity.run.id);
  assert.equal(result.identity.run.origin_run_id, rootRunId);
});
