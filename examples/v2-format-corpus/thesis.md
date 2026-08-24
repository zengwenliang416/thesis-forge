# 摘要 {#chap:abstract-zh}

本文语料覆盖 ThesisForge V2 的结构化 Markdown、富文本行内语义、模板驱动编号、
Review 投影和可编辑 DOCX 输出。

关键词：格式语料；文档编译；OpenXML

# Abstract {#chap:abstract-en}

This corpus exercises the complete local-first V2 document compilation path.

Keywords: format corpus; document compilation; OpenXML

# 第1章 格式语义 {#chap:introduction}

## 行内内容 {#sec:inlines}

这里有**粗体**、*斜体*、***粗斜体***、`inline-code`、[普通链接](https://example.com/spec)、
[邮箱链接](mailto:author@example.com)、<author@example.com>、行内公式 $E = mc^2$、
带定位引用 [@smith2025, p. 12]、期刊 [@smith2025]、专著 [@doe2024]、
会议论文 [@chen2023]，以及交叉引用[章节](#chap:introduction)、[小节](#sec:inlines)、
[图](#fig:architecture)、[表](#tbl:results)、[式](#eq:loss)、[清单](#lst:training)、
[算法](#alg:compile)。
第一行包含普通换行
第二行使用显式硬换行\
第三行保留手动换行，并引用脚注[^scope]。

> 这是一个引用块，保留**强调**和`代码`等行内语义。

## 列表与资源 {#sec:blocks}

3. 从 3 开始的有序列表
4. 有序列表的后续项

- 无序一级
  - 无序二级
    - 无序三级
- 无序一级的第二项

![编译流水线](assets/architecture.png){#fig:architecture}

第二张图片用于验证独立的 manifest 毫米宽度覆盖：

![模型缩略图](assets/model.png){#fig:model}

## 表格与公式 {#sec:math}

| 指标 | 结果 | 说明 |
| :--- | :---: | ---: |
| **准确率** | 96.2% | `stable` |
| 召回率 | 94.1% | 可复现 |

: 格式能力实验结果 {#tbl:results}

结果见[表](#tbl:results)，损失函数见[式](#eq:loss)。

$$
L(\theta) = -\sum_{i=1}^{N} y_i \log \hat{y}_i
$$
{#eq:loss}

独立公式语料还覆盖基础等式、分式与求和、矩阵：

$$
E = mc^2
$$
{#eq:energy}

$$
\frac{a}{b} + \sum_{i=1}^{n} x_i
$$
{#eq:frac-sum}

$$
\begin{pmatrix} a & b \\ c & d \end{pmatrix}
$$
{#eq:matrix}

## 普通代码与语义对象 {#sec:code}

下面的普通代码块必须按字面量保留：

```python
{#literal} [@literal] @fig:literal
print("ordinary code")
```

```python {#lst:training title="训练代码清单"}
def train_epoch(model, batches):
    for batch in batches:
        model.update(batch)
```

```algorithm {#alg:compile title="编译算法"}
输入：项目目录 P 和模板 T
输出：可编辑 DOCX
1. 解析并校验项目
2. 编译 RenderPlan
3. 渲染并执行 OpenXML 检查
```

### 语义类型 {#sec:semantic-types}

这个三级标题用于验证 H3 和 TOC 层级保留。

## 脚注与引用 {#sec:references}

脚注定义会进入 Review 脚注区域，并在 DOCX 中生成原生脚注。

[^scope]: 脚注正文来自本地 Markdown，并通过稳定 label 绑定到引用位置。

# 参考文献 {#chap:bibliography}

# 致谢 {#chap:acknowledgements}

感谢参与语料设计、模板评审和 OpenXML 验证的同学。

# 攻读学位期间的成果 {#chap:achievements}

已完成本地优先编译器、Review 投影和 DOCX 结构验收。
