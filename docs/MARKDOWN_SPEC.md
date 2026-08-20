# ThesisForge Markdown Spec v0.2

ThesisForge Markdown = Markdown 基础结构（V1 子集，见下节）+ YAML Front Matter +
semantic containers + cross-reference syntax。

## Markdown 基础结构（V1 支持集）

V1 Parser 是基于逐行扫描的子集解析器，不支持完整 CommonMark。明确支持的基础
结构：

- ATX 标题（`#`–`######`）
- 段落（连续非空行合并为一个段落）
- 有序 / 无序列表
- 管道表格（仅 `::: table` 容器内）
- 围栏代码块（仅 `::: listing` 容器内）
- 数学公式（仅 `::: equation` 容器内）

V1 **不支持**下列通用 Markdown 构造：

- 粗体 / 斜体（`**...**`、`*...*`）
- 链接（`[text](url)`）
- 行内图片（`![alt](src)`）
- 顶层 ```` ``` ```` 围栏代码块（容器之外）
- 行内数学 `$...$` 的语义提取（按普通文本保留；数学内容应放入 equation 容器）

**当前行为：静默降级。** 以上构造不会被识别，所在行按普通段落文本原样保留，
Parser 不产生任何错误或警告。这些构造是已定方向、待 Parser 后端迁移后支持的
能力；后端选型见 `docs/update/adr/ADR-0001.md`（Parser 后端选型，撰写中）。

## Front Matter

Front Matter 可选；不提供时元数据为空映射。提供时必须以 `---` 起始并闭合：

```yaml
---
document:
  type: bachelor_thesis
thesis:
  title: "论文题目"
author:
  name: "张三"
render:
  template_id: "school-2026"
  bibliography: "./references.bib"
---
```

V1 完整示例还使用 `university`、`advisor`、`dates` 及更多 `thesis`、`author`
字段生成封面可见文本。这些元数据保持普通 YAML 映射；Parser 不写入学校字体或
Word 样式。`render.template_id`、`render.bibliography` 和
`render.citation_style` 是当前编译链读取的渲染配置。

## Heading

```markdown
# 绪论 {#chap:introduction}
## 研究背景 {#sec:background}
### 深度学习方法
```

标题可省略 ID，但需要被交叉引用的章、节必须使用 `chap:` 或 `sec:` 前缀。
标题文本同样做 inline 提取（CrossReference / Citation / FootnoteReference），
行列位置从标题文本起点计算。

## Paragraph And Inline Content

普通连续文本解析为 Paragraph。Parser 保留下列 inline object 的源码行列和出现顺序：

```markdown
如 @fig:model 所示，已有研究给出相关结论 [@smith2025, p. 12]。[^note]
```

- `@fig:model` → CrossReference
- `[@smith2025, p. 12]` → Citation
- `[^note]` → FootnoteReference
- 其余内容 → Text

Inline 提取适用于：段落、标题文本、列表项正文、容器 `caption:` 元数据值、
`::: table` 与 `::: algorithm` 的正文行、脚注定义（含续行）。Figure 的
`src`/`width`、Equation 的公式体、Listing 的代码体不做 inline 提取。

最终编号不在 Parser 阶段计算。

## List

V1 支持连续的有序列表和无序列表。两个空格表示一级缩进：

```markdown
- 第一项
  - 第二级项目

