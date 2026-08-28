'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  archiveCommandSucceeded
} = require('../scripts/archive-change');

test('rejects an OpenSpec archive that reports Aborted with exit zero', () => {
  assert.equal(archiveCommandSucceeded({
    ok: true,
    status: 0,
    stdout_tail: [
      'Task status: Complete',
      'Aborted. No files were changed.'
    ].join('\n')
  }), false);
});

test('accepts only a successful non-aborted OpenSpec archive result', () => {
  assert.equal(archiveCommandSucceeded({
    ok: true,
    status: 0,
    stdout_tail: 'Archived docforge-workbench-ui-redesign.'
  }), true);
  assert.equal(archiveCommandSucceeded({
    ok: false,
    status: 2,
    stdout_tail: ''
  }), false);
});
