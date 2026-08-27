'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const pluginRoot = path.resolve(__dirname, '..');
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
const {
  createDevelopmentRepairBridge
} = require('../kernel/repair/development-repair-bridge');
const {
  lifecycleRepairPath,
  normalizeSupersededScope,
  run
} = require('../scripts/verification-v2-repair-loop');
const {
  commandFor,
  createVerificationHostAdapter
} = require('../scripts/host-verification-adapter');

const fixedTime = '2026-08-27T09:00:00.000Z';
const fixedGitRevision = 'c'.repeat(40);
const trustedKey = Buffer.alloc(32, 7);

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

function writeJsonl(file, values) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(
    file,
    values.length === 0
      ? ''
      : `${values.map((value) => JSON.stringify(value)).join('\n')}\n`
  );
}

function sourceChangeFile(relative) {
  return path.join(
    sourceProject,
    'openspec',
    'changes',
    changeId,
    relative
  );
}

function runtimeStatus() {
  return readJson(sourceChangeFile('verify/v2/runtime-status.json'));
}

function schemaRegistry() {
  return kernel.createSchemaRegistry({
    runtimeStatus: runtimeStatus(),
    runtimeRoot
  });
}

function digestFile(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function bindings(failure) {
  return {
    failure_id: failure.id,
    change_id: failure.change_id,
    run_id: failure.run_id,
    case_id: failure.case_id
  };
}

function replacementScope(extra = []) {
  const allowedFiles = [
    `openspec/changes/${changeId}/verify/v2/case-plan-request.json`,
    `openspec/changes/${changeId}/verify/v2/case-snapshot.json`,
    ...extra
  ];
  return {
    allowed_files: allowedFiles,
    denied_files: [],
    requires_review_on: allowedFiles,
    allowed_operations: {
      create: true,
      modify: true,
      delete: false,
      rename: false
    }
  };
}

function seedFixture(options = {}) {
  const projectRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), 'specnav-scope-supersession-')
  );
  const changeRoot = path.join(
    projectRoot,
    'openspec',
    'changes',
    changeId
  );
  const verificationRoot = path.join(changeRoot, 'verify');
  const sourceFailureRoot = sourceChangeFile(`verify/repairs/${failureId}`);
  const failure = readJson(sourceChangeFile('verify/v2/failures.json'))
    .find((entry) => entry.id === failureId);
  const runValue = readJson(sourceChangeFile('verify/v2/runs.json'))
    .find((entry) => entry.id === failure.run_id);
  const attempt = readJson(sourceChangeFile('verify/v2/attempts.json'))
    .find((entry) => entry.id === failure.attempt_id);
  const requestedPayload = readJson(
    path.join(sourceFailureRoot, 'repair-link-requested-envelope.json')
  ).payload;
  const startedPayload = readJson(
    path.join(sourceFailureRoot, 'repair-link-started-envelope.json')
  ).payload;
  const baselinePayload = readJson(
    path.join(sourceFailureRoot, 'repair-baseline-envelope.json')
  ).payload;
  const registry = schemaRegistry();
  const authority = createTrustedFactAuthority({
    schemaRegistry: registry,
    key: trustedKey,
    clock: () => fixedTime
  });
  const envelopeBindings = bindings(failure);
  const classificationEnvelope = authority.seal(
    'classification_result',
    readJson(path.join(sourceFailureRoot, 'classification-envelope.json')).payload,
    envelopeBindings
  );
  const requestedEnvelope = authority.seal(
    'repair_link',
    requestedPayload,
    envelopeBindings
  );
  const startedEnvelope = authority.seal(
    'repair_link',
    startedPayload,
    envelopeBindings
  );
  const baselineEnvelope = authority.seal(
    'repair_baseline',
    baselinePayload,
    envelopeBindings
  );
  const repairRoot = path.join(
    verificationRoot,
    'repairs',
    failureId
  );
  writeJson(path.join(verificationRoot, 'v2/failures.json'), [failure]);
  writeJson(path.join(verificationRoot, 'v2/runs.json'), [runValue]);
  writeJson(path.join(verificationRoot, 'v2/attempts.json'), [attempt]);
  writeJson(path.join(verificationRoot, 'v2/repair-links.json'), [
    startedPayload
  ]);
  writeJsonl(
    path.join(verificationRoot, `runs/${failure.run_id}/failures.jsonl`),
    [failure]
  );
  writeJson(
    path.join(repairRoot, 'classification-envelope.json'),
    classificationEnvelope
  );
  writeJson(
    path.join(repairRoot, 'repair-link-requested-envelope.json'),
    requestedEnvelope
  );
  writeJson(
    path.join(repairRoot, 'repair-link-started-envelope.json'),
    startedEnvelope
  );
  writeJson(
    path.join(repairRoot, 'repair-baseline-envelope.json'),
    baselineEnvelope
  );
  writeJson(path.join(repairRoot, 'repair-link.json'), startedPayload);
  const originalTask = readJson(
    sourceChangeFile(
      `development/tasks/${startedPayload.development_task_id}/context.json`
    )
  );
  writeJson(
    path.join(
      changeRoot,
      'development',
      'tasks',
      originalTask.id,
      'context.json'
    ),
    originalTask
  );
  const proposalSource = path.join(
    sourceProject,
    '.specnav/decisions/repair-contract-gap-proposal.json'
  );
  const proposalTarget = path.join(
    projectRoot,
    '.specnav/decisions/repair-contract-gap-proposal.json'
  );
  fs.mkdirSync(path.dirname(proposalTarget), { recursive: true });
  fs.copyFileSync(proposalSource, proposalTarget);
  const snapshot = readJson(sourceChangeFile('verify/v2/case-snapshot.json'));
  const approval = readJson(sourceChangeFile('verify/v2/case-approval.json'));
  if (options.staleApproval) {
    approval.snapshot_hash = '0'.repeat(64);
  }
  const approvalTarget = path.join(verificationRoot, 'v2/case-approval.json');
  if (options.staleApproval) {
    writeJson(approvalTarget, approval);
  } else {
    fs.copyFileSync(
      sourceChangeFile('verify/v2/case-approval.json'),
      approvalTarget
    );
  }
  const review = {
    schema: 'specnav.verification.repair-scope-supersession-review.v1',
    id: 'repair-scope-review-test',
    failure_id: failure.id,
    change_id: failure.change_id,
    classification: 'test_defect',
    decision: 'approved',
    reviewer: {
      id: 'zengwenliang416',
      kind: 'human'
    },
    reviewed_at: fixedTime,
    reason: 'Supersede the insufficient immutable test repair scope.',
    proposal_sha256: digestFile(proposalTarget),
    original_requested_envelope_digest: sha256(
      canonicalJson(requestedEnvelope)
    ),
    original_started_envelope_digest: sha256(
      canonicalJson(startedEnvelope)
    ),
    original_baseline_envelope_digest: sha256(
      canonicalJson(baselineEnvelope)
    ),
    current_git_revision: options.staleGitReview
      ? 'd'.repeat(40)
      : fixedGitRevision,
    replacement_scope: replacementScope(options.extraAllowedFiles || []),
    approved_snapshot_id: snapshot.id,
    approved_snapshot_hash: snapshot.snapshot_hash
  };
  const reviewRelative = `verify/repairs/${failure.id}/scope-review.json`;
  writeJson(path.join(changeRoot, reviewRelative), review);
  const context = {
    projectRoot,
    changeRoot,
    verificationRoot,
    changeId,
    reviewerId: 'zengwenliang416',
    schemaRegistry: registry,
    trustedFactKey: trustedKey,
    runtimeAuthority: { digest: 'runtime-authority-test' },
    runtimeStatusValue: runtimeStatus(),
    snapshotValue: snapshot,
    approvalValue: approval,
    requirementsValue: readJson(
      sourceChangeFile('verify/v2/requirements-source.json')
    ),
    acceptanceValue: readJson(
      sourceChangeFile('verify/v2/acceptance-source.json')
    )
  };
  const args = [
    'scope-supersede',
    '--failure-id',
    failure.id,
    '--supersession-review',
    `openspec/changes/${changeId}/${reviewRelative}`,
    '--contract-proposal',
    '.specnav/decisions/repair-contract-gap-proposal.json',
    '--approved'
  ];
  return {
    args,
    context,
    originalPaths: [
      path.join(repairRoot, 'classification-envelope.json'),
      path.join(repairRoot, 'repair-link-requested-envelope.json'),
      path.join(repairRoot, 'repair-link-started-envelope.json'),
      path.join(repairRoot, 'repair-baseline-envelope.json'),
      path.join(
        changeRoot,
        'development',
        'tasks',
        originalTask.id,
        'context.json'
      ),
      approvalTarget
    ],
    repairRoot,
    projectRoot
  };
}

