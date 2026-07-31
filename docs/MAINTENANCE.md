# ThesisForge Maintenance Guide

This guide defines the reproducible local verification and distribution path for
the ThesisForge V1 core. Product commands remain offline after dependencies are
installed.

## Supported Environment

- Python 3.11 or newer.
- A local virtual environment.
- OpenSpec CLI for lifecycle validation.
- LibreOffice is optional for manual Office compatibility review.

Create the development environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
make install
```

The project does not require AI credentials for `inspect`, `validate`, `build`,
tests, linting, distribution verification or OpenSpec validation.

## Daily Checks

Run the complete maintainer gate:

```bash
make verify
```

This executes:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m pip check
.venv/bin/python -m build --no-isolation --outdir dist
.venv/bin/python scripts/verify_distribution.py --dist-dir dist
OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-v1-core --strict --no-interactive
git diff --check
```

`verify_distribution.py` inspects wheel and sdist contents, rejects AppleDouble
files, checks the console entry point and bundled templates, installs the wheel
without dependency downloads into a temporary isolated prefix, then runs
`inspect`, `validate` and `build` from outside the repository with network
connections blocked. The verifier also proves the temporary install did not
replace or remove the maintainer environment's editable package.

For hermetic execution, the verifier copies only the installed recursive
closure of `[project].dependencies` into the prefix, evaluates PEP 508 markers
with no extras, and launches the generated console script through `python -S`.
It fails if checkout paths or parent `purelib`/`platlib` appear on `sys.path`,
or if ThesisForge, Typer, Rich, PyYAML, python-docx, lxml or Pydantic resolve
outside the temporary prefix.

## Example Build

```bash
make inspect
make validate
make build-example
```

The default output is `output/thesis.docx`. Build uses a same-directory
temporary file, validates the DOCX package and atomically replaces the target
only after all stages succeed.

## Distribution Boundary

`make package` creates:

```text
dist/thesis_forge-<version>-py3-none-any.whl
dist/thesis_forge-<version>.tar.gz
```

The wheel bundles the base and example-university templates under
`thesis_forge/template_data/`. The sdist includes source, templates, examples,
tests, specifications and maintenance scripts.

These artifacts are locally installable verification distributions. The
repository has not selected a project license, so do not publish them to a
public package index until ownership and license review are complete.

## Change Checklist

- Markdown syntax changes require `docs/MARKDOWN_SPEC.md`, parser tests and an
  example update.
- Template fields require `docs/TEMPLATE_SPEC.md`, Template Model tests and
  renderer/compiler coverage.
- DOCX XML changes require direct package/XML assertions and at least one
  Word/WPS/LibreOffice review.
- Third-party implementation reuse requires an entry in
  `docs/THIRD_PARTY_NOTES.md` before merge.
- Core commands must continue to pass with network blocked and AI credentials
  absent.
- Release candidates require the complete `make verify` gate and review of the
  active SpecNav task reports, ledgers, drift checks and handoff contract.
