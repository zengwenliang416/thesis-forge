# Changelog: build-thesisforge-v1-core

## Added

- Offline `inspect`, `validate`, and `build` commands for ThesisForge Markdown.
- Typed `ThesisDocument`, template resolution, structured validation issues, and
  compiler-owned numbering through `RenderPlan`.
- Deterministic DOCX rendering for headings, paragraphs, lists, figures, tables,
  equations, captions, bookmarks, cross-references, sections, headers, footers,
  page fields, citations, and bibliography.
- Local package build and installed-wheel verification with bundled base and
  example-school templates.
- Complete thesis example, maintenance guide, architecture and syntax
  specifications, and distribution verification script.
- Six-domain verification evidence covering 20 approved user cases, OOXML
  structure, package integrity, LibreOffice rendering, prototype behavior, and
  accessibility-oriented interaction checks.

## Changed

- Completed all 65 implementation and verification tasks for the V1 core.
- Preserved failed-build outputs through atomic replacement and deterministic
  conflict handling.
- Documented the local-only distribution boundary while the repository has no
  project license.
