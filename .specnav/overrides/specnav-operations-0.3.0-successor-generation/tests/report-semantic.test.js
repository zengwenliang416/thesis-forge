'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  sameReportSemantics
} = require('../scripts/report-semantic');

function report(generatedAt, evidenceId = 'evidence-current') {
  return {
    schema: 'specnav.verification.report-model.v1',
    id: 'report-model-stable',
    generated_at: generatedAt,
    change_id: 'docforge-project-format-v1',
    verdict: 'green',
    sources: {
      evidence_ids: [evidenceId]
    },
    summary: {
      open_failure_ids: []
    },
    catalog: [],
    results: [],
    blockers: [],
    warnings: []
  };
}

test('ignores generated_at while comparing canonical report semantics', () => {
  assert.equal(sameReportSemantics(
    report('2026-08-28T01:00:00.000Z'),
    report('2026-08-28T01:00:00.100Z')
  ), true);
});

test('rejects canonical report source drift', () => {
  assert.equal(sameReportSemantics(
    report('2026-08-28T01:00:00.000Z'),
    report('2026-08-28T01:00:00.000Z', 'evidence-forged')
  ), false);
});
