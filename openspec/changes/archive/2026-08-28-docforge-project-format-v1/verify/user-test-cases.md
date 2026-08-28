# User-Aligned Test Cases: docforge-project-format-v1

## User Test Case Scope

- Immutable snapshot: `snapshot-e34e5e74c6ac469ee8bce2be`
- Snapshot hash: `e34e5e74c6ac469ee8bce2be6d0b6ce1e772d4e773710b8bc782cc99da337c85`
- Human approval: `approval-e34e5e74c6ac469ee8bce2be` by `zengwenliang416`
- Sources: requirements, acceptance, prototype handoff, development handoff, and current-HEAD task receipts.

## Aligned Test Cases

### `case-a1-project-open` - Open a canonical DocForge project

- Actor: `document-author`
- Goal: Prove directory and manifest project entry use the strict DocForge v1 contract.
- Acceptance: `A1`
- Runner: `/bin/sh -c PYTHONPATH=src .venv/bin/python -m pytest tests/project tests/application/test_project_services.py -q`
- Expected: The strict DocForge project entry contract passes.

### `case-a10-repository-delivery` - Verify repository and release delivery contracts

- Actor: `release-maintainer`
- Goal: Prove active repository surfaces and local release artifacts use DocForge identities and neutral filenames.
- Acceptance: `A10`
- Runner: `/bin/sh -c set -eu; PYTHONPATH=src .venv/bin/python scripts/check_facticity.py --json /tmp/docforge-case-a10.json --markdown /tmp/docforge-case-a10.md; PYTHONPATH=src .venv/bin/python scripts/verify_desktop_distribution.py --platform macos --bundle-root src-tauri/target/release/bundle; PYTHONPATH=src .venv/bin/python scripts/prepare_release.py --tag v0.1.0 --validate-only`
- Expected: Repository-owned and local release surfaces use the DocForge delivery contract.

### `case-a2-general-project` - Build a general DocForge project

- Actor: `general-document-author`
- Goal: Prove a neutral general project completes inspect, validate, review, and build without academic metadata.
- Acceptance: `A2`
- Runner: `/bin/sh -c set -eu; tmp=$(mktemp -d /tmp/docforge-a2.XXXXXX); trap 'rm -rf "$tmp"' EXIT; cp -R tests/fixtures/docforge-general "$tmp/project"; PYTHONPATH=src .venv/bin/python -m docforge.cli inspect "$tmp/project" >/dev/null; PYTHONPATH=src .venv/bin/python -m docforge.cli validate "$tmp/project" >/dev/null; PYTHONPATH=src .venv/bin/python -m docforge.cli review "$tmp/project" >/dev/null; PYTHONPATH=src .venv/bin/python -m docforge.cli build "$tmp/project" >/dev/null; test -s "$tmp/project/review/document.review.md"; test -s "$tmp/project/review/document.review-map.json"; test -s "$tmp/project/build/document.docx"`
- Expected: The general project completes the neutral offline flow without academic requirements.

### `case-a3-academic-profile` - Build an academic profile without global leakage

- Actor: `academic-author`
- Goal: Prove academic fields are typed and template-scoped while general documents remain valid.
- Acceptance: `A3`
- Runner: `/bin/sh -c PYTHONPATH=src .venv/bin/python -m pytest tests/templates tests/compiler tests/project tests/test_distribution.py -q`
- Expected: Academic profile requirements do not leak into general projects.

### `case-a4-obsolete-contracts` - Reject obsolete ThesisForge contracts

- Actor: `maintainer`
- Goal: Prove obsolete active identities are absent or rejected without aliases.
- Acceptance: `A4`
- Runner: `/bin/sh -c set -eu; PYTHONPATH=src .venv/bin/python -m pytest tests/test_facticity.py tests/core/test_forge_document.py tests/project -q; PYTHONPATH=src .venv/bin/python scripts/check_facticity.py --json /tmp/docforge-case-a4.json --markdown /tmp/docforge-case-a4.md`
- Expected: No obsolete ThesisForge contract remains active.

### `case-a5-neutral-default-paths` - Use neutral source, build, and Review defaults

