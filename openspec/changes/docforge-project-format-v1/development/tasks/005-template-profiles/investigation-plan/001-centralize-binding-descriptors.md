---
issue_id: "001"
title: "Centralize metadata binding descriptors and formatting policy"
priority: 1
scope: "/Volumes/zwl/open_sources/thesis-forge/src/docforge/templates/model.py, /Volumes/zwl/open_sources/thesis-forge/src/docforge/templates/bindings.py, /Volumes/zwl/open_sources/thesis-forge/src/docforge/presentation/metadata.py, /Volumes/zwl/open_sources/thesis-forge/tests/templates/test_metadata_bindings.py"
acceptance_criteria: "Every MetadataBindingPath has exactly one descriptor containing its reader-facing label and value-format policy; default cover fields are selected from that registry; binding resolution and presentation labels use the registry; legal-path parity and multi-author/custom-join behavior are covered by tests."
test_requirements: "Assert registry keys exactly equal typing.get_args(MetadataBindingPath), default cover fields are registry-backed, every legal path has a label, authors and keywords use descriptor-driven joins, and Review/Preview label lookup remains compatible."
depends_on: []
---

# 001: Centralize metadata binding descriptors and formatting policy

## Context

The current binding contract is split across three independent sources:

- `MetadataBindingPath` and `_default_cover_items()` in
  `src/docforge/templates/model.py`;
- path-specific `if` branches for authors and keywords in
  `src/docforge/templates/bindings.py`;
- `_BINDING_LABELS` in `src/docforge/presentation/metadata.py`.

Adding or changing a legal path can therefore leave the Template Model,
resolver, or Review/Preview labels out of sync. The resulting failure is late
and runtime-specific: a valid template can compile and then raise
`ValueError` while projecting a Review or Preview.

## Changes

Create one template-boundary descriptor registry keyed by the existing closed
`MetadataBindingPath` values. Each descriptor should carry, at minimum, the
reader-facing label and a value-format kind for scalar, authors, or keywords
values. Keep `MetadataBindingPath` as the public closed type, and use an
explicit parity assertion/test rather than creating a second open-ended path
type.

Make `_default_cover_items()` select its paths from the registry. Make
`resolve_template_bindings()` dispatch formatting through descriptor metadata
instead of comparing literal path strings. Make
`cover_binding_label()` read the same registry while preserving its current
unsupported-path `ValueError` behavior.

Do not change Renderer behavior or add a compatibility alias for obsolete
paths.

## Files to Modify/Create

- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/templates/model.py` —
  add the typed descriptor registry and derive default cover paths from it.
- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/templates/bindings.py`
  — resolve scalar/list values through descriptor format policy.
- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/presentation/metadata.py`
  — consume registry labels instead of a duplicate mapping.
- `/Volumes/zwl/open_sources/thesis-forge/tests/templates/test_metadata_bindings.py`
  — add registry parity, label coverage, and formatting regressions.

## Edge Cases

- A legal path missing from the registry must fail the parity test before a
  template reaches Review/Preview.
- Empty or malformed authors/keywords entries must still resolve to an empty
  value rather than fabricated prose.
- Custom `join_with` values must be honored for multiple authors and keywords.
- Static cover text remains outside the metadata binding registry.

## Verification

- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates/test_metadata_bindings.py tests/test_template.py`
- `.venv/bin/ruff check src/docforge/templates/model.py src/docforge/templates/bindings.py src/docforge/presentation/metadata.py tests/templates/test_metadata_bindings.py`
