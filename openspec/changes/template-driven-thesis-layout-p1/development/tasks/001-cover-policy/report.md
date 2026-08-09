# Task Report: 001-cover-policy

## Status

DONE

## Files Changed

- `src/thesis_forge/templates/model.py`, `src/thesis_forge/templates/__init__.py`, `tests/test_template.py`, `docs/TEMPLATE_SPEC.md`.

## What Changed

- Added ordered cover policy, closed fields, generic defaults and strict validation.

## TDD Evidence

- Added default, exact-one-of, empty text and duplicate field tests.

## Verification Commands

- Focused suite included in the `142 passed` combined run; full suite `372 passed`.

## Concerns

- The generic default intentionally remains paragraph-flow based and does not add absolute positioning.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Downstream school templates should declare explicit cover items when their layout differs from the generic default.

## Adjudication

Approved against tasks 1.1-1.4.
