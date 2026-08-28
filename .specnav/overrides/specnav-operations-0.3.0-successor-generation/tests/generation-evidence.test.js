'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  selectGenerationEvidence
} = require('../scripts/generation-evidence');

function evidence(id, capturedAt) {
  return {
    schema: 'specnav.verification.evidence.v1',
    id,
    change_id: 'docforge-project-format-v1',
    run_id: `run-${id}`,
    captured_at: capturedAt
  };
}

test('selects current generation evidence while preserving historical index', () => {
  const currentA = evidence('evidence-current-a', '2026-08-28T01:00:00Z');
  const currentB = evidence('evidence-current-b', '2026-08-28T02:00:00Z');
  const historical = evidence('evidence-historical', '2026-08-27T01:00:00Z');
  const result = selectGenerationEvidence({
    change_id: 'docforge-project-format-v1',
    entries: [historical, currentB, currentA]
  }, {
    evidence_index_version: 2,
    aggregation_request: {
      evidence: [currentB, currentA]
    }
  });

  assert.equal(result.ok, true);
  assert.deepEqual(
    result.scoped.entries.map((entry) => entry.id),
    ['evidence-current-a', 'evidence-current-b']
  );
  assert.equal(result.scoped.record_count, 2);
  assert.equal(result.scoped.index_version, 2);
  assert.match(result.scoped.source_digest, /^[a-f0-9]{64}$/);
});

test('rejects forged or missing generation evidence', () => {
  const current = evidence('evidence-current', '2026-08-28T01:00:00Z');
  const forged = { ...current, run_id: 'run-forged' };
  const result = selectGenerationEvidence({
    change_id: 'docforge-project-format-v1',
    entries: [current]
  }, {
    evidence_index_version: 1,
    aggregation_request: {
      evidence: [forged]
    }
  });

  assert.equal(result.ok, false);
});
