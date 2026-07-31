# ThesisForge Markdown Spec v0.1

ThesisForge Markdown = Markdown 基础结构 + YAML Front Matter + semantic containers + cross-reference syntax。

## Front Matter

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

## Heading

```markdown
# 绪论 {#chap:introduction}
## 研究背景 {#sec:background}
### 深度学习方法
```

标题可省略 ID，但需要被交叉引用的章、节必须使用 `chap:` 或 `sec:` 前缀。

## Paragraph And Inline Content

普通连续文本解析为 Paragraph。Parser 保留下列 inline object 的源码行列和出现顺序：

```markdown
如 @fig:model 所示，已有研究给出相关结论 [@smith2025, p. 12]。[^note]
```

- `@fig:model` → CrossReference
- `[@smith2025, p. 12]` → Citation
- `[^note]` → FootnoteReference
- 其余内容 → Text

最终编号不在 Parser 阶段计算。

## List

V1 支持连续的有序列表和无序列表。两个空格表示一级缩进：

```markdown
- 第一项
  - 第二级项目

3. 从 3 开始
4. 下一项
```

Parser 保留列表类型、起始序号、marker、缩进层级、正文和源码位置。列表样式及 Word
编号形式由 Template、Compiler 和 Renderer 决定。

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

## Equation

```markdown
::: equation {#eq:loss}
$$
L=-\sum_i y_i \log \hat y_i
$$
:::
```

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

## Citation

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

## Error Behavior

- YAML Front Matter 必须闭合且根节点必须是键值映射。
- Figure、Table、Equation、Algorithm、Listing、Bibliography semantic container
  必须由 `:::` 闭合。
- Parser 错误使用 `ParseError`，并尽可能提供源码行号。
- Parser 只读取输入，不写 DOCX、不修改 Markdown、不访问网络。

## 版式规则

`thesis.md` 不定义宋体、小四、页边距、行距等学校样式；这些全部进入学校 YAML 模板。
