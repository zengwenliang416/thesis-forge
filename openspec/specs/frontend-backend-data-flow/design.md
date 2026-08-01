# Frontend-Backend Data Flow Spec

## Overview

ThesisForge 的浏览器、macOS 和 Windows 产品共用 React frontend。Web 通过 HTTP
adapter，Tauri 通过 command/sidecar adapter 调用 Python application services。
CLI、Web 和 desktop 必须复用同一 application flows，而不是另建编译逻辑。

## Flow Index

| Flow ID | Trigger | Entry UI | API/Service | Persistence | User Result |
| --- | --- | --- | --- | --- | --- |
| `FLOW-INSPECT` | 用户运行 `thesisforge inspect thesis.md` | CLI | Parser | local source read | 输出结构化文档摘要 |
| `FLOW-VALIDATE` | 用户运行 `thesisforge validate thesis.md` | CLI | Parser + Validator + Template/Bibliography validation | local source/template/resource reads | 输出诊断与稳定 exit code |
| `FLOW-BUILD` | 用户运行 `thesisforge build thesis.md` | CLI | Parser + Validator + Template + Compiler + Renderer | local reads and DOCX write | 生成可打开的 DOCX 或安全失败 |
| `FLOW-OPEN-SOURCE` | 用户选择 source/workspace | React | Web or Tauri transport | browser workspace or local read | 显示同一版本 source snapshot |
| `FLOW-SAVE-SOURCE` | 用户显式保存 | React | Web workspace or Tauri filesystem adapter | browser workspace/download or atomic local replace | 保存成功后解除 dirty |
| `FLOW-WEB-TRANSPORT` | 浏览器发起命令 | React | versioned HTTP adapter | deployment-scoped temporary workspace | 返回 serialized result/progress |
| `FLOW-TAURI-TRANSPORT` | desktop 发起命令 | React in Tauri | Tauri command + Python sidecar | local filesystem | 返回同一 serialized contract |

## Boundary Contracts

- UI event contract: CLI 命令或 typed frontend intent 转换为同一 application
  command semantics。
- Client state contract: React state 保存 workspace handle、saved text、dirty、
  selection、operation token、progress 和 diagnostics；默认无跨会话 cache。
- Request schema: source path 必填；build 接受 template path/id、output path 和后续 bibliography options。
- Response schema: inspect 返回结构摘要；validate 返回 `ValidationIssue[]` 与 exit code；build 返回 output path 与 diagnostics。
- Error schema: parser/template failures、validation issues、render failures必须区分；用户输入错误不得以散落 `print()` 作为领域接口。
- Permission contract: 只读输入路径与显式 output path；不得静默上传、修改源 Markdown 或写入未请求位置。

## State Ownership

- URL state: 无。
- Local component state: 无 UI；CLI 层只拥有当前 invocation state。
- Shared client cache: 无。
- Server state: Web adapter 只持有请求范围或有界 operation state；无 domain
  truth 或数据库持久化。
- Database state: 无数据库。
- Derived state: `ThesisDocument`、ID index、resolved numbering、bookmark map、RenderPlan、diagnostics。
- Persistent state: 用户本地 Markdown/YAML/BibTeX/images 和生成的 DOCX。

## Validation Ownership

- Client-side validation: CLI/frontend 校验参数、capability 和明显输入约束。
- Server-side validation: Web/sidecar adapter 校验 DTO 与 workspace boundary；
  application layer 调用 Parser、Template Model 和 Validator。
- Database constraints: 无。
- Cross-field or cross-entity rules: Validator 负责 duplicate ID、reference target、resource existence、heading hierarchy、metadata/template/citation consistency。
- Error copy source: Domain 提供稳定 code/target/line，CLI/UI adapter 负责中文展示文本和 exit code。
- Render validation: Renderer 前只接受已通过 fatal validation 的 RenderPlan；OOXML tests 验证真实对象结构。

## Error & Empty States

- Empty state: 空文档或无 blocks 产生明确诊断，不生成“成功但空白”的最终论文。
- Permission denied: 文件读写权限错误包含目标路径与操作类型，且不破坏已有输出。
- Validation error: 输出所有可收集问题；存在 `error` 时 build 不进入 Renderer。
- Network error: 核心流不访问网络；desktop 外部网络不可用不得影响
  inspect/validate/build。Web transport failure 必须与 domain validation 区分。
- Server error: adapter 内部异常转换为稳定 transport error，不伪装成
  validation success。
