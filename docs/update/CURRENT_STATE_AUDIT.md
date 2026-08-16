# ThesisForge 现状审计（Current State Audit）

> 状态：Baseline
> 审计日期：2026-08-14
> 审计方法：通读 `src/thesis_forge/` 全部 71 个 Python 文件、`docs/` 规范、`tests/`、`examples/`、`templates/`，并实际运行测试与 lint。
> 用途：作为 `docs/update/` V1 优化计划 Phase 0 的事实输入。只记录已核实的现状，不做选型结论（结论在 `adr/`）。

## 1. 总体判断

代码库已超出 `docs/V1_PLAN.md`（M0–M10）所反映的进度：M1–M8 的核心链路（Parser → ThesisDocument → Validation → Compiler/RenderPlan → DOCX）已打通，且 DOCX 渲染器已实现真 OMML、真 SEQ/REF/PAGE 字段、真 Section/页眉页脚/脚注；M9 的应用服务层、HTTP/sidecar 适配器、React 前端与 Tauri 桌面壳也已存在。

与 V1 优化计划对照，五个高风险闭环的现状是：

| 高风险链路 | 现状 | 主要缺口 |
|---|---|---|
| Parser | 手写正则 + 逐行扫描（396 行），内联位置精确到列 | 块级无列号；未知语法静默降级；无多文件 include；规范外语法（粗斜体/链接/图片/顶层代码围栏）全不支持 |
| Template | 单 YAML v0.3 模型（686 行，`extra="forbid"`），2 个学校模板 | 无 `reference.docx`/`shell.docx`；无模板包/继承/provenance；复杂封面靠 11 个固定 cover field |
| OMML | 真 OMML 输出，LaTeX 子集手写转换（277 行） | 子集覆盖未知（无 corpus 量化）；编号仅 `\t` 分隔无右对齐制表位 |
| Word 字段 | 真 TOC/SEQ/REF/PAGE + cached result + `updateFields` | TOC 无 cached 条目；SEQ 用 `\r` 钉值（Word 端无法重排，确定性取舍未声明）；无 Word 端 no-repair 验证门禁 |
| Citation | 手写 GB/T 7714 formatter，5 种 BibTeX 类型 | 无 citeproc/CSL；`citation_style` 配置被解析但不被使用；无 "等/et al" 截断；无 [EB/OL] 等类型 |

## 2. 子系统事实

### 2.1 Parser（`core/parser.py`，396 行）

