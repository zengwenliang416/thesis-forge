# Acceptance Criteria: docforge-project-format-v1

## User-Visible Criteria

- A user can open a directory containing `docforge.yaml` and `document.md` in
  the CLI and desktop workbench.
- A general document using `docforge-standard` can be inspected, validated,
  reviewed, and built without university, degree, advisor, student ID, or other
  fabricated academic metadata.
- An academic document can supply the optional academic profile and use an
  academic template without leaking those requirements into general projects.
- User-visible filenames, labels, command help, diagnostics, application
  metadata, and release assets use DocForge/document terminology.
- A bare Markdown file is not treated as a complete project; the later importer
  remains the explicit path from arbitrary Markdown to a DocForge project.

## System Criteria

- `docforge.yaml` with `schema: docforge.project.v1` is the only accepted
  manifest contract.
- `thesisforge.yaml`, `thesisforge.project.v2`, the `thesisforge` command, and
  the old workbench protocol are not accepted through compatibility aliases.
- The Python distribution exposes `docforge` and the core aggregate no longer
  exports `ThesisDocument`.
- CLI, HTTP, Tauri, and frontend transport fixtures share one DocForge protocol.
- The existing parse, validate, compile, render, finalize, postflight, and
  preview stages remain ordered and deterministic.
- Renderer boundaries remain unchanged: the parser and core domain do not
  import Word/OOXML implementation dependencies.

## Data Criteria

- Manifest paths remain project-relative and reject absolute, remote, traversal,
  and symlink-escape paths.
- Common metadata is generic and academic metadata is accepted only through the
  typed optional academic profile.
- Output and Review defaults use `document` filenames.
- Repository examples and fixtures contain no active project entrypoint using
  the obsolete manifest/schema/default filenames.
- Failed builds retain the previous successful output and never overwrite the
  source document or project manifest.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Project identity/default constants have a single implementation per language
  boundary and matching contract fixtures across Python, TypeScript, and Rust.
- The generic template is data-driven and does not introduce document-type
  branching in the DOCX renderer.

## Verification Surfaces

- Facticity: scan runtime, package, fixtures, and active documentation for
  obsolete public identifiers and review every intentional historical mention.
- Static: Ruff, Python import/package checks, TypeScript typecheck/lint, Rust
  checks, manifest/schema validation, and distribution allowlist checks.
- Unit: project model/loader/path tests, generic and academic metadata tests,
  template resolution tests, CLI/protocol tests, and default filename tests.
- Redteam: obsolete manifest/schema/protocol rejection, path traversal, symlink
  escape, unknown fields, malformed academic profile, and output boundary cases.
- E2E: inspect/validate/review/build a complete general DocForge project and a
  complete academic DocForge project through CLI and runtime adapters.
- Sensory: open the installed macOS workbench and confirm neutral DocForge
  terminology, filenames, project identity, diagnostics, and Word preview.

## Unresolved Gaps

- None.