- Conflict/stale data: 编译使用单次读取快照；若输入在构建中变化，未来可通过 file metadata/hash 检测并要求重试。
- Missing resource: 缺图、缺模板、缺 BibTeX 或 citation key 均为结构化 issue。

## Loading / Optimistic / Retry Behavior

- Initial loading: CLI 同步读取；React UI 显示可取消的解析/编译进度。
- Partial loading: inspect/validate 可在安全时收集多个问题；build 在 fatal validation 后停止。
- Optimistic update: 无，不能先报告 build 成功再写 DOCX。
- Retry rule: 用户修复输入后可重复运行；同一输入的重试不依赖残留内存状态。
- Cancellation rule: CLI 使用进程取消；Web abort/Tauri cancel 必须映射为
  application cancellation，且不得留下半写 DOCX。
- Idempotency rule: inspect/validate 无副作用；build 对同一 output path 可安全重建，失败时保留此前有效文件。

## End-to-End Flow Details

### FLOW-INSPECT

1. User trigger: 用户执行 `thesisforge inspect <source>`。
2. UI state transition: CLI 进入读取与解析状态。
3. Request: source path。
4. Validation: 路径可读、Front Matter 和 Markdown syntax 可解析。
5. Database read/write: none；读取本地 Markdown。
6. Response: source、metadata、blocks、cross references、citations 的结构化摘要。
7. UI render result: stdout JSON-like output，成功 exit code 0。
8. Retry/idempotency: 可无副作用重复执行。
9. Rollback: 无写操作，无需 rollback。
10. Logging/metrics/audit event: 仅本地命令结果；默认不发送 telemetry。

### FLOW-VALIDATE

1. User trigger: 用户执行 `thesisforge validate <source>`。
2. UI state transition: CLI 解析后运行所有适用 validator rules。
3. Request: source path、解析出的 template/bibliography/resource context。
4. Validation: structural、reference、resource、template、bibliography rules。
5. Database read/write: none；只读本地输入与依赖资源。
6. Response: 有序 `ValidationIssue[]`，包含 severity、code、message、line、target。
7. UI render result: 无 error 时 exit 0；存在 error 时非零；warning 不阻止 build，除非规格另有规定。
8. Retry/idempotency: 修改输入后重跑；未修改时结果顺序稳定。
9. Rollback: 无写操作。
10. Logging/metrics/audit event: CLI 可输出摘要，不记录论文正文或凭据。

### FLOW-BUILD

1. User trigger: 用户执行 `thesisforge build <source> --template <template> -o <output>`。
2. UI state transition: parse -> validate -> resolve template/bibliography -> compile -> render -> finalize。
3. Request: source path、template selection、output path 及明确 build options。
4. Validation: 先完成 FLOW-VALIDATE；任何 fatal error 阻止 Compiler/Renderer。
5. Database read/write: none；读取本地资源，写临时 DOCX 后原子替换目标。
6. Response: 成功返回 output path；失败返回 structured diagnostics 和非零 exit code。
7. UI render result: 用户看到生成位置、warning 摘要或准确失败阶段。
8. Retry/idempotency: 同一输入可重复构建；编号和引用解析结果稳定。
9. Rollback: render/finalize 失败时删除临时文件并保留原有效 output。
10. Logging/metrics/audit event: 记录本地阶段与耗时时不得泄露论文正文；不依赖网络。

## Async / Realtime Flows

- Queue/event source: V1 无。
- Subscriber: V1 无。
- Retry/dead-letter behavior: V1 无队列；文件 I/O 重试必须有界且显式。
- Realtime update channel: Web 使用有界 event stream；Tauri 使用 command/sidecar
  progress events。
- Consistency expectation: 单次 build 使用不可变输入快照和确定性编号顺序。
- Future rule: 引入 worker、watch mode 或 preview 时，必须新增命名 FLOW 并说明取消、去重和 stale-result 处理。

## Flow Do's and Don'ts

- Do route CLI 与未来 UI through the same Parser/Validator/Compiler services.
- Do keep Web and Tauri behavior aligned through shared DTO fixtures.
- Do keep request, response, validation, error, retry/idempotency, and rollback behavior explicit.
- Do stop before rendering when fatal validation exists.
- Do preserve a previously valid DOCX when a rebuild fails.
- Don't add hidden third-party network calls, database writes, or optimistic success.
- Don't let Renderer parse Markdown or let UI duplicate numbering/reference logic.
- Don't mutate user source files during inspect, validate, or build.
