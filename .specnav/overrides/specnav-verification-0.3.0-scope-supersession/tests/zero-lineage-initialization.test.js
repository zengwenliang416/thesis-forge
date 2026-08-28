'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  initializeCanonicalZeroLineage
} = require('../kernel/pipeline/artifact-pipeline');
const {
  createVerificationArtifactStore
} = require('../kernel/persistence/verification-artifact-store');

function createStore() {
  const changeRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'specnav-zero-lineage-'));
  const verificationRoot = path.join(changeRoot, 'verify');
  return {
    changeRoot,
    verificationRoot,
    store: createVerificationArtifactStore({
      changeRoot,
      root: verificationRoot
    })
  };
}

const fingerprints = Object.freeze({
  case_snapshot_hash: 'a'.repeat(64),
  code_sha: 'b'.repeat(40),
  test_sha: 'c'.repeat(64),
  environment_hash: 'd'.repeat(64),
  runtime_version: '2.0.0-alpha.2',
  kernel_version: '2.0.0-alpha.2'
});

test('zero-failure verification materializes every canonical lineage file', (t) => {
  const fixture = createStore();
  t.after(() => fs.rmSync(fixture.changeRoot, { recursive: true, force: true }));

  const result = initializeCanonicalZeroLineage(fixture.store, {
    changeId: 'docforge-workbench-ui-redesign',
    currentFingerprints: fingerprints,
    clock: () => '2026-08-28T10:00:00.000Z'
  });

  assert.equal(result.ok, true);
  assert.deepEqual(
    JSON.parse(fs.readFileSync(
      path.join(fixture.verificationRoot, 'v2/failures.json'),
      'utf8'
    )),
    []
  );
  assert.deepEqual(
    JSON.parse(fs.readFileSync(
      path.join(fixture.verificationRoot, 'v2/repair-links.json'),
      'utf8'
    )),
    []
  );
  for (const name of [
    'attempt-facts.jsonl',
    'transition-proposals.jsonl',
    'transition-receipts.jsonl'
  ]) {
    assert.equal(
      fs.readFileSync(path.join(fixture.verificationRoot, 'v2', name), 'utf8'),
      ''
    );
  }
  const migration = JSON.parse(fs.readFileSync(
    path.join(fixture.verificationRoot, 'v2/migration-status.json'),
    'utf8'
  ));
  assert.equal(migration.schema, 'specnav.verification.migration-status.v1');
  assert.equal(migration.change_id, 'docforge-workbench-ui-redesign');
  assert.equal(migration.required, false);
  assert.equal(migration.status, 'not_required');
  assert.deepEqual(migration.legacy_artifacts, []);
  assert.match(migration.source_inventory_digest, /^[a-f0-9]{64}$/);
  assert.equal(migration.fallback_used, false);
});

test('zero-lineage initialization never overwrites existing history', (t) => {
  const fixture = createStore();
  t.after(() => fs.rmSync(fixture.changeRoot, { recursive: true, force: true }));
  const v2 = path.join(fixture.verificationRoot, 'v2');
  fs.mkdirSync(v2, { recursive: true });
  const existing = {
    'failures.json': '[{"id":"failure-existing"}]\n',
    'repair-links.json': '[{"id":"repair-existing"}]\n',
    'attempt-facts.jsonl': '{"id":"attempt-fact-existing"}\n',
    'transition-proposals.jsonl': '{"id":"proposal-existing"}\n',
    'transition-receipts.jsonl': '{"id":"receipt-existing"}\n',
    'migration-status.json': '{"schema":"existing-migration"}\n'
  };
  for (const [name, content] of Object.entries(existing)) {
    fs.writeFileSync(path.join(v2, name), content);
  }

  const result = initializeCanonicalZeroLineage(fixture.store, {
    changeId: 'docforge-workbench-ui-redesign',
    currentFingerprints: fingerprints
  });

  assert.equal(result.ok, true);
  assert.deepEqual(result.initialized, []);
  for (const [name, content] of Object.entries(existing)) {
    assert.equal(fs.readFileSync(path.join(v2, name), 'utf8'), content);
  }
});