function runFixture(fixture) {
  return run(fixture.args, {
    clock: () => fixedTime,
    gitRevision: () => fixedGitRevision,
    loadContext() {
      return { ok: true, context: fixture.context, blockers: [] };
    }
  });
}

test('scope supersession preserves history and replays idempotently', async (t) => {
  const fixture = seedFixture();
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const before = fixture.originalPaths.map((file) => fs.readFileSync(file));
  const first = await runFixture(fixture);
  assert.equal(first.ok, true);
  assert.equal(first.status, 'repair_scope_superseded');
  assert.equal(first.replayed, false);
  const log = path.join(
    fixture.repairRoot,
    'repair-scope-supersessions.jsonl'
  );
  const firstLog = fs.readFileSync(log);
  const logLines = firstLog.toString('utf8').trim().split(/\r?\n/);
  assert.equal(logLines.length, 1);
  const supersessionEnvelope = JSON.parse(logLines[0]);
  assert.equal(supersessionEnvelope.kind, 'repair_scope_supersession');
  assert.equal(supersessionEnvelope.bindings.log_sequence, 1);
  assert.equal(supersessionEnvelope.payload.failure_id, failureId);
  assert.equal(supersessionEnvelope.payload.classification, 'test_defect');
  const supersededEnvelope = path.join(
    fixture.repairRoot,
    'repair-link-superseded-envelope.json'
  );
  const firstEnvelope = fs.readFileSync(supersededEnvelope);
  const second = await runFixture(fixture);
  assert.equal(second.ok, true);
  assert.equal(second.replayed, true);
  assert.deepEqual(fs.readFileSync(log), firstLog);
  assert.deepEqual(fs.readFileSync(supersededEnvelope), firstEnvelope);
  fixture.originalPaths.forEach((file, index) => {
    assert.deepEqual(fs.readFileSync(file), before[index]);
  });
});

