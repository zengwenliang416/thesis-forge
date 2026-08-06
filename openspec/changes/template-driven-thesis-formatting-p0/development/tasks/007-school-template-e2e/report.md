# Task Report: 007-school-template-e2e

## Status

DONE

## Files Changed

- `docs/TEMPLATE_SPEC.md`
- `templates/schools/hunan-university-of-technology/master-2026.yaml`
- `examples/complete-thesis/thesis.md`
- `examples/complete-thesis/references.bib`
- `examples/complete-thesis/images/acceptance-architecture.png`
- `tests/test_acceptance.py`
- `pyproject.toml`
- `scripts/build_sidecar.py`
- `tests/test_desktop_distribution.py`

## What Changed

- Documented the complete P0 template schema, selection rules, typed paragraph
  policy, units, semantic roles, TOC, bibliography, citation, section variants,
  compatibility behavior and the HUT example.
- Added the `hut-master-2026` school template with template-only body, heading,
  abstract, keyword, TOC, bibliography, citation, page geometry, grid,
  first/default/even header/footer, border and PAGE-field values.
- Added a complete local thesis fixture covering front matter, Chinese and
  English abstracts and keywords, H1-H3, figures, tables, equations,
  cross-references, algorithms, listings, citations, footnotes, bibliography,
  acknowledgements and appendices.
- Added offline inspect/validate/build acceptance tests that hash all source
  inputs before and after execution, inspect real OOXML parts, compare repeated
  RenderPlan and canonicalized Word XML, and prove style-only template variants
  retain document semantics.
- Added the HUT template to Hatch wheel package data and the PyInstaller native
  sidecar package-data list, with distribution contract tests.

## TDD Evidence

- `tests/test_acceptance.py` directly checks `styles.xml`, `document.xml`,
  `settings.xml`, section properties, document relationships and referenced
  header/footer parts rather than treating ZIP validity as formatting proof.
- OOXML assertions cover Normal and semantic style IDs, fonts, sizes, indents,
  spacing, fixed line spacing, widow control, TOC tabs/leaders, bibliography
  hanging indent, superscript citations, page distances, document grid,
  even/odd settings, six main header/footer relationships, blank first header,
  PAGE and absence of NUMPAGES.
- Input immutability covers Markdown, YAML, BibTeX and image bytes. Offline CLI
  execution removes AI credentials and installs a socket-blocking
  `sitecustomize.py`.
- Repeated builds compare renderer-neutral RenderPlan snapshots and C14N output
  for all `word/*.xml` and `word/*.rels` parts.
- The two-template test changes only template font/size policy and proves equal
  RenderPlan, text, fields, bookmarks, drawings, tables and equations. It also
  proves every canonicalized Word XML/relationship part except `styles.xml`
  remains identical while `styles.xml` changes.
- Structured negative acceptance covers missing, ambiguous and invalid
  templates plus a valid template missing a required semantic style.
- Wheel and sidecar template source lists are asserted equal so the two
  distribution paths cannot silently drift.
- A real wheel was built and installed into an isolated target; its resolver
  loaded `hut-master-2026` from installed package data.
- A real 21,871,952-byte macOS arm64 PyInstaller sidecar built the complete
  fixture outside the repository with network blocking enabled and produced a
  valid DOCX through parse, validate, compile, render and finalize.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_acceptance.py -q`
  -> `7 passed in 8.40s`.
- `.venv/bin/python -m pytest tests/test_acceptance.py tests/test_cli.py tests/test_application_services.py tests/test_docx_renderer.py -q`
  -> `116 passed in 12.42s`.
- `.venv/bin/python -m pytest tests/test_desktop_distribution.py -q`
  -> `22 passed in 1.95s`.
- `.venv/bin/python -m pytest -q`
  -> `359 passed in 36.42s`.
- `.venv/bin/ruff check .`
  -> `All checks passed`.
- `.venv/bin/python -m pip check`
  -> `No broken requirements found`.
- `git diff --check`
  -> passed.
- `OPENSPEC_TELEMETRY=0 openspec validate template-driven-thesis-formatting-p0 --strict --no-interactive`
  -> valid.
- `.venv/bin/python -m build --wheel --outdir <temporary-directory>`
  -> built `thesis_forge-0.1.0-py3-none-any.whl`; archive inspection found all
  three template-data entries, including the HUT template.
- Installed-wheel resolver probe
  -> loaded `hut-master-2026` from
  `thesis_forge/template_data/schools/hunan-university-of-technology/master-2026.yaml`.
- `.venv/bin/python scripts/build_sidecar.py --target-triple aarch64-apple-darwin --output-directory <temporary-directory>`
  -> native sidecar built successfully.
- Frozen sidecar streamed build with `THESISFORGE_BLOCK_NETWORK=1`
  -> parse/validate/compile/render/finalize progress and success; generated
  package passed `validate_docx_package`.
- `pnpm frontend:test`, `pnpm frontend:typecheck`, `pnpm frontend:lint`,
  `pnpm frontend:build`
  -> `53` frontend tests and all static/build checks passed.
- `pnpm frontend:e2e`
  -> shared browser suite `15 passed, 18 skipped`; real Python HTTP adapter
  `1 passed`.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check`,
  `cargo test --manifest-path src-tauri/Cargo.toml`,
  `cargo check --manifest-path src-tauri/Cargo.toml`
  -> formatting/check passed and `11` protocol tests passed.
- `codegraph sync .`
  -> synchronized current files with no pending changes.
- Final CodeGraph evidence `ev-mshhrcno`
  -> matched `development:task-007-school-template-e2e` with no blockers.

## Concerns

- Microsoft Word/WPS sensory review is intentionally deferred to task 008.
- The first Playwright attempt could not launch because the pinned Chromium
  binary was absent. After installing the locked Playwright Chromium build, the
  unchanged E2E suite passed.
- Rust emitted non-functional warnings because the external volume does not
  support incremental-cache hard links; Cargo copied files and all checks
  passed.
- Initial independent reviews requested stronger failure-path, semantic
  equivalence, package-list consistency and recursive hardcoding evidence.
  Those findings were fixed and the updated focused/full suites passed.

## Scope Deviations

- The task allowlist was expanded before implementation to include
  `pyproject.toml`, `scripts/build_sidecar.py` and
  `tests/test_desktop_distribution.py`. This is required so the school template
  remains available in installed wheels and packaged macOS/Windows sidecars,
  rather than only in a source checkout.

## Follow-up Needed

- Task 008 must complete Word or WPS sensory review, acceptance A10 and final P0
  verification handoff.

## Adjudication

Tasks 7.1-7.7 are implemented with direct offline, OOXML, determinism and
distribution evidence. School-specific values remain in YAML/fixtures/tests and
were not added to renderer constants. Initial independent findings were fixed;
the final independent spec and quality reviews both approved the diff with no
required fixes.
