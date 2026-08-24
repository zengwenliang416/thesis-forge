PYTHON ?= .venv/bin/python
CHANGE ?= template-v2-build-pipeline-p1
WEB_DIST_DIR ?= dist/web
PYTHON_DIST_DIR ?= dist/python
SIDECAR_DIST_DIR ?= src-tauri/binaries
TARGET_TRIPLE ?= $(shell rustc --print host-tuple)

.PHONY: install test lint dependency-check package package-web package-sidecar verify-dist verify-desktop-dist frontend-verify tauri-verify openspec-validate verify inspect validate build-example

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

dependency-check:
	$(PYTHON) -m pip check

package:
	$(PYTHON) -m build --no-isolation --outdir "$(PYTHON_DIST_DIR)"

verify-dist: package
	$(PYTHON) scripts/verify_distribution.py --dist-dir "$(PYTHON_DIST_DIR)"

package-web:
	pnpm --dir frontend exec tsc -b
	pnpm --dir frontend exec vite build --outDir "../$(WEB_DIST_DIR)" --emptyOutDir

package-sidecar:
	$(PYTHON) scripts/build_sidecar.py --target-triple "$(TARGET_TRIPLE)" --output-directory "$(SIDECAR_DIST_DIR)"

verify-desktop-dist: package-sidecar
	$(PYTHON) scripts/verify_desktop_distribution.py --target-triple "$(TARGET_TRIPLE)" --sidecar-directory "$(SIDECAR_DIST_DIR)" --sidecar-only

frontend-verify:
	pnpm frontend:test
	pnpm frontend:typecheck
	pnpm frontend:lint
	pnpm frontend:build
	pnpm frontend:e2e

tauri-verify:
	cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
	cargo test --manifest-path src-tauri/Cargo.toml
	cargo check --manifest-path src-tauri/Cargo.toml

openspec-validate:
	OPENSPEC_TELEMETRY=0 openspec validate "$(CHANGE)" --strict --no-interactive

verify: test lint dependency-check verify-dist frontend-verify tauri-verify verify-desktop-dist openspec-validate
	git diff --check

inspect:
	$(PYTHON) -m thesis_forge.cli inspect examples/bachelor-thesis/thesis.md

validate:
	$(PYTHON) -m thesis_forge.cli validate examples/bachelor-thesis/thesis.md

build-example:
	$(PYTHON) -m thesis_forge.cli build examples/bachelor-thesis/thesis.md -o output/thesis.docx