- 实现：纯手写，正则 + 逐行单遍扫描；无第三方 Markdown 库，无状态机抽象。
- 支持语法：YAML front matter（强校验）；ATX 标题 1–6 + `{#id}`；`:::` 容器六种（figure/table/equation/listing/algorithm/bibliography）；有序/无序列表（`indent//2` 计层级）；脚注定义（含续行）与 `[^label]` 引用；citation `[@key; @key2, locator]`；crossref `@fig|tbl|eq|alg|lst|sec|chap:name`。
- Source position：`SourceLocation(line, column)`；**内联对象行列精确**（测试断言到列），**块级对象只有行号、column 恒为 None**（parser.py:195,257,326）。
- 无多文件 include（规范与实现双缺）。
- 未知语法策略：**静默降级为段落原文**，无诊断（parser.py:379-384）——粗体/斜体/链接/图片/顶层 ``` 代码围栏均落入口袋段落。

### 2.2 Domain Model（`core/model.py`，160 行）

- 纯 dataclass，无 Word/OOXML 细节（符合 AGENTS.md §1.2）。
- ID 前缀体系 `chap/sec/fig/tbl/eq/alg/lst`（`core/ids.py`），`ThesisDocument.index_by_id()` 聚合交叉引用/citation/脚注引用。

### 2.3 Compiler / RenderPlan / Validator

- `core/compiler.py`（893 行）：全部编号在此计算（章绑定/连续计数）；书签 `tf_` 前缀 + 40 字符截断，冲突抛 `BookmarkCollisionError`；citation 按首次出现编号；含封面提取、`_SectionPlanner`、`_SemanticContext`、Markdown 表格结构化。
- `core/render_plan.py`（475 行）：13 种 frozen instruction；**注意 `SequenceInstruction.field_code`（render_plan.py:166）直接含 Word `SEQ ... \* ARABIC` 字段码，属 renderer-neutral 层的轻度实现泄漏**。
- `core/validator.py`（481 行）：8 条默认规则——required-metadata、empty-document、invalid-id-prefix、duplicate-id、missing-reference、heading-level-jump、missing-image/resource-path-escape、bibliography 与 template 系列；结果确定性排序。
- `core/math.py`（277 行）：手写 LaTeX 子集递归下降解析 → 语义数学树（`\frac \sqrt \sum \hat \bar`、8 函数、希腊字母、上下标）；未知命令抛 `UnsupportedMathError`。

### 2.4 DOCX 渲染器（`renderers/docx/`，18 模块）

OOXML 能力矩阵（已核实）：

| 能力 | 实现 | 细节 |
|---|---|---|
| TOC | 真 field | `TOC \o "1-3" \h \z \u`（renderer.py:230-233）；**无 cached 条目**，靠 dirty + `updateFields`；外包 `tf_toc_index` 书签供 finalizer 定位 |
| SEQ | 真 field + cached result | 字段码 `SEQ TF_Figure_1 \r N \* ARABIC`（render_plan.py:167）——**`\r` 把编号钉死，Word 无法自动重排**（确定性优先的设计取舍，规范未声明） |
| REF | 真 field + cached result | `REF bookmark \h`（fields.py:80-84） |
| Bookmark | 真 bookmarkStart/End | `tf_<id>` 截断 40 字符 |
| PAGE/NUMPAGES | 真 field | cached result 恒为 "1"（sections.py:100-119） |
| OMML | 真 `m:oMath` | `m:f/rad/sSubSup/nary/func/acc`；公式编号为 tab + 真 SEQ + 书签；**编号仅 `\t` 分隔，无右对齐制表位**（equations.py:148） |
| Footnote | 真 footnotes.xml part | separator/continuationSeparator 齐全；嵌套脚注显式拒绝（footnotes.py:111-116） |
| Section | 真 `w:sectPr` | `w:pgNumType` fmt decimal/lowerRoman/upperRoman + `w:start` 重启；页眉页脚 default/first/even + `w:titlePg` + evenAndOddHeaders |
| 三线表 | 真边框控制 | 全 nil 后写 top/bottom + 表头行 `w:tcBorders` 底线，线宽模板驱动（0.25–12pt 校验） |
| 列表编号 | 真 numbering.xml | 9 级、起始值、有序/无序 marker |
| 页面几何 | 完整 | A3–Legal、方向、边距、页眉页脚距离、`w:docGrid` |
| update-on-open | 有 | `<w:updateFields w:val="true"/>`（fields.py:91） |
| 超链接 | **缺失** | 全 src 无 `w:hyperlink`；citation 是纯文本 run |
| 文档样式来源 | python-docx 默认模板 | **无 reference.docx**（document.py:76） |
| 包校验 | 有 | `validate_docx_package`：ZIP 完整性、必需 part、Content_Types/rels/根元素（package.py） |

### 2.5 模板（`templates/model.py` 686 行 + 3 份 YAML）

- 顶层字段：id/name/year/page/cover(11 个固定 field)/list/body/heading(1-3)/semantic_styles/toc/bibliography/figure/table/equation/sections/citation；全部 `extra="forbid"`。
- 规范已对齐到 v0.3（`docs/TEMPLATE_SPEC.md`）。
- YAML：`templates/base/bachelor.yaml`（最小集）、`templates/schools/example-university/2026.yaml`、`templates/schools/hunan-university-of-technology/master-2026.yaml`（完整）。
- `resolver.py`：显式路径 > template_id；搜索序项目祖先 `templates/` → 包内 `template_data/` → 仓库 `templates/`。
- 无 reference.docx、无模板包结构、无继承、无 provenance（即 Template Package v2 全部待建）。

### 2.6 文献引用（`bibliography/`，手写管线，无 citeproc）

- `bibtex.py`：自写 BibTeX 解析，仅 5 类（article/book/inproceedings/mastersthesis/phdthesis），必填校验 + 行号定位。
- `formatter.py`：手写 GB/T 7714 顺序编码制，[J]/[M]/[C]//[D]，著者全大写 + 首字母缩写。
- **缺陷**：`citation.style`/`render.citation_style` 解析后不被用于选择 formatter（compiler.py:858-861 无条件用 GB/T formatter）；无 "等/et al" 截断（formatter.py:20 全列）；无 [EB/OL] 等类型；无著者-出版年制。

### 2.7 CLI / 应用服务 / 适配器

- `cli.py`（135 行）：仅 `inspect`（JSON）/`validate`（Rich 表格）/`build` 三个子命令；退出码 0/1/2（test_cli.py 全覆盖）。**无 doctor**。
- `application/services.py`：五阶段 BuildStage（parse→validate→compile→render→finalize），依赖注入。
- `application/office_refresh.py`（748 行）：LibreOffice UNO 无头刷新 TOC/字段，进程树清理，失败回滚原字节。**缺陷：office_refresh.py:592 与 pdf_preview.py:567 在 darwin 硬编码 `/tmp` 且无回退**。
- `application/pdf_preview.py`（747 行）：LibreOffice / macOS AppleScript Word / Windows COM 三路导出；失败被静默吞掉（services.py:282）。
- `adapters/`：HTTP 与 sidecar（JSON-lines，供 Tauri）适配层；`ui/`、`frontend/`（React+Vite）、`src-tauri/` 桌面壳已存在（UI 层不在 Phase 0 审计范围）。

## 3. 规范 vs 实现对照（MARKDOWN_SPEC）

| 语法 | SPEC | Parser |
|---|---|---|
| front matter / heading+ID / 段落 inline / 列表 / 五种容器 / bibliography marker / citation / crossref / footnote（含续行）/ 保留 ID / 资源边界 | ✓ | ✓ 全部落地 |
| 「Markdown 基础结构」隐含的粗斜体/链接/图片/顶层代码围栏 | 暗示 | ✗ 全部不支持且静默降级 |
| 标题/表格/算法正文/caption 内 inline 提取；equation 可省略 `$$`；listing fence info string 推断语言 | 未写 | ✓（spec 需补） |
| 多文件 include | 未写 | ✗ |

另：`examples/complete-thesis/thesis.md:30-36` 的 front matter `sections:` 段在 Python 核心**无任何消费者**（编译器只读 `render.*` 与封面字段），属死配置或仅供前端。

## 4. 测试基线（2026-08-14 实测）

- `pytest tests/ -q`：**482 passed, 4 failed**（约 28s）。
  - 4 个失败全部为 LibreOffice runner 测试（test_pdf_preview.py ×3、test_application_services.py ×1），根因：本机 `/private/tmp` 被删除、`/tmp` 为悬空符号链接，而 office_refresh.py:592/pdf_preview.py:567 硬编码 `/tmp`。属**环境问题 + 代码无回退**双重缺陷，非功能回归。修复环境：`sudo mkdir -p /private/tmp && sudo chmod 1777 /private/tmp`。
- `ruff check .`：3 个 I001（import 排序），全部位于 `tmp/` 临时脚本；`src/` 与 `tests/` 全部通过。
- 测试深度评估：
  - `test_docx_renderer.py`（3102 行）与 `test_acceptance.py`（951 行）：**大量 XML/XPath 结构断言**（458 处），覆盖三线表边框、SEQ/TOC/PAGE field、OMML、脚注、节页码格式、styles round-trip。
  - parser/validator/compiler 测试断言到类型序列、行列号、规则码，非存在性测试。
  - 缺口：无 heading location 断言；无未知语法降级行为测试；bibliography 无 XML 级测试；无跨软件 no-repair 打开门禁。

## 5. 债务清单（供 RISK_REGISTER / ADR 引用）

| 编号 | 债务 | 位置 | 关联风险 |
|---|---|---|---|
| D-01 | 未知语法静默降级无诊断 | parser.py:379-384 | R-001 |
| D-02 | 块级 SourceLocation.column 恒 None | parser.py:195,257,326 | R-003 |
| D-03 | RenderPlan 泄漏 Word SEQ 字段码 | render_plan.py:166 | R-001/R-012 |
| D-04 | 示例 `sections` front matter 无消费者 | examples/complete-thesis/thesis.md:30-36 | R-030 |
| D-05 | 混合有序/无序标记硬截断列表块 | parser.py:346-347 | R-001 |
| D-06 | 无多文件 include | parser.py | R-018 |
| D-07 | citation style 配置被忽略 | compiler.py:858-861 | R-010/R-011 |
| D-08 | SEQ `\r` 钉值，Word 端无法重编号 | render_plan.py:167 | R-006 |
| D-09 | darwin 硬编码 `/tmp` 无回退 | office_refresh.py:592、pdf_preview.py:567 | R-027 |
| D-10 | 公式编号无右对齐制表位 | equations.py:148 | R-008 |
| D-11 | TOC 无 cached 条目 | renderer.py:230-233 | R-006 |
| D-12 | PDF 预览失败静默 | services.py:282 | R-027 |
| D-13 | 无 w:hyperlink（citation/交叉引用不可点击） | renderers/docx/inlines.py | R-006 |
| D-14 | 无 reference.docx，样式来自 python-docx 默认模板 | document.py:76 | R-004 |
| D-15 | GB/T 仅 5 类型、无 et al、无 CSL | bibliography/ | R-010/R-011 |

## 6. Phase 0 输入建议

1. Parser spike 必须量化：Pandoc JSON AST 的 source position 粒度、对 `:::` 容器/citation/crossref 等自定义语法的扩展成本、与现有 396 行 parser 的功能差距。
2. OMML spike 必须先量化现有 LaTeX 子集对 30–50 公式 corpus 的覆盖率，再决定是否引入成熟转换后端。
3. Citation spike 以 GB/T golden corpus 为判据对比 Pandoc citeproc 与 citeproc-py，同时评估替换手写 formatter 的迁移成本。
4. reference.docx/shell.docx spike 需验证：从真实 DOCX 抽取样式/主题/节属性后，现有 renderer 的页面几何与样式写入逻辑能否改为「从 reference 继承」。
5. 门禁工具优先做 OpenXML/OPC 校验 + 三软件（本机 Word/WPS/LibreOffice 均可用）no-repair 打开验证，因为它是后续所有 Phase 的验收基础设施。
