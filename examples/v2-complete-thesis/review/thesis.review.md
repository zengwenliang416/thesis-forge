> GENERATED FILE - read-only Review export.
> Source: `thesis.md`.

# Review

**学校**：示例大学
**学院**：计算机学院
**题目**：面向可验证文档编译的学术论文示例
**英文题目**：An Academic Thesis Example for Verifiable Document Compilation
**专业**：计算机科学与技术
**学位**：工学硕士
**作者**：张三
**学号**：20260001
**导师**：李教授
**导师职称**：教授
**完成日期**：2026-05

## 前置部分

# 摘要

本文构建一个面向学术论文的本地优先文档编译流程，将可读的 Markdown 源文件转换为经过模板约束、语义校验和 OpenXML 结构检查的可编辑 Word 文档。 系统不把 Markdown 直接写入 Word，而是先生成带有稳定身份和源代码位置的类型化 文档模型，再生成 RenderPlan，最后由 DOCX renderer 输出 Word。

研究结果表明，**内容与格式分离**能够降低重复排版成本，结构化验证能够在 生成文件之前发现未解析引用、重复 ID 和不安全资源。实现中使用 `thesisforge.yaml` 作为项目入口，使用 `$E = mc^2$` 表示行内公式，并通过 \[1\] 的研究结果说明可追踪编译的重要性。

关键词：学术论文；Markdown；DOCX；OpenXML；文档编译

# Abstract

This example demonstrates a manifest-backed academic thesis project. The source remains readable Markdown while metadata, resources, school template and output policy live in `thesisforge.yaml`. The compiler validates the semantic document, resolves references, creates a typed RenderPlan and emits a structurally checked DOCX package.

Keywords: academic writing; Markdown; DOCX; OpenXML; document compilation

**分页**

## 目录
- 摘要
- Abstract
- 第1章 绪论
  - 研究背景
  - 研究问题
- 第2章 系统设计
  - 项目包与单一事实源
  - 数学模型
  - 数据与实验表格
  - 训练代码清单
  - 编译算法
- 第3章 验证与失败恢复
  - 引用、脚注和源代码定位
  - 构建报告
- 第4章 讨论
  - 可复现性
  - 局限性
- 结论
- 附录 A 构建命令
- 参考文献

## 正文

# 第1章 绪论

## 研究背景

论文写作同时包含内容组织、资源管理、引用解析、公式排版和学校格式约束。 传统方式通常要求作者在 Word 中手工维护目录、题注和交叉引用，导致源内容与 最终排版之间出现难以追踪的差异。已有研究认为，结构化文档管线有助于保持 内容身份和发布结果之间的一致性 \[1\]。

本项目把项目目录作为唯一入口。构建流程依次经过解析、校验、编译、渲染、 最终化、OpenXML postflight 和预览阶段。完整流程见图2-1， 损失函数示例见(2-2)，实验结果见表2-1。

普通换行会被归一化为空格，而这一行使用显式硬换行。  
这两个源代码行在 Word 中只应产生一个真实手动换行。

