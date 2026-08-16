# ThesisForge 六域质量与测试证据策略

> 状态：Proposed  
> 适用版本：Engineering Preview 至 V1 GA

## 1. 质量目标

ThesisForge 的测试不能只回答“是否生成了 `.docx`”，必须回答：

1. 输入是否被正确解析；
2. 论文语义、编号和引用是否正确；
3. 学校模板规则是否被正确应用；
4. Word 对象是否为真实、合法、可编辑的 OOXML；
5. 在目标办公软件中是否达到承诺的兼容水平；
6. 构建是否安全、离线、可复现、可安装和可维护。

因此采用六域测试模型，并为每个正式用例保存可审计证据。

---

## 2. 六域模型

## D1 — Syntax & Parser

覆盖：

- Front Matter；
- headings；
- paragraphs/inlines；
- ordered/bullet lists；
- tables；
- footnotes；
- citations；
- cross references；
- math；
- code；
- custom containers；
- source positions；
- multi-file includes；
- malformed syntax；
- encoding/BOM/line endings；
- unknown syntax policy。

主要测试类型：

- parser unit tests；
- AST snapshots；
- source map assertions；
- fuzz/property tests；
- negative fixtures。

示例用例：

```text
TF-D1-HDG-001  带显式 ID 的一级标题
TF-D1-INL-004  同一段落中的强调、引用、链接和行内公式
TF-D1-TBL-007  表格对齐和单元格行内节点
TF-D1-ERR-012  未闭合 semantic container
TF-D1-SRC-018  include 后的源文件和行列映射
```

## D2 — Semantic & Validation

覆盖：

- metadata schema；
- required regions；
- duplicate IDs；
- ID prefix/type；
- heading hierarchy；
- missing reference；
- citation key；
- bibliography file；
- symbol table；
- numbering；
- appendix numbering；
- template compatibility；
- diagnostics location and fix suggestions；
- strict mode。

主要测试类型：

- schema tests；
- semantic resolution tests；
- diagnostics golden tests；
- multi-location diagnostics；
- JSON/SARIF schema tests。

示例用例：

```text
TF-D2-ID-001   跨文件重复 ID
TF-D2-REF-004  fig: 引用错误指向 table
TF-D2-NUM-010  图表按章编号并在附录重启
TF-D2-META-015 缺少 student_id 的模板级错误
TF-D2-DIAG-022 JSON/SARIF 中保留精确 SourceSpan
```

## D3 — Template & Layout

覆盖：

- template schema；
- template inheritance；
- reference.docx；
- optional shell.docx；
- style mapping；
- fonts；
- page size/margins/orientation；
- section policy；
- headers/footers；
- page number format/restart；
- cover/declaration/abstract；
- template migration；
- provenance/license；
- template lint/test/pack。

主要测试类型：

- schema positive/negative tests；
- style presence and inheritance tests；
- section XML assertions；
- template fixture E2E；
- migration tests。

示例用例：

```text
TF-D3-SCH-001  非法长度单位被拒绝
TF-D3-STY-006  模板缺少正文 style ID
TF-D3-SEC-012  前置页罗马数字、正文阿拉伯数字重启
TF-D3-HDR-016  首页与奇偶页页眉策略
TF-D3-MIG-021  schema v1 模板迁移到 v2
```

## D4 — Academic Objects & Fields

覆盖：

- figures；
- structured tables；
- equations/OMML；
- listings/algorithms；
- footnotes；
- bookmarks；
- SEQ/REF/PAGEREF；
- TOC/list of figures/list of tables；
- PAGE/NUMPAGES；
- citations/bibliography；
- cached field results；
- update-on-open；
- finalization。

主要测试类型：

- unit tests for OOXML builders；
- XPath assertions；
- package relationship tests；
- field instruction parsing；
- citation golden corpus；
- editable object manual checks。

示例用例：

```text
TF-D4-FIG-001  图 3-2 的 SEQ、Bookmark 和 REF
TF-D4-TBL-008  三线表、跨页表头和纵向合并
TF-D4-EQ-014   带编号的可编辑 OMML 公式
TF-D4-TOC-019  三级目录字段和可读缓存结果
TF-D4-CIT-026  GB/T 7714-2025 多文献引用与文后表
TF-D4-FLD-031  update-on-open 与 dirty 状态
```

