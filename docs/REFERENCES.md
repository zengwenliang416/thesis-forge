# GitHub Reference Repositories

> 这些仓库是 ThesisForge 的**设计 / 实现参考**，不是 vendored 依赖。  
> 默认 clone 到 `references/external/`，该目录已被 `.gitignore` 排除。

## A. Word / 中文排版参考

### 1. AfishInLake/WordFormat

```bash
git clone https://github.com/AfishInLake/WordFormat.git references/external/WordFormat
```

参考重点：Word 格式规则化、配置驱动排版、格式检查/修改、Python Word 工程组织。

### 2. Drenches/gov-doc-formatter

```bash
git clone https://github.com/Drenches/gov-doc-formatter.git references/external/gov-doc-formatter
```

参考重点：中文公文格式参数、本地文档处理流程、样式模块组织、桌面/本地应用思路。

### 3. wzbwan/gongwen-format-skill

```bash
git clone https://github.com/wzbwan/gongwen-format-skill.git references/external/gongwen-format-skill
```

参考重点：确定性 DOCX 渲染、中文字体 / 行距 / 段落、Python OOXML 实践、内容与排版分离。

### 4. xkonglong/gw

```bash
git clone https://github.com/xkonglong/gw.git references/external/gw
```

参考重点：公文排版产品交互、Word/WPS 高频排版操作、“一键排版”的用户操作模型。

## B. DOCX / OOXML 底座

### 5. python-openxml/python-docx

```bash
git clone https://github.com/python-openxml/python-docx.git references/external/python-docx
```

ThesisForge DOCX Renderer 的基础依赖与源码参考。重点研究 Styles、Sections、Tables、Numbering、OxmlElement、package/part/relationship。

TOC、REF、SEQ、OMML、Footnote 等能力不足时，进入 OOXML 层实现。

## C. Markdown / AST

### 6. jgm/pandoc

```bash
git clone https://github.com/jgm/pandoc.git references/external/pandoc
```

参考重点：Pandoc AST、Markdown attributes、citations、math、figures/tables、DOCX writer 的语义处理。

V1 可把 Pandoc 当**可选解析后端 / 行为参考**，但不要把“Pandoc 直接导出 DOCX”当最终架构，因为学校论文需要更深度的 Word 字段与 OOXML 控制。

## D. Citation / CSL

### 7. citeproc-py/citeproc-py

```bash
git clone https://github.com/citeproc-py/citeproc-py.git references/external/citeproc-py
```

参考重点：CSL processor、Citation / Bibliography 渲染、Python Citation Engine。

### 8. citation-style-language/styles

```bash
git clone https://github.com/citation-style-language/styles.git references/external/csl-styles
```

参考重点：CSL 样式体系、GB/T 7714 相关 CSL、不同引文样式模板。

不要默认把整个 styles 仓库打进最终安装包；实际发行时只纳入许可和产品策略允许的样式文件。

## E. Desktop UI 参考

### 9. zhiyiYo/PyQt-Fluent-Widgets

```bash
git clone https://github.com/zhiyiYo/PyQt-Fluent-Widgets.git references/external/PyQt-Fluent-Widgets
```

仅作为桌面 UI / Fluent 交互参考。ThesisForge 推荐 PySide6；是否直接依赖第三方 UI 包需单独做许可证与发行评估。

---

# 使用原则

可以学习：架构、API 用法、测试策略、OOXML 技术点、用户交互、数据模型思想。

不要默认：直接复制源码、资源、字体、学校模板，或复制许可证不兼容实现。

如需吸收代码，在 `docs/THIRD_PARTY_NOTES.md` 记录：

```text
Source:
Commit:
File:
License:
What was reused:
Local file:
```