test('scope supersession rejects a stale snapshot approval', async (t) => {
  const fixture = seedFixture({ staleApproval: true });
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const result = await runFixture(fixture);
  assert.equal(result.ok, false);
  assert.deepEqual(
    result.blockers.map(({ id }) => id),
    ['verification-cases:approval-hash-mismatch']
  );
  assert.equal(
    fs.existsSync(path.join(
      fixture.repairRoot,
      'repair-scope-supersessions.jsonl'
    )),
    false
  );
});

test('scope supersession rejects unauthorized replacement files', async (t) => {
  const fixture = seedFixture({ extraAllowedFiles: ['README.md'] });
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const result = await runFixture(fixture);
  assert.equal(result.ok, false);
  assert.equal(
    result.blockers[0].id,
    'verification-repair:scope-supersession-file-unauthorized'
  );
});

test('scope supersession rejects a review for a different Git revision', async (t) => {
  const fixture = seedFixture({ staleGitReview: true });
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const before = fixture.originalPaths.map((file) => fs.readFileSync(file));
  const result = await runFixture(fixture);
  assert.equal(result.ok, false);
  assert.equal(
    result.blockers[0].id,
    'verification-repair:scope-supersession-review-invalid'
  );
  assert.equal(
    fs.existsSync(path.join(
      fixture.repairRoot,
      'repair-scope-supersessions.jsonl'
    )),
    false
  );
  assert.equal(
    fs.existsSync(path.join(
      fixture.repairRoot,
      'repair-link-superseded-envelope.json'
    )),
    false
  );
  fixture.originalPaths.forEach((file, index) => {
    assert.deepEqual(fs.readFileSync(file), before[index]);
  });
});

test('scope supersession rejects project-file symlink escapes', async (t) => {
  const fixture = seedFixture();
  const external = path.join(
    os.tmpdir(),
    `specnav-proposal-outside-${crypto.randomUUID()}.json`
  );
  t.after(() => {
    fs.rmSync(fixture.projectRoot, { recursive: true, force: true });
    fs.rmSync(external, { force: true });
  });
  const proposal = path.join(
    fixture.projectRoot,
    '.specnav/decisions/repair-contract-gap-proposal.json'
  );
  fs.copyFileSync(proposal, external);
  fs.rmSync(proposal);
  fs.symlinkSync(external, proposal);
  const result = await runFixture(fixture);
  assert.equal(result.ok, false);
  assert.match(
    result.blockers[0].id,
    /outside-project|outside-allowed-root/
  );
});

test('lifecycle exclusions are limited to the active failure and task', () => {
  const taskId = '900-verification-repair-active';
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      `openspec/changes/${changeId}/verify/repairs/${failureId}/receipt.json`
    ),
    true
  );
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      `openspec/changes/${changeId}/verify/repairs/failure-other/receipt.json`
    ),
    false
  );
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      `openspec/changes/${changeId}/development/tasks/${taskId}/report.md`
    ),
    true
  );
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      `openspec/changes/${changeId}/development/tasks/900-other/report.md`
    ),
    false
  );
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      '.specnav/.gitignore'
    ),
    true
  );
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      '.specnav/config.json'
    ),
    true
  );
  assert.equal(
    lifecycleRepairPath(
      changeId,
      failureId,
      taskId,
      '.specnav/unapproved-local-file.json'
    ),
    false
  );
});