系统提供一个[项目规范说明](https://example.com/thesisforge-spec)作为普通 外部链接；本节还使用行内代码 `thesisforge.yaml` 标识项目配置文件。

## 研究问题

本文关注以下三个问题：

1. 如何在不让 Markdown parser 依赖 Word 实现细节的情况下保留论文语义？
2. 如何让图、表、公式、引用和脚注拥有稳定 ID，并支持源代码定位？
3. 如何在构建失败时保留上一次成功结果，同时明确标记输出已经过期？

实现范围分为三个层次：

- 内容层
  - 标题、段落和列表
  - 图表、公式和代码
  - 引用、交叉引用和脚注
- 编译层
  - 文档索引和编号
  - Typed RenderPlan
  - 模板样式和章节策略
- 输出层
  - Review 投影
  - DOCX/OpenXML 包
  - BuildReport 和最终版式预览

# 第2章 系统设计

## 项目包与单一事实源

项目包的入口是 `thesisforge.yaml`，它定义 schema、项目身份、元数据、资源、 学校模板、对象级布局、Word 输出名称以及 Review 输出位置。`thesis.md` 只 负责可读正文和稳定的语义 ID。

图像资源使用项目相对路径。下面的图展示了从源文件到 Word 的主流程：

**图2-1**：论文编译流水线（图片资源不可用或未提供安全链接）

图中的处理阶段可以概括为：

1. Source：读取项目 manifest 和 Markdown。
2. Typed IR：生成 `ThesisDocument` 和 `DocumentIndex`。
3. Validation：校验引用、资源、模板能力和路径边界。
4. RenderPlan：计算编号并生成 typed instructions。
5. DOCX：写入字段、书签、OMML、脚注、样式、关系和媒体。

## 数学模型

设论文编译结果的质量由结构完整性、内容可读性和模板一致性共同决定，则可以 使用如下目标函数描述：

**(2-1)**
$$
Q = \alpha S + \beta R + \gamma T
$$

其中，\(S\) 表示结构完整性，\(R\) 表示 Review 可读性，\(T\) 表示模板一致性。 在实验中，损失函数可以写为：

**(2-2)**
$$
L(\theta) = -\sum_{i=1}^{N} y_i \log \hat{y}_i
$$

当编译器发现(2-1)或(2-2)的 ID 重复、引用目标不存在 或公式无法转换为 OMML 时，构建应返回结构化诊断，而不是生成伪公式。

## 数据与实验表格

下表比较三种论文编译策略在一个小型示例集上的表现：

**表2-1**：三种文档编译策略的实验结果
| 方法 | 结构错误数 | 资源错误数 | 平均构建时间 |
| --- | --- | --- | --- |
| 手工 Word | 7 | 4 | 18.2 min |
| 纯文本转换 | 5 | 6 | 4.8 min |
| ThesisForge V2 | 0 | 0 | 1.6 min |

结果显示，V2 把错误前移到 validate 阶段，并通过 BuildReport 保留每一阶段 的执行状态。

## 训练代码清单

下面的清单是论文中的可复现代码片段：

训练循环示例
```python
def train_epoch(model, batches, optimizer):
    for batch in batches:
        loss = model.loss(batch)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
```

代码中的 `{#literal}`、`[@literal]` 和 `@fig:literal` 都必须保持为字面量， 不能被当作论文 ID 或引用。

## 编译算法

论文编译算法
```text
输入：项目目录 P，Markdown 源文件 M，学校模板 T
输出：Review R，DOCX D，BuildReport B
1. 读取 thesisforge.yaml 并解析 M
2. 构建 ThesisDocument 和 DocumentIndex
3. 校验资源、引用、ID、模板能力和路径边界
4. 生成编号、书签、字段和 typed RenderPlan
5. 渲染 Review、DOCX 和结构化 BuildReport
6. 执行 DOCX postflight，成功后发布输出
```

# 第3章 验证与失败恢复

## 引用、脚注和源代码定位

每个引用都必须能够在 `references.bib` 中找到对应条目。本文引用 \[1, p. 12\] 说明了带 locator 的引用形式。交叉引用使用可读标签， 例如研究背景，而不是直接暴露内部 NodeId。

这里有一个说明性脚注脚注1。脚注正文会出现在 Review 的脚注区域， DOCX 中则使用 `word/footnotes.xml` 和原生脚注引用。

**脚注 1**
失败构建不会覆盖上一次成功 DOCX；BuildReport 会记录失败阶段、

## 构建报告

每次手动构建或实时预览都应产生一个 BuildReport。报告至少包含：

- `intent`：发布构建或实时预览
- `outcome`：成功、失败或取消
- parse、validate、compile、render、finalize、postflight、preview 阶段状态
- 所有结构化 diagnostics 和 primary diagnostic
- 有界、脱敏的构建日志
- 当前输出和上一次成功输出的关系

如果用户修改了源码导致构建失败，界面保留上一次成功预览，并明确显示 “预览已过期”，不能把旧结果伪装成当前结果。

# 第4章 讨论

## 可复现性

完整项目包可以被复制到另一台机器，在不依赖 AI 服务和网络的情况下重新执行 inspect、validate、review 和 build。模板、图片、BibTeX 和源代码均通过项目 相对路径解析，构建报告则保存本次运行的结构化证据。

## 局限性

当前 V2 有明确的边界：

- 不提供 DOCX 到 Markdown 的反向转换。
- 不执行任意 TeX 宏或外部脚本。
- 不保留旧 Front Matter、`:::` 容器或 `@fig:id` 兼容路径。
- Word/WPS 的最终分页差异仍需在目标 Office 环境中人工验收。

# 结论

本文示例说明，Markdown 转 Word 的完整交付物应当是一个可验证的项目，而不只是 一个孤立的二进制文件。通过 manifest、Typed IR、RenderPlan、Review、DOCX postflight 和 BuildReport，论文内容、格式策略和最终输出之间建立了可追踪关系。

# 附录 A 构建命令

# 参考文献

1. \[1\] SMITH J, ZHANG W. Typed Document Pipelines for Academic Publishing\[J\]. Journal of Document Engineering, 2025, 12(3): 101-120.
