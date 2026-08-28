'use strict';

const crypto = require('node:crypto');

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

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

function sameIds(left, right) {
  return canonicalJson([...new Set(left)].sort())
    === canonicalJson([...new Set(right)].sort());
}

function selectGenerationEvidence(index, input) {
  const inputEvidence = input.aggregation_request.evidence;
  const inputEvidenceIds = inputEvidence.map((entry) => entry.id);
  const entriesById = new Map(index.entries.map((entry) => [entry.id, entry]));
  const inputMatchesHistoricalIndex = inputEvidence.every((entry) => (
    canonicalJson(entriesById.get(entry.id)) === canonicalJson(entry)
  ));
  const entries = inputEvidence.map((entry) => entriesById.get(entry.id))
    .filter(Boolean)
    .sort((left, right) => (
      String(left.captured_at).localeCompare(String(right.captured_at))
      || String(left.id).localeCompare(String(right.id))
    ));
  const rawBytes = Buffer.from(
    entries.length === 0
      ? ''
      : `${entries.map((entry) => JSON.stringify(entry)).join('\n')}\n`
  );
  const scoped = {
    schema: 'specnav.verification.evidence-index.v1',
    index_version: Math.max(1, entries.length),
    change_id: index.change_id,
    generated_at: entries.at(-1)?.captured_at || null,
    source_raw: 'raw.jsonl',
    source_digest: sha256(rawBytes),
    record_count: entries.length,
    entries
  };
  return {
    ok: inputMatchesHistoricalIndex
      && sameIds(entries.map((entry) => entry.id), inputEvidenceIds)
      && scoped.index_version === input.evidence_index_version,
    scoped
  };
}

module.exports = {
  selectGenerationEvidence
};
