---
document:
  type: bachelor_thesis
  language: zh-CN
  spec_version: "1.0"

university:
  name: "XX大学"
  name_en: "XX University"
  college: "XX学院"

thesis:
  title: "本科毕业论文题目"
  title_en: "English Title of the Bachelor Thesis"
  major: "专业名称"
  degree: "学士学位"
  research_direction: ""

author:
  name: "姓名"
  student_id: "学号"
  class: "班级"

advisor:
  name: "指导教师姓名"
  title: "职称"

dates:
  submitted: "2026-05-20"
  defended: "2026-06-01"
  completed: "2026-06"

render:
  template_id: "school-template-id"
  citation_style: "GB-T-7714-2025"
  bibliography: "./references.bib"
  figure_numbering: "chapter"
  table_numbering: "chapter"
  equation_numbering: "chapter"

sections:
  originality_statement: true
  authorization_statement: true
  abstract_zh: true
  abstract_en: true
  toc: true
  list_of_figures: false
  list_of_tables: false
  abbreviations: false
  symbols: false
  references: true
  acknowledgements: true
  appendices: true
  achievements: false
---

::: cover
:::

::: originality-statement

# 本科毕业论文原创性声明

本人郑重声明：所呈交的本科毕业论文是本人在指导教师指导下独立完成的研究成果。除文中已经注明引用的内容外，本论文不包含其他个人或集体已经发表或撰写过的研究成果。

学生签名：

日期：

:::

::: authorization-statement

# 本科毕业论文使用授权声明

本人同意学校按照有关规定保存、使用本毕业论文，并允许采用影印、缩印、数字化等方式进行保存、检索和阅览。

学生签名：

指导教师签名：

日期：

:::

::: abstract {lang="zh"}

# 摘要

在此填写中文摘要。建议包括研究背景与目的、研究方法、主要结果、结论与意义。

**关键词：** 关键词1；关键词2；关键词3；关键词4

:::

::: abstract {lang="en"}

# Abstract

Write the English abstract here. It should correspond to the Chinese abstract in content.

**Keywords:** Keyword 1; Keyword 2; Keyword 3; Keyword 4

:::

::: toc
depth: 3
title: "目录"
:::

::: list-of-figures
title: "插图目录"
:::

::: list-of-tables
title: "表格目录"
:::

# 缩略语表

| 缩略语 | 英文全称 | 中文名称 |
| --- | --- | --- |
| AI | Artificial Intelligence | 人工智能 |
| XXX | Full Name | 中文名称 |

# 符号说明

| 符号 | 含义 | 单位 |
| --- | --- | --- |
| $N$ | 样本数量 | — |
| $x$ | 示例变量 | — |

# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

在此填写研究背景。

## 研究目的与意义 {#sec:significance}

在此填写研究目的、理论意义和实际应用价值。

## 国内外研究现状 {#sec:related-work}

### 国外研究现状

在此填写国外研究进展，并使用文献引用，例如 [@ref-example-1]。

### 国内研究现状

在此填写国内研究进展，例如 [@ref-example-2]。

### 现有研究不足

总结已有工作的不足，并引出本文研究问题。

## 主要研究内容 {#sec:research-content}

本文主要开展以下研究：

1. 研究内容一；
2. 研究内容二；
3. 研究内容三；
4. 研究内容四。

## 技术路线 {#sec:technical-route}

