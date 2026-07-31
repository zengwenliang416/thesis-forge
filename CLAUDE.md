# AGENTS.md — ThesisForge 开发约束

本文件面向 Codex / Claude Code / Cursor 等代码代理。

## 0. 目标

ThesisForge 是一个**本地优先、确定性、模板驱动**的学术论文编译器：

```text
Markdown → ThesisDocument → Validation → Template → RenderPlan → DOCX
```

基础功能不依赖任何 AI 服务，不绑定任何单一模型。

## 1. 不可破坏的架构规则

### 1.1 禁止 Markdown 直接写 DOCX

错误：

```text
markdown_parser.py → python-docx
```

正确：

```text
Markdown Parser
    ↓
ThesisDocument
    ↓
Compiler / RenderPlan
    ↓
DOCX Renderer
```

Parser 不允许 import `docx`、`lxml` 或 Renderer。

### 1.2 AST / Domain Model 不包含 Word 实现细节

`core/model.py` 中不得出现 `w:p`、`w:r`、`CT_P`、`WD_ALIGN_PARAGRAPH`、`docx.Document` 等实现对象。

### 1.3 AI 不能成为编译依赖

以下命令必须在无网络、无 API Key 条件下正常工作：

```bash
thesisforge inspect thesis.md
thesisforge validate thesis.md
thesisforge build thesis.md
```

AI 相关代码仅允许位于 `src/thesis_forge/ai/` 或调用该层的 UI/service 中。

### 1.4 学校样式不得写死在核心代码

学校要求必须来自 Template Model。字体、字号、页边距、行距等不允许散落在 Renderer 业务逻辑里。

### 1.5 Word 高级能力必须是真对象

优先实现真实：

- TOC Field
- SEQ Field
- REF Field
- Bookmark
- OMML
- Footnote
- Section
- Header / Footer
- Page Number Field

不要用普通文字伪造目录、题注编号、交叉引用或公式。

## 2. V1 优先级

1. Parser
2. ThesisDocument
3. Template Model
4. Validator
5. Basic DOCX Renderer
6. Figure / Table
7. Equation / OMML
8. Bookmark / REF / SEQ
9. TOC / Section / Page Number
10. Bibliography
11. UI
12. AI

V1 核心未打通前，不要优先开发 AI 聊天侧栏、账号系统或模板市场。

## 3. 数据模型原则

所有可被引用的对象必须有稳定 ID：

```text
chap:
sec:
fig:
tbl:
eq:
alg:
lst:
```

Parser 阶段不计算最终“图 3-2 / 表 4-1 / 式（3-1）”编号，编号由 Compiler 统一计算。

## 4. Validation 原则

每增加一个语义对象，至少考虑：

- ID 是否重复
- 资源是否存在
- 是否允许被引用
- 引用 target 是否存在
- 标题层级是否合法
- 是否需要编号
- 模板是否定义对应样式

用户输入问题返回结构化 `ValidationIssue`，不要直接散落 `print()`。

## 5. 测试要求

至少覆盖：

- Front Matter
- Heading
- Figure
- Table
- Equation
- Citation
- CrossReference
- Duplicate ID
- Missing Reference
- Missing Image
- Template loading
- DOCX smoke test

涉及 OOXML 的测试应检查 XML 结构，不只检查文件是否存在。

## 6. GitHub 参考仓库使用规则

参考清单见 `docs/REFERENCES.md`。

开发时：

1. 优先学习架构、测试方法、OOXML 处理思路；
2. 不直接复制大段代码；
3. 如确需吸收具体实现，先检查 LICENSE；
4. 在相关源码旁写来源注释；
5. 重大借鉴记录到 `docs/THIRD_PARTY_NOTES.md`；
6. `references/external/` 永不提交。

### Word / DOCX

- `python-openxml/python-docx`
- `AfishInLake/WordFormat`
- `wzbwan/gongwen-format-skill`
- `Drenches/gov-doc-formatter`
- `xkonglong/gw`

### Markdown / AST

- `jgm/pandoc`

### Bibliography

- `citeproc-py/citeproc-py`
- `citation-style-language/styles`

### UI

- `zhiyiYo/PyQt-Fluent-Widgets` 仅作交互和视觉参考；引入前单独检查许可。

## 7. 提交前检查

```bash
pytest
ruff check .
```

如果修改 Markdown 语法：更新 `docs/MARKDOWN_SPEC.md` + Parser 测试 + 示例。

如果修改模板字段：更新 `docs/TEMPLATE_SPEC.md` + Template Model + 测试。

如果修改 DOCX XML：增加 XML 结构测试，并人工验证 Word/WPS/LibreOffice 至少一种目标环境。
