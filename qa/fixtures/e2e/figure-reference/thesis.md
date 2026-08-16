---
document:
  type: bachelor_thesis
  language: zh-CN
  spec_version: "1.0"
university:
  name: "XX大学"
thesis:
  title: "图表公式编号与交叉引用质量夹具"
  major: "计算机科学与技术"
author:
  name: "质量夹具"
  student_id: "2026000001"
advisor:
  name: "示例导师"
  title: "教授"
dates:
  completed: "2026-06"
render:
  template_id: "example-university-2026"
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
sections:
  abstract_zh: true
  toc: true
  references: true
  acknowledgements: true
---

# 摘要 {#chap:abstract-zh}

本夹具面向质量策略 D4 域，验证图、表、公式在编译产物中的 SEQ 编号字段、书签与 REF 交叉引用字段是否为真实 Word 对象，并覆盖目录字段、页码字段与参考文献渲染。确定性编译方法已有充分研究 [@fixture-compile-2025]，字段级验证思路参见 [@fixture-fields-2024]。[^fixture-note]

关键词：交叉引用；SEQ 字段；书签；质量夹具

# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

手工排版在章节调整后容易产生图表编号与正文引用不一致的问题。模板驱动编译把编号计算集中在编译阶段，正文中的引用写作 @fig:pipeline 这样的稳定 ID，最终编号由编译器统一解析。

## 研究内容 {#sec:scope}

本文围绕以下内容展开：

1. 定义带稳定 ID 的图、表、公式语义容器；
2. 编译阶段生成 SEQ 编号字段与书签；
3. 正文交叉引用生成指向书签的 REF 字段。

系统总体管线如 @fig:pipeline 所示。

::: figure {#fig:pipeline}
src: "./images/pipeline.png"
caption: "确定性编译管线示意"
width: "80%"
:::

# 实验与分析 {#chap:experiments}

## 实验设置 {#sec:setup}

实验统计结构校验与字段断言的通过情况，结果面板见 @fig:dashboard，核心指标汇总见 @tbl:metrics。

::: figure {#fig:dashboard}
src: "./images/dashboard.png"
caption: "质量指标结果面板"
width: "75%"
:::

::: table {#tbl:metrics}
caption: "结构校验核心指标"

| 指标 | 通过数 |
| --- | ---: |
| 书签配对 | 13 |
| 字段配对 | 13 |

:::

## 综合评分 {#sec:score}

综合评分定义见 @eq:score，其中权重由模板实验标定。

::: equation {#eq:score}
$$
S = \alpha P + \beta R
$$
:::

图 @fig:pipeline、图 @fig:dashboard、表 @tbl:metrics 与式 @eq:score 均可在 Word 客户端中继续编辑，其编号随章节增删自动刷新。

# 参考文献 {#chap:references}

::: bibliography
:::

# 致谢 {#chap:acknowledgements}

感谢评审同学在夹具设计与断言核对过程中提供的帮助。

[^fixture-note]: 本脚注用于同时覆盖脚注定义与引用的结构校验路径。
