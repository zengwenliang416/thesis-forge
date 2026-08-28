'use strict';

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])])
  );
}

function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

function reportSemantic(model) {
  return {
    change_id: model.change_id,
    verdict: model.verdict,
    sources: model.sources,
    summary: model.summary,
    catalog: model.catalog,
    results: model.results,
    blockers: model.blockers,
    warnings: model.warnings
  };
}

function sameReportSemantics(left, right) {
  if (!left || !right) return false;
  return canonicalJson(reportSemantic(left))
    === canonicalJson(reportSemantic(right));
}

module.exports = {
  reportSemantic,
  sameReportSemantics
};
