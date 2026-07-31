# Prototype Question: build-thesisforge-v1-core

## Question

未来 ThesisForge 桌面工作台采用“论文大纲 + Markdown 编辑器 + Word 纸张预览 +
结构化诊断”的三栏学术编辑布局，是否能够让论文作者在本地完成模板选择、问题定位和
DOCX 构建，并清楚理解确定性编译链的当前状态？

## Branch

`ui-html`

## Review Target

- Entry: `artifact/index.html`
- Variant: `academic-three-pane`
- Generation source: Open Design project `thesisforge-html-workbench-20260729`
- Required reviewer decision: 是否批准该信息架构、视觉方向、移动端 tabs 和状态交互作为未来桌面 UI 的开发依据。

## Out of Scope

- 生产 PySide6 UI。
- 真实文稿保存、DOCX 渲染和本地文件选择。
- 数据库、账号、云端同步或网络服务。
- 暗色主题、主题切换、运行时多语言和语言切换。
