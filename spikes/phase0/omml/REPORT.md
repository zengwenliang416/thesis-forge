# Phase 0 Spike：公式 LaTeX→OMML 链路覆盖率实证报告

- 日期：2026-08-15
- 关联决策：ADR-0003（公式转换路线）；本报告只提供事实，不给结论
- 目录：`spikes/phase0/omml/`
- 环境：macOS（arm64）；Python 3.14.4（`.venv`）；pandoc 3.8.2.1；latex2mathml 3.81.0（本 spike 新装入 `.venv`）

## 1. Spike 方法

三条候选链路对同一语料库（`corpus/formulas.yaml`，50 条）逐条实测，**所有数字由脚本机械产出**：

| 链路 | 脚本 | 结果文件 |
|---|---|---|
| A. 项目手写子集 `thesis_forge.core.math.LatexMathConverter` | `convert_thesisforge.py` | `results/thesisforge_conversion.json` |
| B. pandoc（内部 texmath，LaTeX→原生 OMML） | `convert_pandoc.py` | `results/pandoc_conversion.json` |
| C. latex2mathml + MML2OMML.XSL（LaTeX→MathML→OMML） | `convert_latex2mathml.py` | `results/latex2mathml_conversion.json` |

另有：

- `build_sample.py`：项目完整管线（`parse_markdown` → `validate_document` →
  `compile_document` → `DocxRenderer.render`）把子集可转换的 22 条 display 公式
  构建为 `output/sample.docx`，跑 `qa/tools/openxml_validate.py`，再用 lxml
  XPath 断言 OMML/SEQ/书签结构 → `results/omml_assertions.json`；
- `aggregate.py`：合并 A/B 结果与语料元数据 → `results/coverage.json`。

复跑（顺序执行，全部可重复）：

```bash
.venv/bin/python spikes/phase0/omml/convert_thesisforge.py
.venv/bin/python spikes/phase0/omml/convert_pandoc.py
.venv/bin/python spikes/phase0/omml/convert_latex2mathml.py
.venv/bin/python spikes/phase0/omml/build_sample.py
.venv/bin/python spikes/phase0/omml/aggregate.py
```

## 2. 语料库构成（50 条）

学科分布：计算机 11、数学 15、统计学 6、电子 4、机械 3、物理 4、管理学 4、
多学科通用 3（aligned/多行等归入来源学科）。每条含 id、latex、语法类别、
典型场景、预期难度（简单 31 / 中等 18 / 困难 1）、display/inline 用法。

| 类别 | 条数 | 代表 |
|---|---|---|
| 四则/分式/根式 | 4 | 求根公式、标准差（根式套分式套求和） |
| 上下标（含复合） | 3 | 深度学习权重 `w_{ij}^{(l)}`、高斯核 |
| 求和/积分/极限/乘积 | 7 | 牛顿-莱布尼茨、傅里叶变换、极大似然、e 的极限定义 |
| 希腊字母 | 3 | 含扩展字母 `\nu \tau \chi \psi \varepsilon \varphi` |
| 矩阵/行列式 | 2 | pmatrix、vmatrix+`\det` |
| 分段函数 / 多行对齐 | 1 + 2 | cases、aligned、裸 `\\` 换行 |
| 三角/对数/指数 | 4 | `\sin^2\theta`、`\log_2 n`、`\exp`、`\ln` |
| accent | 4 | `\hat \bar \vec \dot/\ddot` |
| 括号自适应 | 2 | `\left( \right)`、`\left\| \right\|` 范数 |
| `\text`/`\mathrm` | 3 | 中文注释、直立微分 d、MSE 缩写 |
| 运算符 | 7 | `\subset \in \Rightarrow \approx \propto \nabla \partial \sim \forall \exists` 等 |
| 综合 / 行内混排 | 6 + 2 | 交叉熵、矩阵乘法、贝叶斯、代价函数、组合数、行内 `$...$` |

## 3. 覆盖率实测

### 3.1 项目手写子集：24/50（48.0%）

- 成功 24；失败 26，其中 `UnsupportedMathError` 24 条、`MathSyntaxError` 2 条。
- 语法错误 2 条都不是用户写错，而是**文法限制**：函数名不能直接带上下标
  （`\sin^2 \theta` → `Unexpected '^'`；`\log_2 n` → `Unexpected '_'`），
  因为函数参数的解析只吃掉一个原子，上下标无法先挂到函数名上。

失败命令分布（按条数）：

| 失败命令 | 条数 | 典型场景 |
|---|---|---|
| `\begin`（pmatrix/vmatrix/cases/aligned 环境） | 3 | 矩阵、行列式、分段、多行对齐 |
| `\int` | 2 | 定积分、傅里叶变换 |
| `\left` | 2 | 自适应括号、范数 |
| `\mathrm` | 2 | 直立微分 d、MSE 缩写 |
| 单发 15 个：`\approx \binom \ddot \det \eta \forall \lim \nabla \nu \partial \prod \sim \subset \text \vec` | 各 1 | 见 coverage.json |