test('scope supersession rejects a task bound to another failure identity', async (t) => {
  const fixture = seedFixture();
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const task = readJson(fixture.originalPaths[4]);
  task.frozen_failure.case_id = 'case-other';
  writeJson(fixture.originalPaths[4], task);
  const result = await runFixture(fixture);
  assert.equal(result.ok, false);
  assert.equal(
    result.blockers[0].id,
    'verification-repair:scope-supersession-original-task-invalid'
  );
  assert.equal(
    fs.existsSync(path.join(
      fixture.repairRoot,
      'repair-scope-supersessions.jsonl'
    )),
    false
  );
});

test('authority history is not appended before derived artifacts succeed', async (t) => {
  const fixture = seedFixture();
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const review = readJson(path.join(
    fixture.projectRoot,
    'openspec/changes',
    changeId,
    `verify/repairs/${failureId}/scope-review.json`
  ));
  const originalTask = readJson(fixture.originalPaths[4]);
  const replacementScopeDigest = sha256(canonicalJson(
    normalizeSupersededScope(review.replacement_scope)
  ));
  const taskId = `900-verification-repair-${sha256(canonicalJson({
    original_task_id: originalTask.id,
    review_id: review.id,
    replacement_scope_digest: replacementScopeDigest
  })).slice(0, 16)}`;
  writeJson(path.join(
    fixture.projectRoot,
    'openspec/changes',
    changeId,
    'development/tasks',
    taskId,
    'context.json'
  ), { conflict: true });
  const result = await runFixture(fixture);
  assert.equal(result.ok, false);
  assert.equal(
    result.blockers[0].id,
    'verification-repair:derived-artifact-conflict'
  );
  assert.equal(
    fs.existsSync(path.join(
      fixture.repairRoot,
      'repair-scope-supersessions.jsonl'
    )),
    false
  );
  assert.equal(
    fs.existsSync(path.join(
      fixture.repairRoot,
      'repair-link-superseded-envelope.json'
    )),
    false
  );
});

