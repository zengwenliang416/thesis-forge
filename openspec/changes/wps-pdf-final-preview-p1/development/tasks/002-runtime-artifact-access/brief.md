# Task Brief: 002-runtime-artifact-access

## Goal

Web、macOS 和 Windows 能安全读取自动 PDF，并允许用户显式选择 WPS PDF，不向公共
构建 DTO 泄露私有绝对路径。

## Parent Artifacts

- `openspec/changes/wps-pdf-final-preview-p1/requirements.md`
- `openspec/changes/wps-pdf-final-preview-p1/acceptance.md`
- `openspec/changes/wps-pdf-final-preview-p1/prototype/handoff.md`

## Vertical Slice

从 application preview artifact 到 Web PDF bytes 和 Tauri picker/read bytes 完成跨运行时
访问边界。

## In Scope

- 扩展 runtime output presentation 和 strict build descriptor。
- 新增 workspace-bound Web PDF GET。
- 新增 Tauri `.pdf` picker、派生路径校验和 binary response reader。
- 扩展 Web/Tauri transport preview resolve/import 契约及测试。

## Out Of Scope

- PDF exporter internals、React viewer/state、WPS 自动化和文档更新。

## Files Allowed

- `src/thesis_forge/adapters/*`
- `tests/test_adapters.py`
- `tests/test_http_adapter.py`
- `tests/test_sidecar.py`
- `src-tauri/src/*`
- `src-tauri/tests/*`
- `frontend/src/transport/*`
- `openspec/changes/wps-pdf-final-preview-p1/development/tasks/002-runtime-artifact-access/*`
- `openspec/changes/wps-pdf-final-preview-p1/development/*.jsonl`

## Interfaces / Seams

- `RuntimePaths.present_output`.
- `WorkbenchHttpApp`.
- Tauri commands and `WorkbenchTransport`.
- Strict `FinalPreviewDescriptor`.

## Components To Create

- Web PDF artifact response.
- Tauri `pick_pdf_preview` and `read_pdf_preview`.
- Transport preview byte resolver.

## Components To Reuse

- `WebWorkspaceRuntime` workspace ID and plain-name validation.
- Existing Tauri rfd and IPC command bridge.
- Existing build event parser.

## Components To Extract

- Shared descriptor parser and PDF locator types in frontend transport modules.

## API / Data Flow Contracts

- Web descriptor -> workspace-bound GET -> `application/pdf` bytes.
- Desktop authorized derived/user-selected path -> binary IPC -> PDF bytes.

## State / Error / Empty / Loading Behavior

- Loading: byte resolution is an explicit asynchronous transport operation.
- Empty: no ready descriptor returns no bytes.
- Error: invalid path, extension, workspace or PDF returns typed transport failure.
- Disabled: picker cancellation is not an error.
- Permission: arbitrary local or cross-workspace reads are rejected.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_adapters.py tests/test_http_adapter.py tests/test_sidecar.py`
- `pnpm --dir frontend test -- --run frontend/src/transport`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Opaque IDs are not authentication.
- Do not allow arbitrary paths or non-PDF content through preview readers.
