# Spec Review: 001-project-contract

## Verdict

approved

## Missing Requirements

- None. The strict `docforge.yaml` / `docforge.project.v1` entrypoint,
  neutral defaults, generic metadata, optional academic profile, and
  project-root confinement required by items 1.1 through 1.5 are implemented.
- The focused system-executed suite covers directory and manifest entrypoints,
  obsolete contracts, bare Markdown, strict fields, general and academic
  fixtures, and all declared project path boundaries.

## Extra Behavior

- None outside the task allowlist. The old manifest and schema are rejected
  rather than accepted through aliases or migration fallbacks.

## Misunderstood Requirements

- None. `resources.root` is the confined base for assets and bibliography;
  source, output, and Review paths retain their documented project-relative
  ownership.

## Cannot Verify From Diff

- Full CLI, desktop, template, package, and end-to-end migration behavior is
  intentionally owned by later tasks and is not claimed by this verdict.

## Acceptance Assertions Verified

- `A5`: constants, manifest defaults, path resolution tests, and the direct
  application-service probe verify `document.md`, `build/document.docx`,
  `review/document.review.md`, and `review/document.review-map.json`.
- `A6`: model redteam cases cover absolute, remote, traversal, and NUL values;
  path tests cover symlink escape for source, resource root, assets,
  bibliography, output directory and DOCX, and every Review path.

## Required Fixes

- None. The first independent review's path-coverage, canonical-source, and
  stale-evidence findings were fixed and the re-review verdict was approved.
