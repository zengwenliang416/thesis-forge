PYTHON ?= .venv/bin/python
CHANGE ?= build-thesisforge-v1-core
DIST_DIR ?= dist

.PHONY: install test lint dependency-check package verify-dist openspec-validate verify inspect validate build-example

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

dependency-check:
	$(PYTHON) -m pip check

package:
	$(PYTHON) -m build --no-isolation --outdir "$(DIST_DIR)"

verify-dist: package
	$(PYTHON) scripts/verify_distribution.py --dist-dir "$(DIST_DIR)"

openspec-validate:
	OPENSPEC_TELEMETRY=0 openspec validate "$(CHANGE)" --strict --no-interactive

verify: test lint dependency-check verify-dist openspec-validate
	git diff --check

inspect:
	$(PYTHON) -m thesis_forge.cli inspect examples/bachelor-thesis/thesis.md

validate:
	$(PYTHON) -m thesis_forge.cli validate examples/bachelor-thesis/thesis.md

build-example:
	$(PYTHON) -m thesis_forge.cli build examples/bachelor-thesis/thesis.md -o output/thesis.docx
