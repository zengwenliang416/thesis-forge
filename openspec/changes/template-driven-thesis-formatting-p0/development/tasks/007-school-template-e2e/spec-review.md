# Spec Review: 007-school-template-e2e

## Verdict

approved

## Missing Requirements

- None found within tasks 7.1-7.7.
- `docs/TEMPLATE_SPEC.md` documents the complete P0 schema, defaults, units,
  compatibility rules, enums, selection and package-data behavior.
- The HUT YAML and complete thesis fixture cover all required semantic and
  section surfaces without adding school constants to production renderers.
- Offline inspect/validate/build, input immutability, direct package assertions,
  determinism and two-template equivalence have committed acceptance coverage.

## Extra Behavior

- Wheel and native sidecar package-data coverage was added so the HUT template
  remains selectable outside a source checkout. This is required distribution
  behavior, was added to the task allowlist before implementation and does not
  change application service contracts.

## Misunderstood Requirements

- None. `inspect` remains parser-only; `validate` and `build` explicitly select
  the HUT YAML in acceptance tests. The source Front Matter also retains the
  stable `hut-master-2026` template ID.
- Word/WPS sensory review was not claimed and remains task 008/A10.

## Cannot Verify From Diff

- Microsoft Word or WPS visual layout remains outside this slice and is
  explicitly deferred to task 008.
- Windows-native sidecar execution was not run on macOS. The shared package
  list and Windows naming/distribution contracts are tested, while native
  macOS arm64 sidecar execution was verified directly.

## Acceptance Assertions Verified

- A2: existing templates and defaults remain covered by the task-file and full
  regression suites.
- A3: Chinese/English abstract and keyword role style IDs are asserted in
  `document.xml` and `styles.xml`.
- A4: real TOC field plus TOC 1-3 style/tab/leader properties are asserted.
- A5: superscript citations and bibliography hanging indent are asserted.
- A6: page distances, grid, even/odd settings, first/default/even
  relationships, borders and PAGE-only policy are asserted in saved parts.
- A7: equal RenderPlan snapshots across style-only template variants preserve
  the renderer-neutral semantic seam.
- A8: offline input hashing, repeated canonical OOXML and recursive renderer
  scans prove deterministic execution without school constants.
- A9: the complete fixture builds into a package that passes direct XML,
  relationship and package validation.
- Tasks 7.1-7.7: all implementation and evidence requirements are present.
- Independent re-review confirmed explicit HUT validate/build and accepted the
  final implementation after review fixes.

## Required Fixes

- None.
