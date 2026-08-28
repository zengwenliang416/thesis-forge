'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  explicitPluginRoot
} = require('../scripts/verification-v2-trusted-runtime');

function pluginRoot(base, name) {
  const root = path.join(base, name);
  fs.mkdirSync(path.join(root, '.codex-plugin'), { recursive: true });
  fs.writeFileSync(
    path.join(root, '.codex-plugin', 'plugin.json'),
    `${JSON.stringify({ name })}\n`
  );
  return root;
}

test('accepts an explicit identity-validated plugin root', () => {
  const temporary = fs.mkdtempSync(path.join(
    fs.realpathSync(os.tmpdir()),
    'ops-runtime-'
  ));
  const root = pluginRoot(temporary, 'specnav-verification');
  const result = explicitPluginRoot(
    'specnav-verification',
    {
      env: {
        SPECNAV_VERIFICATION_ROOT: root
      }
    },
    'trusted-root-invalid'
  );

  assert.equal(result, root);
});

test('rejects identity mismatch and symlinked explicit roots', () => {
  const temporary = fs.mkdtempSync(path.join(
    fs.realpathSync(os.tmpdir()),
    'ops-runtime-'
  ));
  const wrong = pluginRoot(temporary, 'specnav-core');
  assert.throws(() => explicitPluginRoot(
    'specnav-verification',
    {
      env: {
        SPECNAV_VERIFICATION_ROOT: wrong
      }
    },
    'trusted-root-invalid'
  ), /trusted-root-invalid/);

  const actual = pluginRoot(temporary, 'specnav-verification');
  const link = path.join(temporary, 'verification-link');
  fs.symlinkSync(actual, link);
  assert.throws(() => explicitPluginRoot(
    'specnav-verification',
    {
      env: {
        SPECNAV_VERIFICATION_ROOT: link
      }
    },
    'trusted-root-invalid'
  ), /trusted-root-invalid/);
});
