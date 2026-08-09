# Task Report: 008-regression-office-handoff

## Status

DONE_WITH_CONCERNS

## Files Changed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/renderers/docx/fonts.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `templates/schools/hunan-university-of-technology/master-2026.yaml`
- `docs/TEMPLATE_SPEC.md`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `tests/test_acceptance.py`
- `openspec/changes/template-driven-thesis-formatting-p0/tasks.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/development/task-ledger.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/development/validation-log.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/development/drift-check.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/development/handoff-to-verify.md`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/008-regression-office-handoff/sensory-review.md`
- Task 008 report and independent review records.

## What Changed

- User review found that the HUT heading color still inherited a theme color
  and the heading alignment/indentation did not match the requested
  left-aligned flush-left policy.
- `ParagraphStyleSpec` now exposes a reusable `color` parameter accepting
  `auto` or six hexadecimal digits. The shared DOCX style translator applies
  it to real `w:color` and removes `themeColor`, `themeTint` and `themeShade`
  overrides.
- The HUT YAML sets Heading 1-3 to `color: "000000"`, `alignment: left`,
  zero left/right indentation and zero first-line indentation. These values
  remain template policy rather than renderer constants.
- Rebuilt the complete thesis at commit `f59c81f` and inspected the saved
  package. Heading 1-3 each contain `w:color w:val="000000"`,
  `w:jc w:val="left"` and `w:ind` with `left/right/firstLine="0"`.
- Opened the byte-identical current artifact in WPS and reviewed Chinese and
  English abstracts, the real TOC field, Heading 1-3, body text, citations,
  figure, table, equation, bibliography, headers and page numbers.
- Re-ran Python, frontend, browser, Rust, package and static validation on the
  current commit and refreshed the CodeGraph and lifecycle evidence.

## TDD Evidence

- `.venv/bin/python -m pytest tests/test_template.py tests/test_compiler.py tests/test_render_plan.py tests/test_bibliography.py tests/test_docx_renderer.py -q`
  -> `156 passed in 2.22s`; this is the task 8.1 vertical-slice suite.
- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py tests/test_acceptance.py -q`
  -> `132 passed in 14.81s`.
- `.venv/bin/python -m pytest -q`
  -> `367 passed in 39.45s`.
- Template tests accept `auto` and six-digit colors, reject invalid values and
  assert the HUT Heading 1-3 color/alignment/indent parameters.
- Renderer tests assert explicit color serialization, uppercase normalization,
  removal of Word theme-color attributes and continued shared paragraph-style
  translation; lowercase `abcdef` is emitted as `w:color="ABCDEF"`.
- Complete acceptance tests inspect the built `styles.xml` and require Heading
  1-3 to use black text, left alignment and zero indentation while retaining
  all body, semantic, TOC, bibliography and section assertions.
- The current DOCX is `192447` bytes with SHA-256
  `14cc3a07788bae9f1f5d69e27713f8bcc9bd57cca459d366d136eb29571e3325`.

## Verification Commands

- `.venv/bin/ruff check .` -> passed.
- `.venv/bin/python -m build` -> built sdist and wheel.
- `.venv/bin/python -m pip check` -> no broken requirements.
- `openspec validate template-driven-thesis-formatting-p0 --no-color` -> valid.
- `OPENSPEC_TELEMETRY=0 openspec validate template-driven-thesis-formatting-p0 --strict --no-interactive`
  -> valid.
- `pnpm frontend:test` -> `53 passed`.
- `pnpm frontend:typecheck`, `pnpm frontend:lint`, `pnpm frontend:build`
  -> passed.
- Playwright shared suite on isolated port `4273`
  -> `15 passed, 18 skipped in 25.7s`.
- Playwright real Python HTTP adapter -> `1 passed in 6.3s`.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml` -> `11 passed`.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- `git diff --check` -> passed.
- `codegraph sync .` -> current production and evidence files synchronized.
- SpecNav CodeGraph guard/claims reports -> `ok: true`, task 008 matched and
  no unverified claims remain.

## Concerns

- LibreOffice lacked the configured Chinese fonts and did not update the TOC;
  its output is compatibility evidence only. WPS rendered the Chinese text and
  updated the current real TOC to editable dot-leader entries.
- The original browser command remains blocked by an unrelated process on port
  `4173`. An initial temporary-config attempt forwarded the port argument
  incorrectly and reproduced the same environment failure; the corrected
  isolated config passed without product changes.
- Earlier task-008 browser execution also found a missing pinned Playwright
  Chromium cache. Installing the lockfile-matched browser produced the passing
  results; this historical failure is retained and formally overturned by
  later system-executed passes.
- Microsoft Word automation reached the native open panel but timed out during
  file search. No Word rendering claim is made; complete WPS evidence satisfies
  the Word-or-WPS acceptance.

## Scope Deviations

- Verification was reopened after the user identified a real title-format
  defect. Commit `f59c81f` therefore changes the typed template model, shared
  DOCX style translator, HUT YAML, documentation and tests after task 008 had
  begun.
- The deviation is limited to the already approved
  `Template Model -> shared DOCX translator` seam and the A1 heading policy.
  No parser, domain, compiler, RenderPlan, CI, release or deployment contract
  changed.

## Follow-up Needed

- Independent spec and quality reviewers must approve the current commit and
  refreshed evidence before the task ledger can be closed.
- Six-domain verification should independently inspect the committed evidence;
  a Microsoft Word review remains optional supplemental coverage.

## Adjudication

The user-discovered heading defect was fixed through template parameters rather
than a school-specific renderer branch. Current automated, OOXML and WPS
evidence all reference commit `f59c81f` and DOCX SHA-256 `14cc3a...e3325`.
Environmental browser failures remain in the append-only validation ledger and
are retired only by exact later system-executed passing evidence.
