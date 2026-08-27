'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const sourceProject = path.resolve(__dirname, '../../../..');
const changeId = 'docforge-project-format-v1';
const failureId =
  'failure-046667276b7162f8e5ff3393bf25487fc05b2ab68270ff9e12f6f1a9c8656ee5';
const runtimeRoot = path.join(
  sourceProject,
  '.specnav/runtime/verification/2.0.0-alpha.2'
);
process.env.SPECNAV_MARKETPLACE_ROOT = path.join(
  process.env.CODEX_HOME || path.join(os.homedir(), '.codex'),
  'plugins/cache/specnav-marketplace'
);

const kernel = require('../kernel');
const {
  canonicalJson,
  sha256
} = require('../kernel/evidence/identity');
const {
  createTrustedFactAuthority
} = require('../kernel/repair/trusted-fact-authority');

const trustedKey = Buffer.alloc(32, 11);

function readJson(relative) {
  return JSON.parse(fs.readFileSync(path.join(sourceProject, relative), 'utf8'));
}

function readLastJsonl(relative) {
  return fs.readFileSync(path.join(sourceProject, relative), 'utf8')
    .trim()
    .split(/\r?\n/)
    .map((line) => JSON.parse(line))
    .at(-1);
}

function scopeProjection(plan) {
  const sorted = (values) => [...new Set(values)].sort();
  return {
    required_cases: sorted(plan.required_cases),
    baseline_cases: sorted(plan.baseline_cases),
    repaired_cases: sorted(plan.repaired_cases),
    impacted_cases: sorted(plan.impacted_cases),
    cases_to_rerun: plan.cases_to_rerun
      .map((entry) => ({
        case_id: entry.case_id,
        reasons: sorted(entry.reasons)
      }))
      .sort((left, right) => left.case_id.localeCompare(right.case_id)),
    reasons_by_case: Object.fromEntries(
      Object.entries(plan.reasons_by_case)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([caseId, reasons]) => [caseId, sorted(reasons)])
    )
  };
}

function evaluationFixture() {
  const verificationRoot = `openspec/changes/${changeId}/verify`;
  const repairRoot = `${verificationRoot}/repairs/${failureId}`;
  const registry = kernel.createSchemaRegistry({
    runtimeStatus: readJson(`${verificationRoot}/v2/runtime-status.json`),
    runtimeRoot
  });
  const authority = createTrustedFactAuthority({
    schemaRegistry: registry,
    key: trustedKey,
    clock: () => '2026-08-27T15:30:00.000Z'
  });
  const failure = readJson(`${verificationRoot}/v2/failures.json`)
    .find((entry) => entry.id === failureId);
  const bindings = {
    failure_id: failure.id,
    change_id: failure.change_id,
    run_id: failure.run_id,
    case_id: failure.case_id
  };
  const runs = readJson(`${verificationRoot}/v2/runs.json`)
    .filter((run) => (
      run.id === failure.run_id
      || (
        run.failure_id === failure.id
        && run.kind === 'retest'
      )
    ));
  const runIds = new Set(runs.map((run) => run.id));
  const attempts = readJson(`${verificationRoot}/v2/attempts.json`)
    .filter((attempt) => runIds.has(attempt.run_id));
  const facts = attempts.map((attempt, index) => authority.seal(
    'attempt_fact',
    {
      attempt_id: attempt.id,
      case_id: attempt.case_id,
      attempt_digest: sha256(canonicalJson(attempt)),
      verdict: attempt.status === 'passed' ? 'pass' : 'fail',
      evidence_ids: [`evidence-test-${index + 1}`],
      integrity: 'intact',
      freshness: 'fresh',
      recorded_at: attempt.completed_at
    },
    {
      ...bindings,
      run_id: attempt.run_id,
      case_id: attempt.case_id,
      attempt_id: attempt.id
    }
  ));
  const classification = authority.seal(
    'classification_result',
    readJson(`${repairRoot}/classification-envelope.json`).payload,
    bindings
  );
  const repair = authority.seal(
    'repair_link',
    readJson(`${repairRoot}/repair-link-completed-envelope.json`).payload,
    bindings
  );
  const supersession = authority.seal(
    'repair_scope_supersession',
    readLastJsonl(`${repairRoot}/repair-scope-supersessions.jsonl`).payload,
    bindings
  );
  const rerunPayload = readLastJsonl(`${repairRoot}/rerun-plans.jsonl`).payload;
  const rerun = authority.seal('rerun_plan', rerunPayload, bindings);
  const scope = scopeProjection(rerunPayload);
  const machine = kernel.createRepairLoopStateMachine({
    schemaRegistry: registry,
    trustVerifier: authority,
    rerunScopeAuthority: {
      resolve() {
        return {
          ok: true,
          scope,
          scope_digest: sha256(canonicalJson(scope))
        };
      }
    },
    clock: () => '2026-08-27T15:30:00.000Z'
  });
  return {
    machine,
    request: {
      classification_result: classification,
      runs,
      attempts,
      attempt_facts: facts,
      repair_link: repair,
      repair_scope_supersession: supersession,
      rerun_plan: rerun
    }
  };
}

test('approved successor snapshot repair proceeds to regression', () => {
  const fixture = evaluationFixture();
  const result = fixture.machine.evaluate(fixture.request);
  assert.equal(result.ok, true);
  assert.equal(result.status, 'regression_required');
  assert.equal(result.transition_proposal.action, 'request_regression');
  assert.equal(result.transition_proposal.case_ids.length, 9);
  assert.equal(
    result.transition_proposal.case_ids.includes('case-a6-path-security'),
    false
  );
});

test('successor snapshot repair remains blocked without supersession authority', () => {
  const fixture = evaluationFixture();
  delete fixture.request.repair_scope_supersession;
  const result = fixture.machine.evaluate(fixture.request);
  assert.equal(result.ok, false);
  assert.equal(
    result.blockers[0].id,
    'verification-repair-loop:repair-fingerprint-scope-invalid'
  );
  assert.equal(result.blockers[0].detail, 'case_snapshot_hash');
});

test('successor snapshot repair rejects a tampered supersession authority', () => {
  const fixture = evaluationFixture();
  fixture.request.repair_scope_supersession = {
    ...fixture.request.repair_scope_supersession,
    signature: '0'.repeat(64)
  };
  const result = fixture.machine.evaluate(fixture.request);
  assert.equal(result.ok, false);
  assert.match(
    result.blockers[0].id,
    /trusted-envelope/
  );
});
