'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  selectFailureStateLineage
} = require('../kernel/pipeline/artifact-pipeline');

test('failure state retains successor lineage without widening aggregation', () => {
  const rootFailureId = `failure-${'a'.repeat(64)}`;
  const currentFailureId = `failure-${'b'.repeat(64)}`;
  const unrelatedFailureId = `failure-${'c'.repeat(64)}`;
  const runs = [
    {
      id: 'run-root',
      kind: 'initial',
      generation_id: 'generation-parent',
      failure_id: null,
      origin_run_id: null,
      parent_run_id: null
    },
    {
      id: 'run-retest',
      kind: 'retest',
      generation_id: 'generation-successor',
      failure_id: rootFailureId,
      origin_run_id: 'run-root',
      parent_run_id: 'run-root'
    },
    {
      id: 'run-regression',
      kind: 'regression',
      generation_id: 'generation-successor',
      failure_id: rootFailureId,
      origin_run_id: 'run-root',
      parent_run_id: 'run-retest'
    },
    {
      id: 'run-current-initial',
      kind: 'initial',
      generation_id: 'generation-successor',
      failure_id: null,
      origin_run_id: null,
      parent_run_id: null
    },
    {
      id: 'run-unrelated',
      kind: 'initial',
      generation_id: 'generation-unrelated',
      failure_id: null,
      origin_run_id: null,
      parent_run_id: null
    }
  ];
  const failures = [
    {
      id: rootFailureId,
      run_id: 'run-root'
    },
    {
      id: currentFailureId,
      run_id: 'run-current-initial'
    },
    {
      id: unrelatedFailureId,
      run_id: 'run-unrelated'
    }
  ];
  const repairLinks = [
    {
      id: 'repair-root',
      failure_id: rootFailureId
    },
    {
      id: 'repair-current',
      failure_id: currentFailureId
    },
    {
      id: 'repair-unrelated',
      failure_id: unrelatedFailureId
    }
  ];

  const result = selectFailureStateLineage(
    runs,
    failures,
    repairLinks,
    new Set([
      'run-retest',
      'run-regression',
      'run-current-initial'
    ])
  );

  assert.deepEqual(
    result.runs.map((entry) => entry.id),
    [
      'run-root',
      'run-retest',
      'run-regression',
      'run-current-initial'
    ]
  );
  assert.deepEqual(
    result.failures.map((entry) => entry.id),
    [rootFailureId, currentFailureId]
  );
  assert.deepEqual(
    result.repair_links.map((entry) => entry.id),
    ['repair-root', 'repair-current']
  );
  assert.deepEqual(
    [...result.failure_ids],
    [rootFailureId, currentFailureId]
  );
});

test('failure state follows parent chains across multiple generations', () => {
  const failureId = `failure-${'d'.repeat(64)}`;
  const runs = [
    {
      id: 'run-root',
      kind: 'initial',
      failure_id: null,
      origin_run_id: null,
      parent_run_id: null
    },
    {
      id: 'run-prior-retest',
      kind: 'retest',
      failure_id: failureId,
      origin_run_id: 'run-root',
      parent_run_id: 'run-root'
    },
    {
      id: 'run-current-regression',
      kind: 'regression',
      failure_id: failureId,
      origin_run_id: 'run-root',
      parent_run_id: 'run-prior-retest'
    }
  ];

  const result = selectFailureStateLineage(
    runs,
    [{ id: failureId, run_id: 'run-root' }],
    [],
    new Set(['run-current-regression'])
  );

  assert.deepEqual(
    result.runs.map((entry) => entry.id),
    ['run-root', 'run-prior-retest', 'run-current-regression']
  );
  assert.deepEqual(
    result.failures.map((entry) => entry.id),
    [failureId]
  );
});