3. 从 3 开始
4. 下一项
```

Parser 保留列表类型、起始序号、marker、缩进层级、正文和源码位置。列表项正文
做 inline 提取。列表样式及 Word 编号形式由 Template、Compiler 和 Renderer 决定。

列表块的边界规则（当前实现行为，明确为规范）：

- 有序 / 无序 marker 类型切换会**截断当前列表块**，不同 marker 类型的后续行
  另起新列表块（`- 甲` 后紧跟 `1. 乙` 会产生两个 ListBlock）。该截断是静默
  的，不产生诊断。
- 不匹配列表语法的行（含空行）结束当前列表块；非空行转入段落缓冲。

## Figure

```markdown
::: figure {#fig:model}
src: "./images/model.png"
caption: "模型总体结构"
width: "85%"
:::
```

引用：`如 @fig:model 所示。`

## Table

```markdown
::: table {#tbl:results}
caption: "实验结果"

| 模型 | AUROC |
| --- | ---: |
| A | 0.91 |
| B | 0.94 |

:::
```

分隔行必须使用 Markdown 对齐标记；每个数据行的列数必须与表头一致。无效分隔行
或列数不一致会在编译阶段明确失败，不会生成伪表格。

表格正文行按原文保留在 `Table.markdown`，同时对其做 inline 提取（如单元格内
的 citation 会进入文档级索引）。

## Equation

```markdown
::: equation {#eq:loss}
$$
L=-\sum_i y_i \log \hat y_i
$$
:::
```

公式体可以省略 `$$` 包裹；Parser 在存在首尾 `$$` 时将其剥离，其余内容原样
保留为 `Equation.latex`。

## Algorithm

```markdown
::: algorithm {#alg:train}
caption: "训练流程"

1. 初始化参数；
2. 读取数据；
3. 前向计算；
4. 反向传播。
:::
```

算法正文按原文保留在 `Algorithm.body`，同时对其做 inline 提取。

## Listing

````markdown
::: listing {#lst:predict}
caption: "预测函数"
language: "python"

```python
def predict(x):
    return model(x)
```
:::
````

代码体外层的围栏可以省略。语言来源：`language:` 元数据优先；未提供时使用围栏
info string（如 ```` ```python ````）；两者都缺失时 `Listing.language` 为
`None`。围栏行本身不进入 `Listing.code`。

## Citation

## Inline Strong

`**text**` is parsed as a strong inline span and rendered as a real bold run in
DOCX output. The markers are not emitted into the generated document.

Italic text, links, and inline images remain outside the current supported
syntax and are preserved as literal paragraph text.

## Inline Code

Single-backtick spans such as `` `tenant_id` `` are parsed as inline code.
DOCX output removes the backtick markers, uses a monospace font, and marks the
run as `noProof` so Word/WPS does not apply spelling checks to identifiers.

```markdown
已有研究提出该方法 [@smith2025]。
多文献：[@smith2025; @wang2024]
带页码：[@smith2025, p. 12]
```

Parser 保存 citation key、原始 citation 文本和 locator，但不在解析阶段格式化引用。
BibTeX 路径和引用样式来自 Front Matter 的 `render.bibliography` 与
`render.citation_style`。

## Bibliography Placement

```markdown
# 参考文献 {#chap:references}

::: bibliography
:::
```

`::: bibliography` 解析为 renderer-neutral `BibliographyBlock`，只决定已解析参考
文献条目的插入位置。Parser 不读取 BibTeX、不验证 citation key、不计算 ordinal。

marker 内的 `source`、`style` 等键仅为保留语法，V1 的有效配置仍来自 Front Matter。
未提供 marker 时，Compiler 在存在有效 citation 的情况下把 referenced-only
bibliography instruction 追加到正文末尾。详细的本地 BibTeX 类型、错误和格式合同见
`docs/BIBLIOGRAPHY_SPEC.md`。

## 本地资源边界

`figure.src` 和 `render.bibliography` 默认相对当前 Markdown 文件所在目录解析。
解析后的真实路径不得通过 `..` 或符号链接越出该目录；越界时 Validator 返回
`resource-path-escape`，即使目录外文件真实存在也不会放行。

嵌入式应用如需使用共享资源目录，必须通过 `ValidationContext.resource_roots`
显式提供允许的根目录。CLI 默认不隐式扩大资源范围。

## Footnote

```markdown
这里有一个说明。[^note]

[^note]: 脚注正文。
```

脚注定义支持后续四空格或 Tab 缩进的续行：

```markdown
[^long]: 第一行。
    第二行。
```

脚注 label 在文档内稳定匹配 definition/reference；最终 Word footnote number 由 Compiler
和 Renderer 生成。

## Reserved IDs

```text
chap: chapter
sec:  section
fig:  figure
tbl:  table
eq:   equation
alg:  algorithm
lst:  listing
```

同一文档中 ID 必须唯一。

ID 必须符合 `<prefix>:<name>`。`name` 可使用字母、数字、下划线、连字符、点和冒号。
脚注 label 使用独立的 footnote namespace，不加入上述交叉引用 ID 前缀。

## 源码位置粒度

- Inline object（Text / CrossReference / Citation / FootnoteReference）：
  行列位置精确（`SourceLocation.line` + `column`）。
- 块级 object（Heading / Paragraph / ListBlock / 六种容器 / FootnoteDefinition）：
  **只有行号，`column` 恒为 `None`**。块级列号待 Parser 后端迁移后补齐
  （见 `docs/update/adr/ADR-0001.md`，撰写中）。

## Error Behavior

- YAML Front Matter 必须闭合且根节点必须是键值映射。
- Figure、Table、Equation、Algorithm、Listing、Bibliography semantic container
  必须由 `:::` 闭合；未闭合抛 `ParseError`，消息含容器起始行号。
- 未知 `:::` 容器类型与任何未识别的语法**静默降级**：相关行按普通段落文本
  原样保留，无错误、无警告（见「Markdown 基础结构（V1 支持集）」）。
- Parser 错误使用 `ParseError`，并尽可能提供源码行号。
- Parser 只读取输入，不写 DOCX、不修改 Markdown、不访问网络。
- Parser 为单文件解析：V1 无多文件 include 机制。

## 版式规则

`thesis.md` 不定义宋体、小四、页边距、行距等学校样式；这些全部进入学校 YAML 模板。

## 修订注记

- v0.2（2026-08-15）：与现有 Parser 实现对齐。新增「Markdown 基础结构（V1
  支持集）」明确支持/不支持构造及静默降级行为；补充标题、caption、表格与算法
  正文、列表项的 inline 提取范围；补充 equation 可省略 `$$`、listing 围栏
  info string 推断语言；新增列表块截断规则、「源码位置粒度」节（块级仅行号）、
  未知容器/语法降级策略与无多文件 include 的说明；标注待 ADR-0001 后端迁移后
  支持的能力。
- v0.1：初始版本。
