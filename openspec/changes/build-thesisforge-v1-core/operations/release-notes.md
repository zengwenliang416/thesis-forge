# Release Notes: build-thesisforge-v1-core

## Summary

- ThesisForge `0.1.0` completes the local-first V1 compiler pipeline:
  Markdown to `ThesisDocument`, validation, template resolution, `RenderPlan`,
  and deterministic DOCX output.
- This closure is `local-only`. It permits repository-local development,
  acceptance, package building, and local installation, but not public
  redistribution.

## Verification

- `make verify` completed with `124 passed`.
- All six SpecNav verification domains are green for the 20 user-approved
  cases, with no blocker or uncovered approved scope.
- CodeGraph verified all 18 implementation and verification claims.
- DOCX evidence includes OOXML assertions, ZIP/package integrity,
  `python-docx` reload, installed-wheel execution outside the repository, and
  LibreOffice headless rendering.

## Known Limitations

- No project license has been selected. Do not publish the package or source to
  a public registry until ownership and licensing review is complete.
- GB/T bibliography formatting and LaTeX-to-OMML conversion implement the
  documented V1 subsets rather than the complete standards.
- TOC and page fields require refresh in the target Office client; LibreOffice
  headless field behavior is not authoritative for Word or WPS.
- Sensory verification is not a full WCAG audit or cross-platform
  Word/WPS/LibreOffice certification.
