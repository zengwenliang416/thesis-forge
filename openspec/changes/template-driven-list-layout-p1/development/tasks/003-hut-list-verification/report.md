# Task Report: 003-hut-list-verification

## Status

DONE

## Files Changed

- `templates/schools/hunan-university-of-technology/master-2026.yaml`, `tests/test_template.py`, `tests/test_acceptance.py`, lifecycle evidence.

## What Changed

- Added explicit three-level HUT ordered/unordered policies and complete list paragraph styles; added offline same-source HUT/default builds, repeatability and OOXML difference assertions.

## TDD Evidence

- Added HUT/default loading assertions and a nested, non-1-start list fixture that verifies RenderPlan equality, last-level fallback, numbering references and direct paragraph/run properties.

## Verification Commands

- Focused `147 passed`; full `383 passed`; Ruff, strict OpenSpec and three CodeGraph claims passed; complete HUT DOCX package validated.

## Concerns

- HUT values are explicit editable template policy; visual glyph choice still depends on Office client fonts.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Open the generated DOCX in Word or WPS for sensory list-flow review.

## Adjudication

Approved against tasks 3.1-3.4 in commit `8d6f225`.