## D5 — Compatibility & Visual

覆盖：

- Microsoft Word desktop；
- WPS Writer；
- LibreOffice Writer；
- no-repair-open；
- field refresh behavior；
- font substitution；
- pagination；
- cover layout；
- heading/paragraph spacing；
- figures/tables/equations；
- PDF export；
- screenshot visual comparison。

主要测试类型：

- application matrix；
- human checklist；
- PDF render and page images；
- region-aware visual diff；
- page count and anchor checks；
- screenshots/video for UI phases。

示例用例：

```text
TF-D5-WRD-001  Word 打开无修复提示
TF-D5-WPS-004  WPS 中页码和交叉引用保持可用
TF-D5-LO-008   LibreOffice 可打开并导出 PDF
TF-D5-VIS-012  封面关键区域视觉回归
TF-D5-FNT-017  缺失中文字体时的诊断与替代
```

## D6 — Release & Non-functional

覆盖：

- performance；
- memory；
- large thesis；
- deterministic builds；
- offline installation；
- packaging；
- update/migration；
- security/path traversal；
- remote resource policy；
- malformed files；
- atomic output；
- logs/privacy；
- SBOM/licenses；
- CLI exits and machine-readable contracts。

主要测试类型：

- benchmark tests；
- reproducibility comparisons；
- installation matrix；
- security tests；
- chaos/failure injection；
- CLI contract tests。

示例用例：

```text
TF-D6-PERF-001  300 页论文基准
TF-D6-REP-004   两次 clean build 的规范化包一致
TF-D6-SEC-009   ../ 和符号链接逃逸被阻止
TF-D6-OFF-013   无网络环境安装和 build
TF-D6-ATM-018   build 失败不覆盖上次成功文件
```

---

## 3. 测试层级

```text
                 Manual compatibility / acceptance
                         Visual regression
                  End-to-end project fixtures
             Package/OpenXML/relationship validation
                  Compiler resolution contracts
             Parser/schema/diagnostics contracts
                       Unit tests
```

### 3.1 Unit

适合：

- units parser；
- bookmark sanitizer；
- numbering formatter；
- OOXML field builders；
- path policy；
- citation item conversion；
- XML normalization。

### 3.2 Contract

适合：

- Source AST；
- Normalized IR；
- Resolved IR；
- diagnostics JSON/SARIF；
- template schema；
- CLI exit codes。

Contract snapshot 需要版本化，修改时必须说明是否为 breaking change。

### 3.3 Structural DOCX

DOCX 解包后检查：

- required parts；
- relationships；
- content types；
- `document.xml`；
- `styles.xml`；
- `numbering.xml`；
- `settings.xml`；
- headers/footers；
- footnotes；
- bibliography-related output；
- media；
- bookmarks and fields；
- OMML。

应优先使用语义 XPath 断言，不要完全依赖整份 XML 文本快照。

### 3.4 Golden

适合：

- citation strings；
- bibliography entries；
- diagnostic messages/codes；
- normalized XML fragments；
- numbering outputs；
- manifest content。

Golden 更新必须经过人工审查，不能在 CI 中自动接受。

### 3.5 Visual

建议流程：

```text
DOCX
  ↓ LibreOffice headless / Word finalizer
PDF
  ↓ page rasterization
PNG pages
  ↓ crop/mask/compare
visual report
```

注意：LibreOffice 预览不是 Word 的权威像素基准。其作用是发现大范围回归，并提供跨平台自动化证据；GA 的关键模板仍需在 Word 中人工验收。

### 3.6 Compatibility

每个目标应用记录：

- application/version/build；
- OS；
- installed fonts；
- open/repair behavior；
- field refresh；
- pagination；
- known deviations；
- screenshot/PDF；
- reviewer and date。

---

## 4. 用例目录模型

建议使用 YAML 或 JSON 维护机器可读用例：

