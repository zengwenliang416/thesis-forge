# 摘要 {#chap:abstract-zh}

本文设计并实现一种本地优先、确定性、模板驱动的本科论文编译器。系统将 Markdown 解析为与 Word 实现无关的论文领域模型，经结构化验证与统一编译后生成可编辑 DOCX。验收结果表明，该方案能够离线完成图表、公式、交叉引用、脚注和参考文献等学术对象的编译。

关键词：Markdown；论文编译；OOXML；确定性构建

# Abstract {#chap:abstract-en}

This thesis presents a local-first, deterministic and template-driven bachelor thesis compiler. Structured Markdown is parsed into a renderer-neutral domain model, validated, compiled and rendered as an editable DOCX document with academic objects and real Word fields.

Keywords: Markdown; thesis compiler; OOXML; deterministic build

# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

传统 Word 排版要求作者反复调整标题、图表编号、公式和参考文献。结构化学术文档方法能够降低内容与版式的耦合 [@ref-example-1]，而确定性编译进一步提高了重复构建的可验证性 [@ref-example-2]。[^determinism]

## 研究内容 {#sec:scope}

本文围绕以下内容展开：

1. 定义可验证的结构化 Markdown 输入；
2. 建立与 Word 无关的论文领域模型；
3. 通过模板解析学校版式；
4. 生成包含真实 OOXML 对象的 DOCX。

## 技术路线 {#sec:technical-route}

系统总体架构如[图](#fig:architecture)所示。

![DocForge 确定性编译架构](images/acceptance-architecture.png){#fig:architecture}

# 系统设计 {#chap:design}

## 编译流水线 {#sec:pipeline}

系统采用 Markdown -> ForgeDocument -> Validation -> Template -> RenderPlan -> DOCX 的单向编译链路，其抽象关系见[式](#eq:pipeline)。

$$
D_{docx} = R(C(V(P(D_{md}))))
$$
{#eq:pipeline}

## 能力模型 {#sec:capabilities}

V1 核心能力见[表](#tbl:capabilities)。

| 能力 | 输入 | DOCX 输出 |
| --- | --- | --- |
| 图 | 本地图片 | Drawing 与题注 |
| 表 | Markdown 表格 | 三线表 |
| 公式 | LaTeX 子集 | OMML |
| 引用 | BibTeX key | 顺序编码引用 |

: DocForge V1 核心能力 {#tbl:capabilities}

## 安全构建算法 {#sec:safe-build}

安全构建流程见[算法](#alg:build)。

```algorithm {#alg:build title="安全构建流程"}
1. 解析并验证本地输入；
2. 编译 renderer-neutral RenderPlan；
3. 渲染到目标目录临时文件；
4. 校验 DOCX ZIP 与核心 XML；
5. 原子替换最终输出。

```

## 应用服务接口 {#sec:application-service}

核心服务接口示意见[代码](#lst:service)。

```python {#lst:service title="安全构建服务调用"}
result = build_service(
    source="document.md",
    output="build/document.docx",
)
```

# 实验结果与分析 {#chap:results}

## 离线验收 {#sec:offline-acceptance}

在禁用网络连接并移除 AI 服务凭据后，inspect、validate 与 build 均只读取本地 Markdown、YAML、BibTeX 和图片资源。重复构建生成的 ZIP 元数据可以不同，但编号、书签、字段和章节结构保持语义等价。

## Word 对象验收 {#sec:word-acceptance}

验收包包含真实目录字段、图表与公式编号字段、交叉引用字段、页码字段、OMML、脚注、页眉页脚及多个节。[图](#fig:architecture)、[表](#tbl:capabilities)和[式](#eq:pipeline)均可在 Word 客户端中继续编辑。

# 结论与展望 {#chap:conclusion}

本文完成了 DocForge V1 核心编译链和端到端验收。系统在不依赖网络或 AI 服务的条件下生成可编辑 DOCX，并以结构化测试验证关键 OOXML 对象。

# 参考文献 {#chap:references}

# 致谢 {#chap:acknowledgements}

感谢指导教师和同学在系统设计、文档验证与兼容性测试过程中提供的帮助。

# 附录 A 验收命令 {#chap:appendix-a}

本附录记录完整样例使用的离线命令：

1. docforge inspect .
2. docforge validate .
3. docforge build . -o build/document.docx

[^determinism]: 确定性构建指相同输入、模板和依赖版本产生语义等价的编号、引用、字段和章节结构。
