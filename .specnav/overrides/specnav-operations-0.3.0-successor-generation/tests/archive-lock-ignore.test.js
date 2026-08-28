'use strict';

const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const path = require('node:path');
const test = require('node:test');

const PROJECT_ROOT = path.resolve(__dirname, '../../../..');

function isIgnored(relativePath) {
  const result = childProcess.spawnSync(
    'git',
    ['check-ignore', '--no-index', '--quiet', '--', relativePath],
    {
      cwd: PROJECT_ROOT,
      encoding: 'utf8'
    }
  );
  if (result.status !== 0 && result.status !== 1) {
    throw new Error(result.stderr.trim() || 'git check-ignore failed');
  }
  return result.status === 0;
}

test('ignores only the SpecNav archive transaction lock', () => {
  assert.equal(
    isIgnored('openspec/.specnav/archive.lock/owner'),
    true
  );
  assert.equal(
    isIgnored('openspec/.specnav/unexpected-state/owner'),
    false
  );
});
