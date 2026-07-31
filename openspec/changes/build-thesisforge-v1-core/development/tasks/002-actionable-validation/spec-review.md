# Spec Review: 002-actionable-validation

## Verdict

approved

## Missing Requirements

- None within tasks 2.1 through 2.8.
- Citation-key existence is not missing from this slice because task 006
  explicitly owns BibTeX loading and citation-key validation.

## Extra Behavior

- Resource-root enforcement was added because `acceptance.md` names path escape
  as a red-team surface and the validation flow owns local resource safety.
- Built-in templates are included in the wheel so metadata template IDs remain
  deterministic outside the repository checkout.

## Misunderstood Requirements

- None. Explicit template paths override metadata IDs; warning-only validation
  succeeds; errors fail; source parse/read failures use exit 2.

## Cannot Verify From Diff

- The repository has no baseline commit, so review used current allowed files,
  executable tests, package artifacts, CodeGraph evidence and command output.

## Acceptance Assertions Verified

- `A1`: validate-flow portion runs offline without API keys.
- `A3`: duplicate IDs, missing references/images/bibliography/metadata,
  template errors and structural citation prerequisites are verified. Per-key
  BibTeX validation remains assigned to task 006.

## Required Fixes

- None. Review findings for cwd-dependent template lookup, missing packaged
  templates, malformed YAML classification, bibliography omission, resource
  escapes, core/CLI copy coupling, example pipeline drift and explicit template
  suffixes were fixed and re-reviewed.
