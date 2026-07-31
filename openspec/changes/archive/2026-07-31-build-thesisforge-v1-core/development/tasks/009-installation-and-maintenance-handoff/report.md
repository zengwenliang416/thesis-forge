# Task Report: 009-installation-and-maintenance-handoff

## Status

DONE_WITH_CONCERNS

## Files Changed

- `pyproject.toml`
- `Makefile`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/MARKDOWN_SPEC.md`
- `docs/TEMPLATE_SPEC.md`
- `docs/THIRD_PARTY_NOTES.md`
- `docs/MAINTENANCE.md`
- `scripts/verify_distribution.py`
- `tests/test_distribution.py`
- Task 009 packet, development ledgers, CodeGraph artifacts and final
  development handoff.

## What Changed

- Added `build` and Hatchling to the development extra so the documented
  no-isolation package build is available after `make install`.
- Added an explicit sdist content policy covering source, templates, examples,
  tests, specifications and maintenance scripts while excluding AppleDouble
  and Python cache files.
- Expanded the Makefile into one reproducible maintainer interface for pytest,
  Ruff, pip consistency, wheel/sdist build, distribution verification, strict
  OpenSpec validation and whitespace checks.
- Added a lightweight distribution verifier that checks wheel package data and
  console metadata, checks sdist maintenance content, rejects AppleDouble
  files, evaluates PEP 508 dependency markers through the explicit development
  `packaging` dependency, installs the wheel with `--no-index --no-deps`,
  proves installed modules do not come from the checkout or parent
  site-packages, blocks network connections, and runs the complete
  inspect/validate/build flow outside the repository with bundled templates.
- Added a pytest regression that builds the real wheel/sdist and invokes the
  same verifier used by maintainers.
- Reconciled README, architecture, Markdown/template specifications and
  third-party notes with the accepted V1 implementation, then added a
  maintainer guide with the exact verification and distribution boundary.
- Audited task packets 001 through 009, independent reviews, validation logs,
  drift checks, task ledgers and CodeGraph evidence before preparing the final
  development handoff.

## TDD Evidence

- Initial `.venv/bin/python -m build` failed with
  `No module named build` before development build dependencies were added.
- The first distribution regression built valid artifacts but failed when a
  child venv could not import Typer.
- A nested stdlib venv then exposed a Python 3.11 distribution-specific
  `ensurepip`/child-interpreter SIGABRT. The verifier was changed to a
  temporary `--prefix` install that does not require a nested interpreter.
- The first prefix implementation let pip consider the parent editable
  installation for uninstall. `--ignore-installed` and a regression asserting
  the parent module path before and after verification closed that side effect.
- Independent quality review then proved runtime dependencies still resolved
  from the parent development environment. The verifier now copies only the
  active recursive closure of declared runtime dependencies, launches with
  `python -S`, and rejects parent site-packages, checkout paths or key imports
  outside the temporary prefix.
- The corrected focused regression passed on Python 3.11 and Python 3.14.
- The final full suite passed on Python 3.11.11, Python 3.12.9 and Python
  3.14.4: `124 passed` in all three environments.

## Verification Commands

- `make verify` on Python 3.14.4 passed `124` tests, Ruff, pip check,
  wheel/sdist build, isolated distribution verification, strict OpenSpec and
  `git diff --check`.
- `make PYTHON=/tmp/thesisforge-009-py311/bin/python
  DIST_DIR=/tmp/thesisforge-009-py311-dist verify` passed the same gate on
  Python 3.11.11.
- `make PYTHON=/tmp/thesisforge-009-py312/bin/python
  DIST_DIR=/tmp/thesisforge-009-py312-dist verify` passed the same gate on
  Python 3.12.9.
- Wheel: `51` files, SHA-256
  `36c308bf7cf4038c26dab254455438c22519793668add8be753b631bce41984e`.
- Sdist: `86` files, SHA-256
  `faa635eb731f48ec35a384ecad42369911560236231e1438b4c5c951cbc17b6e`.
- Installed Python 3.11 wheel generated a `187059`-byte DOCX with SHA-256
  `4dfb71bd08722a6f0ace109e12f1c93cd92d51e0402d87ccc2f3e8be3a158e93`.
- Installed Python 3.12 wheel generated a `187059`-byte DOCX with SHA-256
  `b88c1bc1aeb1158aec51b694afef40ea9a4ce654e5b6b455b431e31c3b1d2a85`.
- Installed Python 3.14 wheel generated a `187059`-byte DOCX with SHA-256
  `30fdc01987931e52cd45013872fd99ac71954e6a08a1dfdc7f67822281691a05`.
- All installed modules resolved from temporary prefix `site-packages`; all
  template roots resolved from installed `thesis_forge/template_data`; parent
  editable module paths remained unchanged. Hermetic `sys.path` contained only
  the prefix and Python standard-library paths, and the active runtime closure
  contained `15` production distributions.
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-v1-core --strict
  --no-interactive` returned `Change 'build-thesisforge-v1-core' is valid`.
- CodeGraph evidence `ev-ms8ykosi` matches the distribution verifier, focused regression,
  CLI, package configuration and bundled templates with no blockers.
- SpecNav development entry returned `ok:true`.

## Concerns

- The project has not selected a license. Artifacts are verified for local
  installation but must not be presented as ready for public package-index
  publication.
- Word field expansion remains client-dependent: task 008 recorded that
  LibreOffice headless leaves TOC unexpanded and can report a NUMPAGES value
  different from exported physical PDF pages. The DOCX contains real dirty
  fields and update-on-open settings.
- DOCX archive hashes can differ across builds because byte-for-byte ZIP
  determinism is not a V1 requirement; normalized semantic structures remain
  the determinism contract.

## Scope Deviations

- None. No accepted Parser, Domain, Validator, Compiler, RenderPlan, DOCX or UI
  behavior changed.

## Follow-up Needed

- Six-domain verification is the next lifecycle stage.
- Public release, package-index publication and archive remain downstream
  decisions and retain the documented license boundary.

## Adjudication

Both independent reviewers approved the final checkout. Tasks `9.1` through
`9.4` are complete, CodeGraph verifies all nine development claims, and the
SpecNav development handoff contract returned `ok:true` with no blockers or
warnings. License/publication and Office-client observations remain documented
non-blocking boundaries for downstream verification and release decisions.