- Actor: `document-author`
- Goal: Prove canonical filenames match across project, CLI, runtime, and desktop contracts.
- Acceptance: `A5`
- Runner: `/bin/sh -c PYTHONPATH=src .venv/bin/python -m pytest tests/project tests/cli tests/contracts tests/test_desktop_distribution.py -q`
- Expected: Canonical neutral default paths match across all product layers.

### `case-a6-path-security` - Enforce project path security

- Actor: `security-reviewer`
- Goal: Prove safe project-relative resources are accepted and unsafe path classes are rejected.
- Acceptance: `A6`
- Runner: `/bin/sh -c set -eu; PYTHONPATH=src .venv/bin/python -m pytest tests/project tests/application/test_project_services.py -q; /Users/wenliang_zeng/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml project_tests`
- Expected: All unsafe project path classes are rejected without weakening safe relative paths.

### `case-a7-deterministic-docx` - Preserve the deterministic DOCX pipeline

- Actor: `document-compiler-maintainer`
- Goal: Prove semantic ordering, renderer boundaries, OOXML structures, cancellation, deterministic output, and atomic replacement.
- Acceptance: `A7`
- Runner: `/bin/sh -c PYTHONPATH=src .venv/bin/python -m pytest tests/core tests/compiler tests/renderers/docx tests/application tests/test_acceptance.py tests/test_compiler.py tests/test_docx_renderer.py -q`
- Expected: The semantic-to-DOCX pipeline remains deterministic, ordered, cancelable, and atomic.

### `case-a8-runtime-parity` - Keep Python, TypeScript, Rust, HTTP, and Tauri protocol parity

- Actor: `runtime-maintainer`
- Goal: Prove all runtime boundaries use one strict versioned DocForge protocol and BuildReport identity.
- Acceptance: `A8`
- Runner: `/bin/sh -c set -eu; PYTHONPATH=src .venv/bin/python -m pytest tests/adapters tests/application/test_build_report_contract.py tests/application/test_build_stage_lifecycle.py -q; /Users/wenliang_zeng/.nvm/versions/node/v22.19.0/bin/pnpm --dir frontend test; /Users/wenliang_zeng/.cargo/bin/cargo test --manifest-path src-tauri/Cargo.toml`
- Expected: The versioned DocForge runtime and BuildReport contract is consistent across all boundaries.

### `case-a9-installed-office` - Verify installed DocForge and Microsoft Word preview evidence

- Actor: `desktop-document-author`
- Goal: Prove the installed macOS workbench uses neutral terminology and generated a valid Word PDF preview.
- Acceptance: `A9`
- Runner: `/bin/sh -c PYTHONPATH=src .venv/bin/python -c 'import hashlib,json,pathlib; root=pathlib.Path("openspec/changes/docforge-project-format-v1/development/tasks/006-workbench-desktop/evidence"); r=json.loads((root/"macos-native-acceptance.json").read_text()); p=root/r["evidence"]["screenshot"]; assert r["ok"] is True and r["status"]=="passed"; assert r["app"]["displayName"]=="DocForge" and r["runtime"]["manifest"]=="docforge.yaml" and r["runtime"]["source"]=="document.md"; assert r["build"]["output"]=="document.docx" and r["wordPreview"]["engine"]=="microsoft-word" and r["wordPreview"]["status"]=="available" and r["wordPreview"]["pdfGenerated"] is True; assert hashlib.sha256(p.read_bytes()).hexdigest()==r["evidence"]["screenshotSha256"]; assert r["bundleVerification"]["ok"] is True; print(json.dumps({"ok":True,"word":r["wordPreview"]["microsoftWordVersion"],"screenshotSha256":r["evidence"]["screenshotSha256"]}))'`
- Expected: Installed DocForge.app and Microsoft Word final preview evidence is internally consistent and content-addressed.

## User Signoff

Status: `approved` at `2026-08-27T06:27:15Z` by `zengwenliang416`.

Approval binds `snapshot-e34e5e74c6ac469ee8bce2be` and `e34e5e74c6ac469ee8bce2be6d0b6ce1e772d4e773710b8bc782cc99da337c85`.

## Domain Mapping

Every approved A1-A10 case is required in facticity, static, unit, redteam, e2e, and sensory. The machine-readable mapping is `verify/domain-case-matrix.json`.