意外发现：`\eta` 不在 `GREEK_SYMBOLS` 里（其余 20 个小写希腊字母都在），
深度学习最常用的学习率记号恰好踩中（eq06）。

### 3.2 pandoc：49/50（98.0%）

唯一失败：eq22 裸 `\\` 无环境换行（pandoc 输出 "Could not convert TeX math"
警告并把公式退化为纯文本，退出码仍为 0，判失败靠 stderr + m:oMath 计数双重判据）。
pmatrix/vmatrix/cases→`m:m`，aligned→`m:eqArr`，`\left\right`→`m:d`，
`\int/\prod/\lim`→`m:nary`，全部为真 OMML（合并产物 `output/pandoc_corpus.docx`
含 49 个 `m:oMath`，其中 `m:m`×3、`m:d`×7、`m:eqArr`×1、`m:nary`×17）。

### 3.3 latex2mathml + MML2OMML.XSL：MathML 50/50 → OMML 49/50

- latex2mathml 3.81.0 把 50 条全部转成 presentation MathML（100%）。
- MathML→OMML 用 Microsoft 随 Office 分发的 MML2OMML.XSL（XSLT 1.0 正式版，
  本 spike 副本镜像自 PaddlePaddle/PaddleX 仓库，见 `assets/MML2OMML.XSL`），
  lxml 直接执行 XSLT，49 条得到以 `m:oMath` 为根的良构 OMML。
- 唯一失败 eq21（aligned）：latex2mathml 把对齐符 `&` 未转义地写进
  MathML（`<mi>&</mi>`），产物不是良构 XML。属上游 bug，可预处理
  （MathML 字符串先转义裸 `&`）绕过。
- 另实测排除一个坑：meTypeset 镜像的 "Beta Version 070708" 副本是
  **XSLT 2.0**，libxslt（lxml/xsltproc）只支持 1.1，转换退化成纯文本拷贝，
  不可用；必须用 Office 正式版（1.0）。

### 3.4 分类对照（thesisforge 成功数 / pandoc 成功数 / 总数）

| 类别 | thesisforge | pandoc |
|---|---|---|
| 四则/分式/根式 | 4/4 | 4/4 |
| 上下标 | 2/3 | 3/3 |
| 求和/积分/极限/乘积 | 3/7 | 7/7 |
| 希腊字母 | 2/3 | 3/3 |
| 矩阵/行列式 | 0/2 | 2/2 |
| 分段函数 | 0/1 | 1/1 |
| 多行对齐 | 1/2（保真存疑，见 §5） | 1/2 |
| 三角/对数/指数 | 2/4 | 4/4 |
| accent | 2/4 | 4/4 |
| 括号自适应 | 0/2 | 2/2 |
| `\text`/`\mathrm` | 0/3 | 3/3 |
| 运算符 | 1/7 | 7/7 |
| 综合 | 5/6 | 6/6 |
| 行内混排 | 2/2（仅转换层；管线不支持行内，见 §4） | 2/2 |

## 4. OMML 结构验证（项目链路 sample.docx）

`build_sample.py` 把子集可转换的 22 条 display 公式（`::: equation {#eq:*}` 容器，
模板 `templates/schools/example-university/2026.yaml`，equation 编号为 chapter 模式）
构建为 `output/sample.docx`，断言结果（`results/omml_assertions.json`）：

- `m:oMath` 总数 **22 = 预期 22**，逐条落在对应公式段落内；
- 编号公式 SEQ field **22 个**，`w:instrText` 形如 `SEQ TF_Equation_1 \r 3 \* ARABIC`
  （字段名规则 `TF_{Kind}_{chapter}`，见 `core/compiler.py:180`）；
- 编号公式书签 **22 个**，`w:bookmarkStart` 名形如 `tf_eq_eq01_arith_frac`
  （规则 `tf_` + id 非法字符转 `_`，见 `core/compiler.py:155`）；
- 逐条断言（oMath + SEQ + 书签同段落）**全部通过**（`per_equation_all_ok=true`）；
- `qa/tools/openxml_validate.py` 结构校验 **13/13 通过，退出码 0**；
- 行内混排场景：**管线不支持行内数学**——正文中 `$O(n \log n)$` 原样保留为
  字面文本（`inline_math_converted=false`，两条 inline 公式均以纯文本形式找到）。
  `MARKDOWN_SPEC.md` 的 equation 语法只有块级容器，INLINE_TOKEN_RE 不含 `$`。

## 5. 保真度问题：转换「成功」≠ 输出正确

