# Quality Review: 007-safe-and-repeatable-builds

## Verdict

approved

The prior blocking quality finding is closed on the current checkout. Task 007
now has direct deterministic coverage for the two package-integrity branches
that were previously only inferred from source inspection: CRC corruption and
duplicate ZIP-part rejection. No remaining blocker was found across Separation
Of Concerns, Component Cohesion / Coupling, Test Quality, Error Handling,
Reuse / Duplication, or Complexity Delta.

## Separation Of Concerns

- `build_service` 负责 parse -> validate -> compile -> render -> finalize 的应用层编排，没有把最终输出路径传给 Renderer；临时文件与替换边界被隔离在 [src/thesis_forge/application/output.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/output.py:13) 和 [src/thesis_forge/application/services.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/services.py:120)。
- CLI 仍是展示适配层：仅调用 application services 并把结构化失败映射到中文输出/exit code，没有重新实现 parse/validate/build 编排；这一点也有架构测试覆盖 [src/thesis_forge/cli.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/cli.py:87) [tests/test_architecture.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_architecture.py:74)。
- DOCX package smoke validation 留在 `renderers/docx/package.py`，没有泄漏到 Parser / Domain / Compiler 层，符合 task 007 的 application/output boundary 要求 [src/thesis_forge/renderers/docx/package.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/renderers/docx/package.py:46)。

## Component Cohesion / Coupling

- `ApplicationDependencies` 把 parser / validator / compiler / renderer / package validator / replace seam 集中在一个 dataclass 内，当前聚合度是合理的，且默认生产依赖仍是本地 Parser/Validator/Compiler/DOCX Renderer/`os.replace` [src/thesis_forge/application/services.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/services.py:46)。
- `build_service` 仍是单个可读的 orchestrator，核心职责清晰，没有把 CLI 或 Renderer 细节回灌到应用层；复杂度增量可控 [src/thesis_forge/application/services.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/services.py:120)。
- `replace_file` / `package_validator` 作为可注入 seam 仍然是合理的测试边界；这次 review-fix 之后，最关键的 safety-critical 分支已经从“源码可见”升级为“直接测试可证”，生产风险明显下降。

## Test Quality

- 正向覆盖总体不错：共享 inspect/validate 无输出副作用、五阶段 progress 顺序、fatal validation stop、旧输出保留、同目录临时文件清理、CLI 无 traceback、CLI/application 边界，以及 repeated-build 语义等价，都有直接测试 [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:118) [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:147) [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:166) [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:204) [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:274) [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:387) [tests/test_cli.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_cli.py:244)。
- 之前的唯一缺口已经被直接补齐：`test_docx_package_validation_rejects_crc_corruption()` 确定性破坏 `word/document.xml` 的 ZIP payload 并验证 `package.testzip()` 路径会拒绝该包 [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:352)；`test_docx_package_validation_rejects_duplicate_parts()` 直接向同一包追加第二个 `word/document.xml` 并验证 duplicate-part rejection [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:372)。
- `system-executed` 证据也已经刷新：focused application/CLI/architecture suite 现在是 `40 passed in 0.95s`，并明确包含这两条 package-integrity regression tests；full suite、Ruff 和 `pip check` 也都已通过 [openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl](/Volumes/zwl/open_sources/thesis-forge/openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl:117) [openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl](/Volumes/zwl/open_sources/thesis-forge/openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl:118)。

## Error Handling

- `ApplicationStageError` / `BuildValidationError` 让 parse / validate / compile / render / finalize 失败都带 stage 返回，CLI 也正确隐藏 traceback；这一点在实现和测试上都是成立的 [src/thesis_forge/application/contracts.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/contracts.py:41) [src/thesis_forge/cli.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/cli.py:24) [tests/test_cli.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_cli.py:53) [tests/test_cli.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_cli.py:261)。
- fatal validation 确实在 compile/render/finalize 前停止，旧输出保持不变，且不会留下 `.tmp.docx`，这部分风险已经被测试压住 [tests/test_application_services.py](/Volumes/zwl/open_sources/thesis-forge/tests/test_application_services.py:166)。
- package validator 作为 finalize 前最后一道防线，现在不仅有实现，还有直接失败证据支撑；此前的“严格性依赖源码阅读”问题已关闭。

## Reuse / Duplication

- `inspect_service` 被 `validation_service` / `build_service` 复用，`_validate_inspection()` 抽出了 parse 后的共享验证路径，避免 CLI 和应用层重复 orchestrate，复用方向正确 [src/thesis_forge/application/services.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/services.py:75) [src/thesis_forge/application/services.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/services.py:90)。
- `temporary_output_path()` 与 `replace_output()` 让临时文件生命周期和最终替换逻辑复用在单点，不存在同类逻辑散落多处的问题 [src/thesis_forge/application/output.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/output.py:13)。
- 当前没有看到需要额外抽象的新重复块；此前阻塞项也不是重复问题，而是测试闭环缺失，而这部分现已补齐。

## Complexity Delta

- 本任务新增的复杂度主要集中在 `build_service()` 和 `validate_docx_package()`，二者长度与嵌套仍在可审查范围内，没有出现 task 005 那种需要立即拆分的高复杂 orchestrator [src/thesis_forge/application/services.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/application/services.py:120) [src/thesis_forge/renderers/docx/package.py](/Volumes/zwl/open_sources/thesis-forge/src/thesis_forge/renderers/docx/package.py:46)。
- “安全构建”最后一道 validator 的证据强度现在与实现复杂度匹配：新的 deterministic corruption/duplicate tests 精确覆盖了此前未证实的分支，因此这一复杂度增量已被等量验证。

## Required Fixes

None for task 007.

The task ledger and validation log now match the final checkout state:

- `quality_review_needs_fix` is followed by `review_fix_complete_pending_rereview`
  for task 007 in the ledger [openspec/changes/build-thesisforge-v1-core/development/task-ledger.jsonl](/Volumes/zwl/open_sources/thesis-forge/openspec/changes/build-thesisforge-v1-core/development/task-ledger.jsonl:53) [openspec/changes/build-thesisforge-v1-core/development/task-ledger.jsonl](/Volumes/zwl/open_sources/thesis-forge/openspec/changes/build-thesisforge-v1-core/development/task-ledger.jsonl:54)。
- `validation-log.jsonl` records the direct package-integrity regression evidence
  and refreshed full-suite/static-check evidence [openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl](/Volumes/zwl/open_sources/thesis-forge/openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl:117) [openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl](/Volumes/zwl/open_sources/thesis-forge/openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl:118)。
