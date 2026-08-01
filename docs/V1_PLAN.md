# V1 Development Plan

## M0 — 规范与仓库骨架

- [x] README
- [x] AGENTS.md
- [x] Markdown 规范
- [x] Template 规范
- [x] GitHub 参考仓库
- [x] 基础 Domain Model
- [x] CLI 骨架
- [x] 示例项目

## M1 — Parser + AST

目标：`thesisforge inspect thesis.md`

验收：Front Matter、Heading、Paragraph、Figure、Table、Equation、Listing、Algorithm、CrossReference、Citation。

## M2 — Validator + Template

目标：`thesisforge validate thesis.md`

检查：duplicate id、missing ref、missing image、heading jump、template exists、required metadata。

## M3 — Basic DOCX

实现：A4 / margin、body、heading 1–4、中文/西文字体、字号、行距、首行缩进、段距、分页。

## M4 — Figure + Table

Figure：图片、题注、章编号、bookmark、宽度。  
Table：基础表格、三线表、题注、章编号、bookmark。

## M5 — Equation

- block LaTeX
- OMML
- equation number
- bookmark

## M6 — Cross References + Fields

- SEQ
- REF
- Bookmark
- TOC
- PAGE
- Section
- 前置部分罗马页码 / 正文阿拉伯页码（模板驱动）

## M7 — Bibliography

- BibTeX loader
- citation key validation
- CSL pipeline
- GB/T 7714-2025
- inline citations
- bibliography list

## M8 — End-to-end Compiler

目标：

```bash
thesisforge build thesis.md \
  --template templates/schools/example-university/2026.yaml \
  -o output/thesis.docx
```

验收样例至少包含 cover、摘要、TOC、三级标题、图、三线表、公式、交叉引用、引用、参考文献、致谢、附录。

## M9 — Cross-platform Workbench

使用 React + TypeScript + Vite 实现共用的 Outline / Editor / Preview /
Diagnostics / Template selector / Build 工作台。Web 通过版本化 HTTP adapter
访问 Python application services；macOS 和 Windows 使用 Tauri 2、command
bridge 与托管 Python sidecar 访问相同 services。

## M10 — AI Plugin

统一 provider；AI 不得改变 Compiler 的确定性行为。
