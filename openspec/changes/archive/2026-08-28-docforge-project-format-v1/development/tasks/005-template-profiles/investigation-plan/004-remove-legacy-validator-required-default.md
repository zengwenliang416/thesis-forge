---
issue_id: "004"
title: "Remove thesis-shaped global validator metadata defaults"
priority: 4
scope: "/Volumes/zwl/open_sources/thesis-forge/src/docforge/core/validator.py, /Volumes/zwl/open_sources/thesis-forge/tests/test_validator.py"
acceptance_criteria: "ValidationContext defaults to no global required metadata, from_document() does not restore thesis.title/author.name when project discovery fails or is absent, and selected-template required bindings still produce structured required-metadata issues."
test_requirements: "Add direct no-project and bare ForgeDocument validator regressions without passing required_metadata=(), plus a template-scoped academic missing-field regression that proves template requirements remain active."
depends_on: ["001", "002"]
---

# 004: Remove thesis-shaped global validator required defaults

## Context

`ValidationContext` still defaults to `("thesis.title", "author.name")`.
`ValidationContext.from_document()` restores that tuple whenever it cannot
discover a project. This contradicts the generic DocForge contract and makes
direct Validator callers fail ordinary documents even when the selected
template has no such fields.

The template binding pass already supplies template-owned requirements. The
global default should therefore be neutral, while an explicitly supplied
`required_metadata` tuple remains available for callers that intentionally
define an additional rule.

## Changes

Remove the legacy constant and use an empty tuple as the dataclass and
`from_document()` default. Do not remove template-scoped requirement
diagnostics: `resolve_template_bindings()` must still produce structured
`required-metadata` issues for required academic fields and must include the
template ID in their details.

Keep the change local to the Validator contract. Do not add a fallback to the
old thesis-shaped paths and do not alter unrelated validation rules.

## Files to Modify/Create

- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/core/validator.py` —
  make global required metadata opt-in and retain template-owned checks.
- `/Volumes/zwl/open_sources/thesis-forge/tests/test_validator.py` — cover
  direct no-project validation and explicit/template requirement separation.

## Edge Cases

- A missing project must still report project/template/path errors that are
  independently applicable; only obsolete global metadata errors disappear.
- `required_metadata=("custom.path",)` must continue to work unchanged.
- A generic template with only common metadata must not acquire academic
  requirements through Validator defaults.
- An academic template's missing required bindings remain errors even when the
  global tuple is empty.

## Verification

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_validator.py tests/templates/test_metadata_bindings.py`
- `.venv/bin/ruff check src/docforge/core/validator.py tests/test_validator.py`
