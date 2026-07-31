## Context

ThesisForge 当前是 Python 3.11+ 项目骨架，已经存在：

- dataclass-based `ThesisDocument` 与基础 Block/Inline types；
- 手写 Markdown/semantic-container parser；
- duplicate ID、missing reference/image、heading jump validator；
- Pydantic Template Model；
- Compiler 到 untyped `RenderPlan` 的最小映射；
- python-docx smoke renderer；
- Parser、Template 和 Validator 的少量 tests。

目标架构和不可破坏边界已经写入项目文档及 foundation specs。主要缺口不是重新选型，
而是把现有分层扩展成完整、可测试、离线的论文编译链路。

Stakeholders 包括论文作者、学校模板维护者、核心开发者、Office 输出审核者，以及未来
UI/AI adapter 开发者。

## Goals / Non-Goals

**Goals:**

- 完成 Markdown 到 `ThesisDocument` 的 V1 语义覆盖。
- 提供可组合、结构化且上下文完整的 validation。
- 让学校版式全部来自强类型 Template Model。
- 在 Compiler 中统一解析编号、bookmark、reference、citation 和 section。
- 用 typed RenderPlan 隔离 Domain 与 DOCX/OOXML。
- 生成真实、可编辑的 Word fields、bookmarks、OMML、footnotes 和 sections。
- 提供本地 BibTeX 与 GB/T 7714-2025 formatter contract。
- 打通离线 inspect/validate/build 与原子输出。
- 建立 unit、integration、OOXML structure、redteam 和 sensory verification。

**Non-Goals:**

- 本变更不实现生产桌面 UI、暗色主题或 i18n runtime；但提供隔离的 HTML review prototype。
- 不增加数据库、Web API、账号、云存储、多人协作或后台 worker。
- 不让 AI 进入核心编译依赖。
- 不直接复制参考仓库实现；需要借鉴时先审查许可证并记录来源。

## Decisions

### 1. 保留单向编译流水线

采用 `Parser -> ThesisDocument -> Validator -> Compiler -> RenderPlan -> Renderer`。

Rationale: 该结构已经是项目明确合同，能同时保证语义可测试、模板可替换和 Renderer
可演进。替代方案“解析时直接写 DOCX”会让编号、交叉引用、校验和模板切换不可维护。

### 2. Parser 使用确定性状态机，不引入必需 Pandoc runtime

在当前 parser 上扩展 block/inline state machine，并把语法支持保持在
`docs/MARKDOWN_SPEC.md` 可验证范围内。Pandoc 仅作语义参考或未来可选 backend。

Rationale: V1 必须离线、易安装且行为可控。直接依赖 Pandoc 会增加外部二进制和 AST
兼容成本。

### 3. Domain types 保持 renderer-neutral

Domain 使用 dataclasses；Template 使用 Pydantic；Word XML 和 python-docx objects 只存在于
`renderers/docx/`。所有 referencable block 使用稳定 ID 和 source location。

Rationale: dataclasses 适合不可耦合领域模型，Pydantic 适合用户 YAML 输入验证。统一改成
python-docx model 或 dict 会降低边界清晰度。

### 4. Validation 采用 context + rules 组合

引入 ValidationContext，包含 source root、template、bibliography 和 resource policy。
每条 rule 返回 `ValidationIssue[]`，最终按 source line、severity、code 稳定排序。

Rationale: 当前单函数可继续兼容，但 V1 规则跨文档、模板和文献，需要可组合边界。避免
validator 直接 print 或抛出首个用户错误。

### 5. Template Model 明确单位与样式结构

页面、字体、段落、标题、caption、numbering、sections、headers/footers、citation 都进入
Pydantic models。长度通过单一 unit parser 转换为 internal value。

Rationale: Renderer 不应理解学校 profile；无约束 dict 会把字段错误推迟到渲染阶段。

### 6. Compiler 先解析全局语义，再生成 typed RenderPlan

Compiler 分两步：

1. 建立 document index、chapter context、numbering、bookmark 和 citation maps。
2. 生成 typed render instructions。

迁移期间保留 `RenderNode` compatibility adapter，但新能力不继续扩散 magic payload keys。

Rationale: SEQ/REF/TOC 和跨章节编号需要全局视图，不能按 block 单次即时渲染。

