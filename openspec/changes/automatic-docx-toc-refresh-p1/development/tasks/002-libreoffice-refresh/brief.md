# Task Brief: 002-libreoffice-refresh

## Goal

安装兼容 LibreOffice 的主机能够在隔离、超时受控的本地进程中更新一个临时 DOCX 的
目录索引和字段；未安装或失败时返回安全 no-op。

## Parent Artifacts

- `openspec/changes/automatic-docx-toc-refresh-p1/requirements.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/acceptance.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/prototype/handoff.md`

## Vertical Slice

从 executable discovery 到 isolated process/profile、UNO update/save 和 cleanup 完成一个
可注入、可独立测试的 application service，不接入 Renderer 或 adapter。

## In Scope

- 新增 `application/office_refresh.py`。
- 定义 `DocumentRefresher` contract 和默认 `LibreOfficeDocumentRefresher`。
- 覆盖 macOS、Linux、Windows executable candidates。
- 实现隔离 profile、私有 endpoint、hidden load、index/field update、same-file save、
  timeout 和 process/profile cleanup。
- 增加发现、缺失、失败和超时测试；真实 LibreOffice 证明可作为集成证据。

## Out Of Scope

- `build_service` 接入顺序、Renderer、UI、Word/WPS automation。
- 新增 Python runtime dependency 或远程服务。

## Files Allowed

- `src/thesis_forge/application/office_refresh.py`
- `tests/test_application_services.py`
- `openspec/changes/automatic-docx-toc-refresh-p1/development/tasks/002-libreoffice-refresh/*`
- `openspec/changes/automatic-docx-toc-refresh-p1/development/*.jsonl`
- `output/verification/automatic-docx-toc-refresh-p1/*`

## Interfaces / Seams

- `DocumentRefresher.refresh(path) -> bool`.
- Local executable and subprocess runner are injectable for deterministic tests.
- The refresher may modify only the passed temporary DOCX.

## Components To Create

- `DocumentRefresher`
- `LibreOfficeDocumentRefresher`
- `discover_libreoffice_executable`
- isolated UNO helper script/runner

## Components To Reuse

- Python `pathlib`, `tempfile`, `subprocess`, `shutil`, `socket` and `time`.
- Existing application typed boundaries and temporary output policy.

## Components To Extract

- Centralize all platform candidates and Office lifecycle in this module.
- Keep UNO code in one generated/helper script rather than embedding variants per platform.

## API / Data Flow Contracts

- `temporary DOCX -> optional local LibreOffice -> updated same temporary DOCX`.
- Missing or failed optional runtime returns `False` and leaves build policy to the caller.

## State / Error / Empty / Loading Behavior

- Loading: wait only within configured startup and refresh timeout.
- Empty: no document indexes is a successful no-op save.
- Error: catch optional runtime failures, terminate owned process and return `False`.
- Disabled: missing executable returns `False` without starting a process.
- File access: passed DOCX and owned temporary profile only.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_application_services.py -k libreoffice`
- `.venv/bin/ruff check src/thesis_forge/application/office_refresh.py tests/test_application_services.py`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume `soffice` is on PATH.
- Do not assume system Python can import UNO.
- Do not connect to or terminate an existing user LibreOffice instance.
- Do not treat optional refresh failure as permission to corrupt the DOCX.