```yaml
id: TF-D4-REF-001
title: 图题注与交叉引用
version: 1
status: active
domain: D4
priority: P0
requirements:
  - MD-FIG-001
  - CMP-REF-003
  - DOCX-FIELD-002
releases:
  - alpha
  - beta
  - ga
input:
  project: fixtures/figure-reference
  template: templates/schools/example-university/2026
steps:
  - run: thesisforge build . --profile draft
  - inspect_xpath: //w:bookmarkStart[@w:name='tf_fig_model']
expected:
  exit_code: 0
  diagnostics_errors: 0
  artifacts:
    - output/thesis.docx
  fields:
    - type: SEQ
      instruction_contains: "Figure"
    - type: REF
      target: tf_fig_model
evidence:
  required:
    - build-report
    - docx
    - xml
    - pdf
    - screenshot
owners:
  component: compiler-fields
```

### ID 规范

```text
TF-D<domain>-<area>-<sequence>
```

- ID 永不复用；
- 标题可修改，ID 不变；
- 废弃用例保留记录；
- 每个 P0/P1 需求必须至少关联一个用例。

---

## 5. 两个 HTML 页面

## 5.1 六域测试用例清单

建议输出：`qa-site/catalog/index.html`

页面信息架构：

- 顶部总览：总数、P0/P1、域分布、自动化率、覆盖率；
- 过滤：域、优先级、release、组件、模板、自动/人工、状态；
- 主表：ID、标题、域、需求、优先级、自动化、最近结果、owner；
- 用例详情抽屉：输入、步骤、预期、依赖、历史、关联 issue；
- 规范覆盖视图：requirement → cases；
- 未覆盖项清单；
- 导出 JSON/CSV。

## 5.2 测试结果与证据清单

建议输出：`qa-site/runs/<run-id>/index.html`

页面信息架构：

- Run 摘要：commit、环境、模板、应用、时长、通过率；
- 域级 scorecard；
- 失败聚类；
- 用例结果表；
- 每个用例的证据详情；
- DOCX/PDF 下载；
- 页面截图前后对比；
- XML XPath/片段证据；
- 日志和 diagnostics；
- 兼容矩阵；
- issue 链接；
- 重跑与历史趋势。

核心编译器用例的主要证据是：

- 源 fixture；
- 模板版本；
- `.docx`；
- build report；
- normalized/resolved IR（debug profile）；
- OOXML 片段；
- PDF；
- 页面截图；
- 应用兼容检查；
- 哈希和环境信息。

桌面 UI 阶段再将视频作为常规证据类型。

---

## 6. 证据目录

```text
qa/
├── catalog/
│   ├── cases/
│   │   ├── TF-D1-HDG-001.yaml
│   │   └── ...
│   ├── requirements.yaml
│   └── suites.yaml
├── fixtures/
│   ├── parser/
│   ├── templates/
│   ├── e2e/
│   └── stress/
├── baselines/
│   ├── xml/
│   ├── citations/
│   └── visual/
├── tools/
│   ├── build_catalog.py
│   ├── collect_evidence.py
│   ├── normalize_docx.py
│   └── render_visual.py
└── results/
    └── <run-id>/
```

正式 run 的产物不应直接提交全部二进制到主分支。建议：

- 小型 golden/fixture 进入 Git；
- 大型 DOCX/PDF/截图进入 CI artifact 或对象存储；
- `run.json` 和摘要可长期保留；
- 发布候选的关键证据归档并带哈希。

---

## 7. DOCX 规范化策略

直接比较 `.docx` 二进制没有意义，因为 ZIP 顺序、时间戳、relationship IDs、文档属性等可能变化。

建议规范化过程：

1. 安全解包；
2. 校验 OPC 结构；
3. XML canonicalization；
4. 规范化 namespace prefix；
5. 删除或替换允许变化的时间戳；
6. 规范化无业务意义的 rsid；
7. 对 relationship 做稳定排序和映射；
8. 对 media 计算内容哈希；
9. 输出 semantic manifest；
10. 比较关键 XPath、parts 和 manifest。

不得为了“快照稳定”而删除具有业务意义的字段、样式或 section 信息。

---

## 8. OpenXML/OPC 门禁

每个 E2E DOCX 至少经过：

- ZIP 完整性；
- `[Content_Types].xml`；
- relationship target existence；
- duplicate relationship IDs；
- XML well-formed；
- Open XML SDK validator；
- bookmark start/end pairing；
- field begin/separate/end pairing；
- media relationship；
- section properties；
- style references；
- numbering references；
- footnote references；
- no Word repair prompt。

已知 validator 兼容差异需要通过有理由、有范围、有到期日的 allowlist 管理。

