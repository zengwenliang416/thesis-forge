'use strict';

const macosAliases = Object.freeze({
  宋体: 'Source Han Serif SC',
  黑体: 'PingFang SC',
});

function previewFontAliases(platform) {
  return platform === 'darwin' ? macosAliases : Object.freeze({});
}

function planConversion(platform, adaptationResult) {
  const aliases = previewFontAliases(platform);
  if (Object.keys(aliases).length === 0) {
    return { input: 'source-docx', aliases, status: 'convert-original' };
  }
  if (adaptationResult === 'success') {
    return { input: 'temporary-docx', aliases, status: 'convert-adapted' };
  }
  return { input: null, aliases, status: 'preview-unavailable' };
}

module.exports = { macosAliases, previewFontAliases, planConversion };

if (require.main === module) {
  const cases = [
    ['darwin', 'success'],
    ['darwin', 'failure'],
    ['win32', 'success'],
    ['linux', 'success'],
  ];
  for (const [platform, result] of cases) {
    process.stdout.write(`${platform}/${result} -> ${JSON.stringify(planConversion(platform, result))}\n`);
  }
}