本文技术路线如[图](#fig:technical-route)所示。

::: figure {#fig:technical-route}
src: "./images/technical-route.png"
caption: "本文研究技术路线"
width: "85%"
:::

## 论文组织结构 {#sec:organization}

本文共分为若干章，各章主要内容如下：

第一章，绪论。介绍……

第二章，相关理论与技术。介绍……

第三章，……

# 相关理论与关键技术 {#chap:theory}

## 理论基础一 {#sec:theory-1}

在此填写理论内容。

## 理论基础二 {#sec:theory-2}

在此填写理论内容。

### 公式示例

正文中可引用公式，如[式](#eq:example-equation)所示。

::: equation {#eq:example-equation}
$$
y = f(x)
$$
:::

其中，$x$ 表示……，$y$ 表示……。

## 本章小结

总结本章主要内容，并说明与下一章的关系。

# 研究方法或模型设计 {#chap:method}

## 总体方案 {#sec:method-overview}

介绍整体研究方案或模型架构。

::: figure {#fig:architecture}
src: "./images/architecture.png"
caption: "总体架构"
width: "90%"
:::

如[图](#fig:architecture)所示，整体方案包括……

## 数据或研究对象 {#sec:data}

介绍数据来源、研究对象、样本、数据采集方式等。

## 方法设计 {#sec:method-design}

详细介绍本文提出的方法。

### 模块一

描述模块一。

### 模块二

描述模块二。

## 算法流程 {#sec:algorithm}

::: algorithm {#alg:main}
caption: "核心算法流程"

**输入：** 输入数据

**输出：** 输出结果

1. 初始化；
2. 执行步骤一；
3. 执行步骤二；
4. 计算结果；
5. 返回结果。

:::

## 本章小结

总结本章工作。

# 实验设计或系统实现 {#chap:experiment}

## 实验环境 {#sec:environment}

::: table {#tbl:environment}
caption: "实验环境配置"

| 项目 | 配置 |
| --- | --- |
| 操作系统 | Ubuntu / Windows / macOS |
| Python | 3.x |
| 深度学习框架 | PyTorch / TensorFlow |
| CPU | XXX |
| GPU | XXX |

:::

实验环境如[表](#tbl:environment)所示。

## 数据集与数据处理 {#sec:dataset}

介绍数据集、数据划分、清洗、预处理与增强方法。

::: table {#tbl:dataset}
caption: "数据集统计"

| 数据集 | 样本数量 | 训练集 | 验证集 | 测试集 |
| --- | ---: | ---: | ---: | ---: |
| Dataset A | 10000 | 7000 | 1000 | 2000 |
| Dataset B | 20000 | 14000 | 2000 | 4000 |

:::

数据集统计信息见[表](#tbl:dataset)。

## 实验参数 {#sec:parameters}

::: table {#tbl:parameters}
caption: "实验参数设置"

| 参数 | 数值 |
| --- | ---: |
| Learning Rate | 0.001 |
| Batch Size | 64 |
| Epoch | 200 |

:::

## 评价指标 {#sec:metrics}

介绍实验使用的评价指标。

::: equation {#eq:metric-example}
$$
Metric = \frac{A}{B}
$$
:::

## 系统实现 {#sec:system}

如果论文属于软件、信息系统或工程实现类，可在此介绍：

1. 系统需求；
2. 总体架构；
3. 模块设计；
4. 数据库设计；
5. 核心功能实现；
6. 系统界面；
7. 系统测试。

如果论文不涉及系统实现，可删除本节。

### 代码示例

::: listing {#lst:example}
caption: "核心代码示例"
language: "python"

```python
def example(x):
    return x
```

:::

## 本章小结

总结实验设计或系统实现工作。

# 实验结果与分析 {#chap:results}

## 总体实验结果 {#sec:main-results}

::: table {#tbl:main-results}
caption: "不同方法实验结果对比"

| 方法 | 指标1 | 指标2 | 指标3 |
| --- | ---: | ---: | ---: |
| Baseline A | 0.800 | 0.810 | 0.820 |
| Baseline B | 0.830 | 0.840 | 0.850 |
| Proposed | **0.880** | **0.890** | **0.900** |

:::

根据[表](#tbl:main-results)可以看出……

## 结果可视化 {#sec:visualization}

::: figure {#fig:results}
src: "./images/results.png"
caption: "实验结果可视化"
width: "80%"
:::

实验结果如[图](#fig:results)所示。

## 对比实验 {#sec:comparison}

分析本文方法与现有方法的差异及性能变化。

## 消融实验 {#sec:ablation}

::: table {#tbl:ablation}
caption: "消融实验结果"

| 实验设置 | 指标1 | 指标2 |
| --- | ---: | ---: |
| 完整模型 | 0.900 | 0.910 |
| 去除模块A | 0.870 | 0.880 |
| 去除模块B | 0.860 | 0.870 |

:::

## 参数敏感性分析 {#sec:sensitivity}

分析关键参数变化对结果的影响。

## 误差分析 {#sec:error-analysis}

分析失败案例、异常样本以及模型可能存在的问题。

## 统计显著性分析 {#sec:statistics}

如有需要，可在此给出置信区间、显著性检验或其他统计结果。

## 本章小结

总结实验结果与主要发现。

# 讨论 {#chap:discussion}

## 主要发现

归纳研究中最重要的发现。

## 与已有研究的比较

结合参考文献讨论本文结果与已有研究的一致性和差异。

## 方法优势

说明本文方法的主要优势。

## 研究局限

说明数据、方法、实验、应用范围等方面的局限。

## 实际应用价值

说明成果的潜在应用场景。

# 结论与展望 {#chap:conclusion}

## 研究结论

总结全文，不再展开新的论证。

## 主要工作

本文主要完成了以下工作：

1. ……
2. ……
3. ……

## 创新点

本文的主要创新点如下：

1. ……
2. ……
3. ……

## 不足之处

本文仍存在以下不足：

1. ……
2. ……

## 未来展望

未来可从以下方向继续研究：

1. ……
2. ……
3. ……

# 参考文献 {#references}

::: bibliography
source: "./references.bib"
style: "GB-T-7714-2025"
:::

# 致谢 {#acknowledgements}

在此填写致谢内容。

# 附录 {#appendices}

## 附录A 补充实验数据 {#appendix-a}

在此填写正文中不适合展开的补充实验数据。

::: table {#tbl:appendix-data}
caption: "补充实验数据"

| 项目 | 数值 |
| --- | ---: |
| A | 1 |
| B | 2 |

:::

## 附录B 补充图表 {#appendix-b}

::: figure {#fig:appendix}
src: "./images/appendix.png"
caption: "补充结果"
width: "80%"
:::

## 附录C 核心代码 {#appendix-c}

::: listing {#lst:model-code}
caption: "模型核心代码"
language: "python"

```python
class Model:
    def __init__(self):
        pass

    def forward(self, x):
        return x
```

:::

## 附录D 调查问卷 {#appendix-d}

> 本节适用于管理学、社会科学、教育学等需要问卷调查的论文；不需要时可删除。

### 基本信息

1. 您的年龄：
2. 您的职业：
3. ……

### 调查问题

1. ……
2. ……
3. ……

# 攻读学位期间取得的成果 {#achievements}

## 发表论文

1. 作者. 论文名称[J]. 期刊名称, 年份.

## 专利

1. 发明人. 专利名称[P]. 专利号, 年份.

## 软件著作权

1. 软件名称，登记号，年份.

## 竞赛与获奖

1. XX竞赛X等奖，年份.


<!-- =========================
     常用语法示例
     =========================

文献引用：
[@ref-example-1]
[@ref-example-1; @ref-example-2]

图引用：
[图](#fig:architecture)

表引用：
[表](#tbl:main-results)

公式引用：
[式](#eq:example-equation)

算法引用：
[算法](#alg:main)

代码引用：
[代码](#lst:example)

脚注：
正文中的说明文字[^note-1]

[^note-1]: 这是脚注内容。

-->