---

## 9. 视觉回归策略

### 9.1 页面分区

对以下区域单独建立视觉基线：

- cover；
- declarations；
- abstract；
- TOC；
- chapter opening；
- normal body；
- figure page；
- table page；
- equation page；
- bibliography；
- appendix。

### 9.2 差异分类

- P0：内容丢失、重叠、裁切、页眉页脚错误、页码错误、对象不可见；
- P1：分页严重漂移、表格跨页错误、题注错位、字体错误；
- P2：细微字距、抗锯齿或渲染器差异；
- Ignore：时间戳、动态域或已声明可变区域。

### 9.3 基线更新

必须记录：

- 为什么更新；
- 对应 issue/PR；
- reviewer；
- 旧/新截图；
- 是否影响模板版本；
- 是否属于 breaking layout change。

---

## 10. 性能与压力

建议建立以下 fixture：

- `small`：20 页；
- `normal`：80–120 页；
- `large`：300 页；
- `image-heavy`：200 张图片；
- `citation-heavy`：1000 条引用、3000 citation occurrences；
- `table-heavy`：100 张表、跨页和合并；
- `math-heavy`：500 个公式；
- `multi-file`：100 个 Markdown 文件。

记录：

- wall time；
- phase breakdown；
- peak RSS；
- output size；
- finalizer time；
- PDF render time。

Phase 0 建立基线，之后 CI 检测相对回退。绝对目标应在真实环境数据出现后确定。

---

## 11. 安全测试

至少覆盖：

- `../` path traversal；
- absolute paths outside allowed roots；
- symlink escape；
- remote image URL；
- file URI；
- oversized images；
- decompression bomb；
- deeply nested YAML；
- duplicate YAML keys；
- malicious XML in template package；
- external relationships；
- macros in shell/reference docx；
- executable attachments；
- temporary directory leakage；
- log redaction；
- plugin/provider permissions。

模板包默认应拒绝宏和未声明外部关系。

---

## 12. CI 分层

### Pull Request

- unit；
- parser/schema contracts；
- lint/type checks；
- small E2E；
- OOXML structure；
- security fast suite。

### Main/Nightly

- full fixture corpus；
- visual regression；
- large/stress；
- reproducibility；
- template matrix；
- LibreOffice headless；
- dependency/license scan。

### Release Candidate

- all P0/P1 automated cases；
- OpenXML validation；
- Word/WPS/LibreOffice manual matrix；
- three representative template acceptance；
- offline install；
- signed package/SBOM；
- evidence site archive。

---

## 13. Release Gate

### Engineering Preview

- P0 spike cases complete；
- Parser/Math/Fields/Citation/Template/Validation evidence available；
- no unresolved architecture blocker。

### Alpha

- one template full E2E；
- D1–D4 P0 cases pass；
- Word opens without repair；
- known limitations documented。

### Beta

- three templates；
- D1–D6 P0 pass；
- P1 pass rate达到团队设定门槛；
- compatibility matrix evidence complete；
- no open severity-1 defects。

### GA

- all release blockers closed；
- approved allowlist only；
- reproducible/offline/package tests pass；
- documentation and template authoring workflow complete；
- evidence archive frozen and hashed。

---

## 14. 缺陷分级

| 级别 | 定义 | 示例 |
|---|---|---|
| S1 | 数据损坏、无法打开、错误引用或严重学术正确性问题 | Word 修复、引用指错、正文丢失 |
| S2 | 核心功能错误或明显版式失败 | 页码策略错误、公式不可编辑、表格裁切 |
| S3 | 有 workaround 的中等问题 | 个别模板样式偏差、非关键诊断不足 |
| S4 | 轻微视觉或体验问题 | 小范围间距、文案、非阻断性能波动 |

GA 不允许未豁免的 S1/S2。

---

## 15. Test Case Definition of Done

一个正式用例必须具备：

- 稳定 ID；
- 需求和规范映射；
- 明确输入；
- 可重复步骤；
- 可机器判断的预期结果；
- 必要人工检查项；
- 环境要求；
- 所需证据；
- owner；
- 自动化状态；
- 最近结果；
- 失败时的 issue 链接。

只有用例文本、没有 fixture 和证据的测试清单，不算真正建立质量体系。
