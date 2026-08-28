---
issue_id: "002"
title: "Define locale-aware localized metadata resolution"
priority: 2
scope: "/Volumes/zwl/open_sources/thesis-forge/src/docforge/project/model.py, /Volumes/zwl/open_sources/thesis-forge/src/docforge/templates/bindings.py, /Volumes/zwl/open_sources/thesis-forge/templates/base/docforge-standard.yaml, /Volumes/zwl/open_sources/thesis-forge/tests/templates/test_metadata_bindings.py"
acceptance_criteria: "For zh-* and en-* project languages, localized title bindings prefer the matching locale, fall back to the other available locale when needed, emit the effective title exactly once, and treat an English-only en-* generic project as valid without weakening the no-title error."
test_requirements: "Cover zh-only, en-only, bilingual, and missing-title projects; assert selected RenderPlan binding/value and absence of duplicate fallback output; assert the explicit required-title diagnostic for a project with no title."
depends_on: ["001"]
---

# 002: Define locale-aware localized metadata resolution

## Context

`LocalizedText` accepts either `zh` or `en`, and `ProjectSpec.language` already
provides a BCP47-like language tag. However, `docforge-standard` marks only
`metadata.title.zh` as required, so a valid `en-US` project containing only
`metadata.title.en` is rejected. The current resolver also treats localized
fields as independent cover items, which would either report a false missing
required field or emit the same fallback value twice once fallback is added.

The project is intentionally UI-locale-static (`zh-CN`), but document metadata
still needs an explicit language policy. This is a binding-resolution concern,
not a parser or Renderer locale switch.

## Changes

Carry the manifest project language into the binding-resolution context without
flattening the typed metadata groups. Extend the shared binding descriptors with
the localized-field group and locale preference needed to resolve title and
subtitle pairs.

Define the observable policy explicitly:

- `zh-*` prefers `metadata.*.zh`, then falls back to `.en`;
- `en-*` prefers `metadata.*.en`, then falls back to `.zh`;
- if both values exist, emit only the preferred value for the localized cover
  group unless the template intentionally declares both as separate content;
- if the preferred value is absent and fallback exists, the template-required
  localized title is considered satisfied by that fallback;
- if neither value exists, preserve a structured required-metadata failure.

Update the generic template declaration only as needed to express this policy;
do not add a second locale-specific template or a frontend language switch.

## Files to Modify/Create

- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/project/model.py` —
  preserve strict `LocalizedText` validation and expose the language context
  needed by the binding boundary if the current manifest dump is insufficient.
- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/templates/bindings.py`
  — resolve localized groups with preferred-locale fallback and deduplicate
  the effective value.
- `/Volumes/zwl/open_sources/thesis-forge/templates/base/docforge-standard.yaml`
  — align the generic cover requirement with the explicit one-title locale
  policy without adding academic requirements.
- `/Volumes/zwl/open_sources/thesis-forge/tests/templates/test_metadata_bindings.py`
  — add locale matrix and no-title regressions.

## Edge Cases

- `zh-Hant`, `zh-TW`, and `en-GB` must use the primary language subtag rather
  than exact-string equality.
- A bilingual project must not duplicate one title as both a preferred value
  and a fallback value.
- A subtitle may remain absent even when a title is required.
- The policy must not fabricate a title from organization, author, or body
  text.

## Verification

- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates/test_metadata_bindings.py tests/project/test_manifest_model.py`
- `.venv/bin/ruff check src/docforge/project/model.py src/docforge/templates/bindings.py tests/templates/test_metadata_bindings.py`