1. **eq22 裸 `\\` 静默错渲染**：子集把 `\\` 当转义字面量接受，sample.docx 中
   该公式的 OMML 出现一个内容为 `\` 的 `m:r`（实测 `m:t` 序列
   `y = a + b \ z = c + d`）。pandoc 对同条直接报错退出。
   建议：`\\` 应作为语法错误或换行语义处理，不应静默通过。
2. **函数参数只吃一个原子**：`\log p(x_i)` 渲染为 `m:func(log, p)` + 括号文本
   游离在 func 外（实测 eq10 的 OMML：`fName=log`、`e=p`）。视觉上接近，
   语义结构错误；`\exp{...}` 加花括号可规避，但真实论文常不写花括号。
3. **`\eta` 缺失属个别遗漏**而非设计边界，补齐成本低。

## 6. 项目不支持但学位论文常用的命令清单（按建议优先级）

- **P0（缺了基本没法用）**：`\int \prod \lim`（含上下限）；`\left \right`
  自适应括号；`\begin{pmatrix|bmatrix|vmatrix|cases|aligned}` 环境；
  `\partial \nabla`；`\mathrm`；函数名上下标文法（`\sin^2`、`\log_2`、`\max_a`）。
- **P1（高频）**：`\text`（含中文注释）；`\vec \dot \ddot \tilde` 等 accent；
  `\sim \approx \propto \in \subset \Rightarrow \Leftrightarrow`；`\det \binom`；
  扩展希腊字母（`\nu \tau \chi \psi \varepsilon \varphi \eta \ldots`）。
- **P2（可延后）**：多行/对齐语义（`\\`、`&` 对齐点）；行内 `$...$` 语法；
  `\mathbb \mathbf \mathit` 字体类；`\sqrt[n]{}` 可选参数；`\overline \underline`。

## 7. 给 ADR-0003 的建议回答问题清单

1. **目标覆盖率是多少？** 手写子集现为 48%；论文常用公式要 ≥95% 需补齐
   §6 全部 P0/P1——实质上是重写一个 texmath 的子集，parser/model/renderer
   三层都要动，且每类需配 OOXML 结构测试（AGENTS.md §5）。
2. **是否接受公式链路引入外部进程？** pandoc 即用即 98%，但单二进制 253 MB
   （phase0 parser spike 已记录）且编号/书签/REF 仍需项目自行包装——pandoc
   只产出 `m:oMath` 片段，SEQ 字段与书签包装点已验证集中在
   `renderers/docx/equations.py:render_equation`。
3. **latex2mathml 路线的真实成本**：纯 Python、语料 100% 转 MathML；
   MathML→OMML 经 XSLT 实测 49/50（1 例上游 bug 可预处理绕过）。但
   MML2OMML.XSL 是 Microsoft 专有分发文件，**未附开源许可，再分发需法务确认**；
   自写等价转换的工作量参照物是该 XSL 约 150 KB / 数千模板规则。
4. **保真度验收标准**：本 spike 证明「转换成功」会掩盖静默错误（§5）。
   无论选哪条路线，是否需要 OMML 结构黄金测试（对照样本 XML 断言）？
5. **行内公式是否进 V1？** 当前语法与管线都不支持 `$...$` 行内数学，
   混排场景下公式以纯文本残留（§4 实测）。
6. **语义树 vs 最终 OMML**：项目链路的 MathNode 树支撑编号、校验、预览等
   下游能力；外部后端只给 OMML 片段。若引入外部后端，语义信息（哪些符号、
   是否分段/矩阵）是否还需要、从哪里拿？

## 8. 产物清单

```text
spikes/phase0/omml/
├── corpus/formulas.yaml            # 50 条语料（id/latex/类别/场景/难度/用法）
├── convert_thesisforge.py          # 链路 A：项目子集逐条转换
├── convert_pandoc.py               # 链路 B：pandoc 逐条 + 合并 docx
├── convert_latex2mathml.py         # 链路 C：latex2mathml + XSLT
├── build_sample.py                 # 项目全管线构建 sample.docx + 结构断言
├── aggregate.py                    # 合并 A/B → coverage.json
├── assets/MML2OMML.XSL             # Microsoft Office 版（XSLT 1.0），镜像自 PaddlePaddle/PaddleX
├── output/
│   ├── sample.docx                 # 项目管线产物（22 条编号公式）
│   ├── sample_thesis.md            # 构建用 Markdown 源
│   ├── pandoc_corpus.docx          # pandoc 合并产物（49 个 m:oMath）
│   └── pandoc_corpus.md
└── results/
    ├── thesisforge_conversion.json
    ├── pandoc_conversion.json
    ├── latex2mathml_conversion.json
    ├── coverage.json               # 语料 × 链路 对照矩阵
    ├── omml_assertions.json        # sample.docx 结构断言
    └── openxml_validate_report.json  # 13/13 通过
```

### assets/MML2OMML.XSL 来源说明

Microsoft 随 Office 分发的 MathML→OMML 转换样式表（XSLT 1.0 正式版），
本 spike 副本取自 [PaddlePaddle/PaddleX](https://github.com/PaddlePaddle/PaddleX)
仓库 `paddlex/inference/common/result/converter/MML2OMML.XSL`（2026-08-15 拉取，
151707 字节）。文件本身无许可声明；仅作 spike 实证用途，若项目要分发需另行
确认授权或自写等价转换。
