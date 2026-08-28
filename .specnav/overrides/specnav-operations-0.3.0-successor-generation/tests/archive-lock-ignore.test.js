'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  nonTransientGitStatusLines
} = require('../scripts/verification-v2-proof');

test('accepts only the owned SpecNav archive transaction lock', () => {
  const root = fs.mkdtempSync(path.join(
    fs.realpathSync(os.tmpdir()),
    'ops-archive-lock-'
  ));
  const lock = path.join(root, 'openspec', '.specnav', 'archive.lock');
  const token = '1234:0123456789abcdef0123456789abcdef';
  fs.mkdirSync(lock, { recursive: true });
  fs.writeFileSync(path.join(lock, 'owner'), `${token}\n`);

  assert.deepEqual(
    nonTransientGitStatusLines(
      root,
      '?? openspec/.specnav/archive.lock/owner\n',
      { SPECNAV_ARCHIVE_LOCK_TOKEN: token }
    ),
    []
  );
  assert.deepEqual(
    nonTransientGitStatusLines(
      root,
      [
        '?? openspec/.specnav/archive.lock/owner',
        ' M src/docforge/cli.py'
      ].join('\n'),
      { SPECNAV_ARCHIVE_LOCK_TOKEN: token }
    ),
    [' M src/docforge/cli.py']
  );
  assert.deepEqual(
    nonTransientGitStatusLines(
      root,
      '?? openspec/.specnav/archive.lock/owner\n',
      { SPECNAV_ARCHIVE_LOCK_TOKEN: '1234:ffffffffffffffffffffffffffffffff' }
    ),
    ['?? openspec/.specnav/archive.lock/owner']
  );
});
