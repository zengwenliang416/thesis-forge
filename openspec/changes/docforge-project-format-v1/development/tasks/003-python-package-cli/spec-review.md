# Spec Review: 003-python-package-cli

## Verdict

approved

## Missing Requirements

- None for Task 003 items 3.1 through 3.5.
- `docforge` is the sole active Python distribution, import package, and CLI
  identity.
- The CLI exposes `inspect`, `validate`, `review`, and `build` through the
  shared typed application service.
- `review` uses manifest-resolved paths when `--output-dir` is omitted, while
  preserving explicit export-root behavior.
- The wheel contains all four required template YAML resources and exactly one
  console entry point: `docforge = docforge.cli:app`.
- Clean isolated installation and offline execution of `inspect`, `validate`,
  `review`, and `build` passed.

## Extra Behavior

- None. No `thesis_forge` compatibility package, `thesisforge` command alias,
  fallback loader, or migration shim was added.

## Misunderstood Requirements

- None. The package and CLI cutover does not claim ownership of the later
  protocol, desktop, template, example, or release migrations.

## Cannot Verify From Diff

- The old workbench protocol and BuildReport identifiers remain deferred to
  Task 004 and are not claimed by this Task 003 review.
- Repository-owned obsolete project fixtures and full-repository migration
  failures remain assigned to Task 007.

## Acceptance Assertions Verified

- `A4` Task 003 clauses: the active source tree has no `thesis_forge` imports
  or `ThesisDocument` definition, `pyproject.toml` exposes only `docforge`, and
  the freshly built wheel contains no `thesis_forge/` files or `thesisforge`
  console alias. The old workbench protocol clause remains pending Task 004;
  the whole assertion is not yet globally complete.
- `A5` Task 003 clauses: `document.md`, `build/document.docx`,
  `review/document.review.md`, and `review/document.review-map.json` are
  verified through project constants, manifest and path tests, default Review
  CLI execution, and isolated installed-CLI execution.

## Required Fixes

- No fixes are required for Task 003.
