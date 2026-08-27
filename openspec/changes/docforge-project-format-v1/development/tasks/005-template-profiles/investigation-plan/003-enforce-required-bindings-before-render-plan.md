---
issue_id: "003"
title: "Enforce required template bindings before RenderPlan construction"
priority: 3
scope: "/Volumes/zwl/open_sources/thesis-forge/src/docforge/core/compiler.py, /Volumes/zwl/open_sources/thesis-forge/tests/compiler/test_template_profiles.py"
acceptance_criteria: "compile_document() never returns a partial CoverInstruction when a selected template binding is required but unresolved, and CoverInstruction.bindings contains only non-empty resolved values; optional omission is visible at the RenderPlan boundary."
test_requirements: "Add direct RenderPlan assertions for absent optional common metadata and a negative academic-template compile test that asserts a stable compiler error and no usable partial plan."
depends_on: ["001", "002"]
---

# 003: Enforce required bindings before RenderPlan construction

## Context

`_compile_cover()` currently resolves every declared cover field and copies
every result into `CoverInstruction.bindings`. Empty optional values are only
filtered later by the DOCX Renderer, Review, and Preview projections. This
leaks renderer-specific cleanup into a supposedly renderer-neutral RenderPlan.

The same function ignores `ResolvedMetadataBinding.required`. Direct callers of
`compile_document()` can therefore compile an academic template without its
required profile and receive a partial cover instruction.

## Changes

Keep full binding resolution as the source for diagnostics, then enforce the
compiler boundary before constructing `CoverInstruction`:

- detect every `required` binding with an empty resolved value;
- raise the existing compiler error family or a focused
  `CompilerError` subtype carrying the missing paths;
- do not return a partial `RenderPlan` or `CoverInstruction` on that failure;
- include only non-empty resolved values in `CoverInstruction.bindings`;
- preserve template item order and static cover items.

Do not add profile branches to the Renderer and do not make the Renderer
responsible for required-field enforcement.

## Files to Modify/Create

- `/Volumes/zwl/open_sources/thesis-forge/src/docforge/core/compiler.py` —
  enforce required bindings and filter optional empties in `_compile_cover()`.
- `/Volumes/zwl/open_sources/thesis-forge/tests/compiler/test_template_profiles.py`
  — add RenderPlan-level omission and required-binding failure tests.

## Edge Cases

- A document with no resolved common metadata must still omit the cover rather
  than create an empty cover instruction.
- Multiple missing required bindings should be reported deterministically.
- A required value that resolves to whitespace must count as missing.
- The Renderer must continue to work for valid general and academic plans
  without checking document type or template ID.

## Verification

- `PYTHONPATH=src .venv/bin/python -m pytest tests/compiler/test_template_profiles.py tests/test_compiler.py`
- `.venv/bin/ruff check src/docforge/core/compiler.py tests/compiler/test_template_profiles.py`