### 7. OOXML 能力拆成 focused helpers

`renderers/docx/` 下按能力拆分：

- units/fonts/styles；
- fields/bookmarks/references；
- figures/tables；
- equations/OMML；
- footnotes；
- sections/headers/footers/page numbers；
- package/XML inspection helpers for tests。

Rationale: python-docx 高层 API 不覆盖全部 Word 对象；集中在单文件会混合模板、编号和 XML
职责。

### 8. LaTeX 到 OMML 使用可替换 converter contract

Domain 保存 LaTeX；Compiler 生成 equation instruction；Renderer 调用
`MathConverter` contract 产生 OMML。V1 先支持项目示例和常用结构，unsupported input
产生明确 validation/render error，不静默转 PNG。

Rationale: 真实可编辑公式是硬要求，但完整 TeX 引擎超出 V1。contract 允许后续更换更完整
实现。

### 9. Bibliography 使用本地 loader + formatter interface

BibTeX loader 负责 records 与 key validation；formatter 负责 inline citation 和
bibliography entries。citeproc-py 可作为 optional backend，但 core contract 和基本
GB/T golden fixtures 不依赖网络。

Rationale: 将数据加载与 style formatting 分开，避免 CLI/Renderer 直接解析 BibTeX。

### 10. Build 使用临时文件和原子替换

Renderer 写入同目录临时 DOCX，成功关闭并完成 package smoke validation 后再替换目标。
失败时清理临时文件并保留此前有效输出。

Rationale: 论文构建可能在 XML、图片或文件权限阶段失败，不能破坏用户已有成果。

### 11. 以垂直切片推进

实现顺序：

1. 测试环境与 architecture guards。
2. Parser/Domain coverage。
3. Validation/Template coverage。
4. typed RenderPlan 与基础 DOCX。
5. Figure/Table。
6. Equation/OMML。
7. Bookmark/SEQ/REF/TOC/Section/Page。
8. Bibliography。
9. full example、atomic build、verification。

Rationale: 每个切片都能通过 CLI 和 tests 形成可观察结果，避免先搭大量未集成 helper。

## Risks / Trade-offs

- [Risk] Word、WPS、LibreOffice 对 field update 行为不同 -> 生成标准 field XML，设置
  update-on-open，并记录至少一种目标客户端检查。
- [Risk] python-docx 不支持全部 OOXML -> 所有低层 XML 放入 focused helpers，并用 package
  XML tests 锁定。
- [Risk] LaTeX coverage 不完整 -> 定义 supported subset、明确失败和可替换 converter。
- [Risk] GB/T 7714-2025 细节复杂 -> 使用 golden fixtures，分离 loader/formatter，并在引入
  citeproc/CSL 前检查版本与许可证。
- [Risk] 手写 Markdown parser 边界增多 -> 语法严格文档化、状态机小步扩展、每个语义对象
  配套 tests；保留未来可选 backend。
- [Risk] V1 变化面过大 -> 按垂直切片提交，每个 task 有独立验证，未完成高级能力不得伪装成功。
- [Risk] AppleDouble `._*` 文件污染扫描和 package -> 工具和 tests 显式忽略，不把其当源码。
- [Trade-off] V1 不做 UI/i18n -> 更快完成核心，但后续 UI 需要单独的 prototype/requirements
  change。

## Migration Plan

1. 建立项目本地虚拟环境并恢复 pytest/ruff 可重复执行。
2. 增加 architecture/import guards，保护现有不可破坏边界。
3. 扩展 Domain/Parser，同时保持现有 `parse_markdown` contract。
4. 扩展 Template/Validator，同时保持现有 `load_template` 和
   `validate_document(doc)` compatibility。
5. 引入 typed RenderPlan，提供旧 `RenderNode` adapter 直到 renderer 迁移完成。
6. 按 capability 添加 DOCX helpers 和 XML tests。
7. 接入 bibliography 与完整 build service。
8. 更新示例与文档，执行 full test/ruff/build/package/Office review。

Rollback: 每个垂直切片保持 tests 绿色；若高级 renderer 失败，回退该 helper/typed node，
不删除用户 source/template，不覆盖已有有效 output。

## Open Questions

None for requirements handoff. Unsupported LaTeX constructs and完整 GB/T fixture coverage are
implementation/test backlog items, not unresolved product decisions.