test('successor snapshot allowance requires a trusted supersession fact', async (t) => {
  const fixture = seedFixture();
  t.after(() => fs.rmSync(fixture.projectRoot, { recursive: true, force: true }));
  const superseded = await runFixture(fixture);
  assert.equal(superseded.ok, true);
  const registry = schemaRegistry();
  const successorAuthority = JSON.parse(fs.readFileSync(
    path.join(fixture.repairRoot, 'repair-scope-supersessions.jsonl'),
    'utf8'
  ).trim());
  const sourceLink = successorAuthority.payload.superseded_repair_link;
  const afterIdentity = {
    ...sourceLink.before_identity,
    case_snapshot_hash:
      successorAuthority.payload.approved_snapshot_hash,
    test_sha: 'b'.repeat(64)
  };
  const reviews = ['spec-review', 'quality-review'].map((kind, index) => ({
    schema: 'specnav.verification.repair-review.v1',
    id: `review-${kind}`,
    kind,
    verdict: 'approved',
    reviewer_id: `reviewer-${index + 1}`,
    reviewer_kind: 'human',
    reviewed_at: fixedTime,
    evidence_id: `evidence-${kind}`,
    task_id: sourceLink.development_task_id,
    failure_id: sourceLink.failure_id,
    repair_link_id: sourceLink.id,
    repair_link_digest: sha256(canonicalJson(sourceLink)),
    scope_digest: sourceLink.scope_digest,
    after_identity_digest: sha256(canonicalJson(afterIdentity))
  }));
  const bridge = createDevelopmentRepairBridge({
    schemaRegistry: registry,
    clock: () => fixedTime,
    trustedFactVerifier: createTrustedFactAuthority({
      schemaRegistry: registry,
      key: trustedKey,
      clock: () => fixedTime
    }).verify
  });
  const withoutApproval = bridge.completeRepair({
    repair_link: sourceLink,
    after_identity: afterIdentity,
    reviews
  });
  assert.equal(withoutApproval.ok, false);
  assert.equal(
    withoutApproval.blockers[0].id,
    'verification-repair-bridge:completion-fingerprint-invalid'
  );
  assert.equal(withoutApproval.blockers[0].detail, 'case_snapshot_hash');
  const forgedBooleanRepair = bridge.completeRepair({
    repair_link: sourceLink,
    after_identity: afterIdentity,
    reviews,
    approved_successor_snapshot: true
  });
  assert.equal(forgedBooleanRepair.ok, false);
  const approvedTestRepair = bridge.completeRepair({
    repair_link: sourceLink,
    after_identity: afterIdentity,
    reviews,
    successor_snapshot_authority: successorAuthority
  });
  assert.equal(approvedTestRepair.ok, true);
  assert.equal(
    approvedTestRepair.repair_link.after_identity.case_snapshot_hash,
    afterIdentity.case_snapshot_hash
  );
  assert.equal(
    approvedTestRepair.repair_link.after_identity.test_sha,
    afterIdentity.test_sha
  );
  assert.equal(
    approvedTestRepair.repair_link.after_identity.code_sha,
    sourceLink.before_identity.code_sha
  );
  const tamperedAuthorities = [
    {
      ...successorAuthority,
      signature: '0'.repeat(64)
    },
    {
      ...successorAuthority,
      payload: {
        ...successorAuthority.payload,
        approved_snapshot_hash: '0'.repeat(64)
      }
    },
    {
      ...successorAuthority,
      claims: [
        ...successorAuthority.claims,
        'repair-scope-supersession:forged'
      ]
    }
  ];
  for (const successor_snapshot_authority of tamperedAuthorities) {
    const tampered = bridge.completeRepair({
      repair_link: sourceLink,
      after_identity: afterIdentity,
      reviews,
      successor_snapshot_authority
    });
    assert.equal(tampered.ok, false);
    assert.equal(
      tampered.blockers[0].id,
      'verification-repair-bridge:completion-fingerprint-invalid'
    );
  }
  const unchangedTestIdentity = {
    ...afterIdentity,
    test_sha: sourceLink.before_identity.test_sha
  };
  const unchangedTestReviews = reviews.map((review) => ({
    ...review,
    after_identity_digest: sha256(canonicalJson(unchangedTestIdentity))
  }));
  const unchangedTestResult = bridge.completeRepair({
    repair_link: sourceLink,
    after_identity: unchangedTestIdentity,
    reviews: unchangedTestReviews,
    successor_snapshot_authority: successorAuthority
  });
  assert.equal(unchangedTestResult.ok, false);
  assert.equal(
    unchangedTestResult.blockers[0].id,
    'verification-repair-bridge:completion-no-source-change'
  );
  assert.equal(unchangedTestResult.blockers[0].detail, 'test_sha');
  const productLink = {
    ...sourceLink,
    id: 'repair-product-test',
    repair_kind: 'product_code'
  };
  const productAfterIdentity = {
    ...afterIdentity,
    code_sha: 'c'.repeat(64)
  };
  const productReviews = reviews.map((review) => ({
    ...review,
    task_id: productLink.development_task_id,
    repair_link_id: productLink.id,
    repair_link_digest: sha256(canonicalJson(productLink)),
    scope_digest: productLink.scope_digest,
    after_identity_digest: sha256(canonicalJson(productAfterIdentity))
  }));
  const productResult = bridge.completeRepair({
    repair_link: productLink,
    after_identity: productAfterIdentity,
    reviews: productReviews,
    successor_snapshot_authority: successorAuthority
  });
  assert.equal(productResult.ok, false);
  assert.equal(
    productResult.blockers[0].id,
    'verification-repair-bridge:completion-fingerprint-invalid'
  );
  assert.equal(productResult.blockers[0].detail, 'case_snapshot_hash');
});

test('host adapter requires approval and maps the supersession command', () => {
  const adapter = createVerificationHostAdapter({
    host: 'test',
    blockerPrefix: 'test-verification',
    execute() {
      throw new Error('must not execute without approval');
    }
  });
  const blocked = adapter.invoke({
    action: 'repair-scope-supersede',
    project_root: sourceProject,
    mode: 'full'
  });
  assert.equal(blocked.ok, false);
  assert.deepEqual(blocked.blocker_ids, [
    'test-verification:scope-supersession-approval-required'
  ]);
  const command = commandFor(pluginRoot, {
    action: 'repair-scope-supersede',
    project_root: sourceProject,
    options: {
      change: changeId,
      reviewer_id: 'zengwenliang416',
      failure_id: failureId,
      supersession_review: 'review.json',
      contract_proposal: '.specnav/decisions/proposal.json',
      approved: true
    }
  });
  assert.equal(command[1], 'scope-supersede');
  assert.equal(command.includes('--approved'), true);
  assert.equal(command.includes('--supersession-review'), true);
  assert.equal(command.includes('--contract-proposal'), true);
});
