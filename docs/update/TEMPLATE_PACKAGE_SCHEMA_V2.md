# ThesisForge Template Package v2 Schema 设计文档

> 状态：Design（可实现级）  
> 上游文档：`docs/update/TEMPLATE_PACKAGE_SPEC_V2.md`（概念级草案，下称 SPEC_V2）  
> 实证依据：`spikes/phase0/docx-template/REPORT.md`（下称 SPIKE）  
> 迁移对象：`src/thesis_forge/templates/model.py` + `docs/TEMPLATE_SPEC.md`（v0.3）  
> 风险关联：R-004 / R-005 / R-012 / R-020 / R-026

## 0. 文档定位与阅读约定

本文件把 SPEC_V2 的概念设计落成可实现的 schema：每个字段给出类型、单位、枚举、
默认值、必需性和 lint 规则；SPEC_V2 未回答或与其冲突之处，在正文对应位置以
「**偏差记录 C-n**」显式标注，并在第 10 章汇总。关键设计决策以「**决策 D-n**」
编号，附录 A 提供决策摘要。

约定：

- 「必需/可选」指模板作者角度；带「条件必需」的字段给出触发条件。
- 所有 lint 规则注明默认级别：`error`（阻断加载/构建）、`warning`、`info`。
- 诊断码沿用 v0.3 已有码（`invalid-template`、`missing-template-style`），
  新增码在各章定义，统一使用 kebab-case。
- 本文件不引入任何网络加载、代码执行或 AI 依赖；全部规则可离线确定性校验
  （R-020、AGENTS.md §1.3）。
- 长度写 `Length`、版本范围写 `SemverRange`，均见第 2 章。

## 1. 包结构与文件清单

目录结构沿用 SPEC_V2 §3，逐项标注 schema 约束。包有两种等价形态：

- **目录形态**（authoring）：模板作者维护的源码目录；
- **打包形态**（distribution）：`.tftpl` 文件（第 7 章），内容为目录形态的
  确定性 ZIP 快照外加 `manifest.json`。

两种形态由同一 loader 读取，lint 规则一致；打包形态额外强制哈希与签名检查。

### 1.1 文件清单与约束

| 路径 | 必需性 | 类型/格式 | 校验规则 | lint 层 |
| --- | --- | --- | --- | --- |
| `template.yaml` | 必需 | UTF-8 YAML | 本文件第 3 章全量 schema；未知字段一律拒绝（`extra=forbid`）；`schema_version` 必须为整数 `2` | L2 |
| `reference.docx` | 必需 | OOXML OPC 包 | OpenXML 校验通过；无宏/外部关系/OLE（§5.5）；正文为空或仅含允许清理的占位段落；包含全部必需 style token 对应样式（§3.7） | L1/L3 |
| `shell.docx` | 可选 | OOXML OPC 包 | 同上安全规则；锚点协议见 §5.2；存在时 `tf_body` 锚点必需 | L1/L3 |
| `assets/**` | 可选 | 图片（png/jpg/jpeg/gif/emf/svg*）等静态资源 | 仅允许被 layouts/shell 引用的相对路径；路径安全（§1.3）；被引用文件必须存在（`missing-template-asset`，error） | L1 |
| `layouts/<name>.yaml` | 可选 | UTF-8 YAML | §3.20 Layout schema；必须被 `template.yaml` 的 `layouts` 节显式引用，未被引用的 layout 文件报 warning | L2 |
| `styles/aliases.yaml` | 可选 | UTF-8 YAML | §3.7.3 schema；键必须是已声明的 style token 值 | L2 |
| `citations/style.csl` | 条件必需 | CSL 1.0.1 XML | 当 `bibliography.provider: default` 且论文启用参考文献时必需；SHA-256 必须与 `provenance.yaml` 记录一致（`hash-mismatch`，error） | L1/L4 |
| `citations/overrides.yaml` | 可选 | UTF-8 YAML | 结构由 bibliography subsystem 定义；本文件只约束存在性与路径安全 | L2 |
| `fixtures/minimal/` | 必需 | Markdown + 资源 | 可零 error 构建（L5）；覆盖 Front Matter、标题、正文、至少一个图/表/公式/引用中的最小集合 | L5 |
| `fixtures/full/` | 可选（Beta 必需） | 同上 | 覆盖模板声明的全部 region 与对象类型 | L5 |
| `fixtures/edge-cases/` | 可选 | 同上 | 覆盖深层列表、超宽表格、长题注、空 metadata 等边界 | L5 |
| `expected/manifest.json` | 可选（Beta 必需） | JSON | 声明期望产物清单与 XPath 断言集，schema 见 §6.5 | L5 |
| `expected/xml/**` | 可选 | XML 片段 | 被 `expected/manifest.json` 引用 | L5 |
| `expected/visual/**` | 可选 | PNG/PDF | 仅作相对回归基线，必须标注渲染引擎（R-028） | L5 |
| `provenance.yaml` | 必需 | UTF-8 YAML | §3.21 schema；缺失即 `provenance-missing`（error） | L1 |
| `CHANGELOG.md` | 打包时必需 | Markdown | 顶部版本号必须等于 `header.version`（`changelog-version-mismatch`，error）；目录形态开发期缺失为 warning | L1 |
| `LICENSES/` | 条件必需 | 文本 + SBOM | 包内含第三方资产（CSL、Logo、字体）时必需；建议提供 `SBOM.spdx.json` | L1 |
| `README.md` | 必需 | Markdown | 必须包含使用说明与「已知限制」一节；缺失 `readme-missing`（error） | L1 |

\* SVG 是否允许由目标应用兼容矩阵决定；允许时必须 sanitized（无 script/外部引用）。

最小包（SPEC_V2 §3）：`template.yaml` + `reference.docx` + `provenance.yaml` +
`fixtures/minimal/` + `README.md`。最小包也必须通过 L1–L3。

### 1.2 目录保留名与禁止项

- 包内禁止出现：以 `.` 开头的隐藏文件（lint 忽略但不打包）、绝对路径引用、
  指向包外的符号链接、`__MACOSX/`、`.DS_Store`（打包时剔除）。
- 保留路径：`manifest.json` 只允许出现在 `.tftpl` 根（打包产物），目录形态
  下出现同名文件报 `package-path-conflict`（warning，打包时剔除重建）。

### 1.3 路径安全（目录形态与打包形态共用）

所有包内路径必须满足：

1. 相对路径，不以 `/`、`\\`、盘符开头；
2. 规范化后不含 `..` 段；
3. 分隔符统一为 `/`；
4. 不解引用符号链接到包外；
5. 单文件解压后 ≤ 64 MB，包解压后总量 ≤ 512 MB（默认值，可在
   `thesisforge config` 下调但不允许关闭）。

违反任一条 → `package-path-unsafe`（error，加载即拒绝，R-020）。

## 2. 通用类型与单位解析

### 2.1 标量类型

| 类型 | 定义 | 说明 |
| --- | --- | --- |
| `Length` | 带单位字符串，算法见 §2.2 | 禁止裸数字 |
| `Semver` | `^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$` | 模板自身版本 |
| `SemverRange` | 逗号分隔的比较子句 | 语法见 §2.4 |
| `BCP47` | 语言标签，如 `zh-CN` | 只做语法校验，不校验注册表 |
| `SHA256Ref` | `sha256:` + 64 位小写十六进制 | 哈希引用统一格式 |
| `StyleTokenRef` | §3.7 定义的 token 名 | 跨节引用 |
| `Path` | 包内相对路径 | 受 §1.3 约束 |
| `Date` | ISO 8601 `YYYY-MM-DD` | provenance 使用 |

所有 YAML 模型节点 `extra=forbid`：未知字段 → `invalid-template`（error），
错误信息保留完整字段路径（沿用 v0.3 §12 约定）。

### 2.2 长度单位解析算法

单位全集：`mm`、`cm`、`pt`、`in`、`em`、`%`（v0.3 仅前四个中的
mm/cm/pt/em；`in` 与 `%` 为 v2 新增，与 SPEC_V2 §5 一致）。

**词法解析**（确定性，无环境依赖）：

```text
parse_length(raw, ctx) -> Length | invalid-template
1. raw 必须是 YAML 字符串；数字、null、列表 → 报错（字段路径）。
2. s = strip(raw)
3. m = fullmatch(r"([0-9]+(?:\.[0-9]+)?)(mm|cm|pt|in|em|%)", s)
   - 不接受符号（±）、科学计数法、内部空格、裸数字、其他单位。
4. unit ∉ ctx.allowed_units → 报错（注明该字段允许的单位集）。
5. ctx.positive == true 且 value <= 0 → 报错。
6. 返回 Length{value: Decimal, unit}。
   字符串规范化形式：去尾零（"10.50pt" → "10.5pt"，沿用 v0.3 行为）。
```

**求值**（构建期，Renderer 使用）：

```text
resolve(length, use_site) -> twips 整数 | 比例
- 绝对单位先换算为 Decimal 磅（pt）：
    pt = value；in = value × 72；cm = value × 72 / 2.54；mm = value × 72 / 25.4
  再 ×20 换算 twips，ROUND_HALF_UP 取整（确定性与 Word 存储一致）。
- em：value × use_site 有效字号（pt）。
  有效字号解析顺序：目标角色显式字号 → 其 basedOn 链 → body 有效字号。
  若解析到的字号本身以 em 表示，则以 body 的绝对字号为基准
  （沿用 v0.3 §3.2 规则）。body 角色有效字号必须最终解析为绝对值，
  否则 L4 `non-absolute-body-size`（error）。
- %：value / 100 × ctx.base。
  base 定义：当前 section 正文栏宽
      = page.width − margin.inner − margin.outer − gutter
  columns > 1 时再按栏宽均分后取单栏宽。嵌套上下文（表格单元格内 %）
  的 base 未定义，见开放问题 OQ-9；schema 暂禁止嵌套 %（L2 error）。
```

### 2.3 单位上下文矩阵

| 上下文类别 | 代表字段 | 允许单位 | 额外约束 |
| --- | --- | --- | --- |
| 页面物理几何 | `page.margin.*`、`page.gutter`、`page.header_distance`、`page.footer_distance`、`page.document_grid.line_pitch` | mm/cm/pt/in | `line_pitch`、`margin.*` ≥ 0；`line_pitch` 非 default 网格时必需且 > 0 |
| 物理线宽/边框 | `tables.styles.*.borders.*`、页眉 `bottom_border.width` | mm/cm/pt/in 或 `none`（仅 borders） | > 0 且换算后 ∈ [0.25pt, 12pt]（沿用 v0.3 Word 1/8pt 约束） |
| 字号 | style 内字号（主要由 reference.docx 承载）、YAML 白名单字号字段 | pt（绝对）；非 body 角色允许 em | body 基准必须绝对（§2.2） |
| 缩进与段距 | `first_line_indent`、`hanging_indent`、`left/right_indent`、`space_before/after`、`toc.levels.*.page_number_tab`、`bibliography.hanging_indent` | mm/cm/pt/in/em | `page_number_tab` > 0；`first_line_indent` 与 `hanging_indent` 不得同时为正（沿用 v0.3） |
| 固定行距 | `line_spacing.value`（type=fixed） | mm/cm/pt/in/em | em 按目标样式有效字号解析 |
| 父宽比例 | `figures.max_width`、`figures.default_width`、`tables.width`、`tables.overflow.threshold`、layout block `width` | % 或 mm/cm/pt/in | % ∈ (0, 100]；`overflow.threshold` 允许 > 100 用于诊断延迟触发 |
| 图片最大高度 | `figures.max_height` | mm/cm/pt/in | > 0 |
| 栏间距 | `sections.*.columns.spacing` | mm/cm/pt/in | ≥ 0 |

### 2.4 SemverRange 语法

```text
range   := clause ("," clause)*
clause  := op version | caret version
op      := ">=" | ">" | "<=" | "<" | "==" | "!="
caret   := "^" version        # 等价于 >=version 且 < 下一主版本
version := Semver（允许省略 patch，省略位视为 0）
```

示例：`">=1.0,<2.0"`、`"^2.0"`。解析失败 → `invalid-template`。
`extends.version` 与 `compatibility.thesisforge` 均使用此语法。

## 3. `template.yaml` 逐节 schema

顶层字段一览：

| 字段 | 必需性 | 内容 |
| --- | --- | --- |
| `schema_version` | 必需 | 常量 `2`（§3.1） |
| `id` `version` `name` `language` `status` | 必需（language/status 有默认） | header（§3.1） |
| `compatibility` | 必需 | §3.2 |
| `extends` | 可选 | §3.3 |
| `word` | 必需 | §3.4 |
| `page` | 必需 | §3.5 |
| `fonts` / `font_policy` | 必需 / 可选 | §3.6 |
| `styles` | 必需 | §3.7 |
| `body` | 必需 | §3.8 |
| `headings` | 必需 | §3.9 |
| `regions` | 必需 | §3.10 |
| `sections` | 必需 | §3.11 |
| `numbering` | 必需 | §3.12 |
| `figures` / `tables` / `equations` | 可选 | §3.13–3.15 |
| `fields` / `cross_references` / `toc` | 可选（有默认） | §3.16–3.18 |
| `bibliography` | 可选 | §3.19 |
| `layouts` | 可选 | §3.20 |

省略 `figures`/`tables`/`equations`/`bibliography` 而论文实际使用对应对象时，
Validator 报 `missing-template-style`（沿用 v0.3 语义）。

### 3.1 header

| 字段 | 类型 | 默认 | 必需性 | 校验 / lint |
| --- | --- | --- | --- | --- |
| `schema_version` | int | 无 | 必需，必须等于 `2` | 其他值 → `unsupported-schema-version`（error，§8.3） |
| `id` | str | 无 | 必需 | `^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*$`；包内全局唯一；继承解析键 |
| `version` | Semver | 无 | 必需 | 打包时与 CHANGELOG 顶部一致（L1） |
| `name` | str | 无 | 必需，非空 | 人类可读名称 |
| `language` | BCP47 | `zh-CN` | 可选 | 写入 docDefaults 语言的参考值 |
| `status` | enum | `draft` | 可选 | `draft`/`active`/`deprecated`/`archived`；语义见 §9.3 |

### 3.2 compatibility

| 字段 | 类型 | 默认 | 必需性 | 校验 / lint |
| --- | --- | --- | --- | --- |
| `thesisforge` | SemverRange | 无 | 必需 | 加载时检查宿主版本，不满足 → `incompatible-thesisforge`（error，CP2） |
| `document_types` | list[enum] | 无 | 必需，非空 | `bachelor_thesis`/`master_thesis`/`phd_thesis`/`course_paper`/`report` |
| `target_apps` | map | `{word: primary}` | 可选 | 键 ∈ `{word, wps, libreoffice}`；值 ∈ `primary`/`compatible`/`preview`/`unsupported`；`primary` 恰允许一个（L2 error 若多个） |

### 3.3 extends

```yaml
extends:
  id: thesisforge.base.bachelor.zh-cn
  version: "^2.0"
  sha256: "sha256:..."   # 可选锁定
```

| 字段 | 类型 | 默认 | 必需性 | 校验 / lint |
| --- | --- | --- | --- | --- |
| `id` | str | 无 | 必需 | 必须能在本地模板根解析（禁止网络加载，SPEC_V2 §4.2）；解析失败 → `missing-template` |
| `version` | SemverRange | 无 | 必需 | 解析到的父模板版本不满足 → `unsatisfied-parent-version`（error） |
| `sha256` | SHA256Ref | None | 可选 | 提供时与父模板内容哈希不一致 → `hash-mismatch`（error） |

合并语义（字段白名单、list replace、禁环、manifest 记录）见 §4.3 决策 D-2。

### 3.4 word

| 字段 | 类型 | 默认 | 必需性 | 校验 / lint |
| --- | --- | --- | --- | --- |
| `reference_docx` | Path | `reference.docx` | 可选 | 文件必须存在且通过 §5.1 契约（L3） |
| `shell_docx` | Path \| None | None | 可选 | 存在时通过 §5.2 契约（L3） |
| `macro_policy` | enum | `forbid` | 可选 | 仅允许 `forbid`（v2 无其他合法值；写其他值 → L2 error） |
| `external_relationships` | enum | `forbid` | 可选 | `forbid`/`allowlist`；`allowlist` 时必须给出下字段 |
| `external_relationship_allowlist` | list[str] | `[]` | 条件必需 | 仅当上一字段为 `allowlist`；每项为协议+主机白名单（如 `https://example.edu`）；L1/L3 逐条比对 |
| `anchors` | map | 见下 | 可选 | 键 ∈ `{body, toc, bibliography}`；值匹配 `^tf_[a-z0-9_]+$`，三键值互不相同（L2 error） |

`anchors` 默认：`{body: tf_body, toc: tf_toc, bibliography: tf_bibliography}`。
锚点协议与消费语义见 §5.2。

### 3.5 page

| 字段 | 类型 | 单位/枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `size` | enum | `A3`/`A4`/`A5`/`Letter`/`Legal` | `A4` | 可选 | — |
| `orientation` | enum | `portrait`/`landscape` | `portrait` | 可选 | — |
| `margin.top/bottom/inner/outer` | Length | 绝对单位 | 无 | 必需 | ≥ 0；`inner/outer` 语义见下 |
| `gutter` | Length | 绝对单位 | `0mm` | 可选 | ≥ 0 |
| `mirror_margins` | bool | — | `false` | 可选 | `false` 时 `inner≡left`、`outer≡right`（Word 非镜像行为） |
| `header_distance` / `footer_distance` | Length | 绝对单位 | None | 可选 | ≥ 0 |
| `document_grid.type` | enum | `default`/`lines`/`lines_and_chars`/`snap_to_chars` | `lines` | 可选 | 非 `default` 时 `line_pitch` 必需且 > 0（沿用 v0.3） |
| `document_grid.line_pitch` | Length | 绝对单位 | None | 条件必需 | > 0 |
| `document_grid.char_space` | int | — | None | 可选 | — |

说明：SPEC_V2 §5 示例未列出 `header_distance/footer_distance/document_grid`，
但 reference.docx 职责清单（SPEC_V2 §4.3）包含 page setup，且 v0.3 已有这三
字段；本 schema 予以保留，不构成偏差。page 属「结构语义类」，YAML 为唯一权威，
reference.docx sectPr 中的对应值仅作漂移比对（§4.1 D-1 分类，L3
`template-reference-drift`，warning）。

### 3.6 fonts 与 font_policy

```yaml
fonts:
  body:
    east_asia: SimSun
    latin: Times New Roman
    complex_script: Times New Roman
    fallback:
      east_asia: [Noto Serif CJK SC]
      latin: [Liberation Serif]
  code: {...}
font_policy:
  missing_primary: error
  missing_fallback: warning
  embed_fonts: false
```

| 字段 | 类型 | 默认 | 必需性 | 校验 / lint |
| --- | --- | --- | --- | --- |
| `fonts.<role>.east_asia` | str | 无 | 必需 | 角色字体族要求；非空 |
| `fonts.<role>.latin` | str | 无 | 必需 | 同时作为 ASCII 与 High ANSI 默认 |
| `fonts.<role>.high_ansi` | str | = `latin` | 可选 | SPEC_V2 §6 要求区分四槽位 |
| `fonts.<role>.complex_script` | str | = `latin` | 可选 | — |
| `fonts.<role>.fallback.<slot>` | list[str] | `[]` | 可选 | 按序候选；`doctor` 探测 |
| `font_policy.missing_primary` | enum | `error` | 可选 | `error`/`warning`；`doctor` 与构建期字体探测使用（R-013） |
| `font_policy.missing_fallback` | enum | `warning` | 可选 | 同上 |
| `font_policy.embed_fonts` | bool | `false` | 可选 | `true` 时要求 LICENSES 含字体授权（L1 error 缺失） |

已知角色：`body`、`code`、`heading`、`caption`。未知名角色 → L2 warning
（允许模板先行，渲染器忽略未知角色）。字体族名是逻辑要求而非平台内部名，
`doctor` 负责探测映射（SPEC_V2 §6）。

### 3.7 styles（style tokens）

#### 3.7.1 token 清单（规范表）

paragraph token：

| token | 必需性 | 说明 |
| --- | --- | --- |
| `body` | 必需 | 正文 |
| `body_first` | 可选 | 章后首段（不缩进场景） |
| `abstract` | 可选 | 摘要正文 |
| `bibliography` | 可选 | 参考文献条目 |
| `caption_figure` / `caption_table` | 条件必需 | 启用 figures/tables 时必需 |
| `equation` | 条件必需 | 启用 equations 时必需 |
| `listing` | 可选 | 代码块 |
| `footnote` | 可选 | 脚注文本；默认 `Footnote Text` 为内置样式，本地化问题见 §3.7.3 |

heading token：键 `1`–`4`，`1` 必需；启用级别被论文使用而缺失 →
`missing-template-style`。

character token：`emphasis`、`strong`、`code`、`hyperlink`，均可选，默认
映射 Word 内置样式。

#### 3.7.2 字段规则

| 字段 | 类型 | 校验 / lint |
| --- | --- | --- |
| `styles.paragraph.<token>` | str（reference.docx 中的样式名） | 值非空；L3 检查样式存在（`missing-token-style`，error）、类型匹配（`style-type-mismatch`，error） |
| `styles.heading.<1-4>` | 同上 | 同上，类型必须为 paragraph 且 outline level 与级别一致（L4 warning 不一致） |
| `styles.character.<token>` | 同上 | 类型必须为 character |

通用 L3/L4 规则（对应 SPEC_V2 §7）：style ID 重复（error）；`basedOn`/`next`/
`link` 引用必须存在于同一样式表（error）；不允许引用 reference.docx 中不存在
的样式（error）；token 值跨类别重复（同一名字同时作 paragraph 与 character
token）→ error。

#### 3.7.3 `styles/aliases.yaml`

**偏差记录 C-6**：SPEC_V2 §3 列出 `styles/aliases.yaml` 但未定义其结构；
§7 示例 `footnote: Footnote Text` 依赖内置样式的英文名，在中文版 Word 中
内部名可能本地化。本 schema 定义：

```yaml
# styles/aliases.yaml
"Footnote Text": ["脚注文本", "footnote text"]
"TF Body": ["正文TF"]
```

结构：`map[样式名, list[别名]]`。解析样式时先按主名、再按别名匹配
reference.docx 的 styles.xml；匹配到别名 → L3 info 并在 build manifest 记录
实际命中名。键必须是 §3.7 中已声明的 token 值（L2 error 否则）。

### 3.8 body

| 字段 | 类型 | 单位/枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `style` | StyleTokenRef | paragraph token | `body` | 可选 | 必须存在于 `styles.paragraph` |
| `alignment` | enum | `left`/`center`/`right`/`justify` | `justify` | 可选 | — |
| `first_line_indent` | Length | 缩进上下文 | None | 可选 | 与 reference.docx 样式重复定义时触发 §4.2 诊断 |
| `line_spacing.type` | enum | `single`/`multiple`/`fixed` | `fixed` | 可选 | 规则同 v0.3：fixed 需 Length value；multiple 需正浮点；single 禁带 value |
| `line_spacing.value` | Length \| float | 见 §2.3 | None | 条件必需 | 同上 |
| `spacing.before/after` | Length | 缩进上下文 | None | 可选 | — |
| `widow_control` | bool | — | None | 可选 | — |

本节全部为 §4.2 覆盖白名单字段：不写则以 reference.docx 中 `body` token
样式为准；写了则按 D-1 生效并产生诊断。

### 3.9 headings

```yaml
headings:
  1:
    style: 1
    page_break_before: true
    keep_with_next: true
    numbering:
      enabled: true
      pattern: "第{chapter_zh}章"
```

每级（键 `1`–`4`）字段：

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `style` | heading token 键 | = 级别号 | 可选 | 必须存在于 `styles.heading` |
| `page_break_before` | bool | None | 可选 | 白名单字段（D-1） |
| `keep_with_next` | bool | None | 可选 | 白名单字段 |
| `numbering.enabled` | bool | `true`（级别 1–3）/ `false`（级别 4） | 可选 | `false` 时 `pattern` 不得出现（L2 error） |
| `numbering.pattern` | str | 见下 | 可选 | 占位符词表见 §3.12.4；未知占位符 → error |

默认 pattern：级别 1 `"第{chapter_zh}章"`，级别 2 `"{chapter}.{section}"`，
级别 3 `"{chapter}.{section}.{subsection}"`，级别 4 无。标题其余版式属性
（字体/字号/段距/对齐）不在 YAML 表达，由 token 样式承载（SPEC_V2 §8
「样式优先」的具体化）。

### 3.10 regions

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `order` | list[region_id] | 无 | 必需 | 元素属于下方词表；唯一；必须含且仅含一个 `main`（L2 error） |
| `<region>.required` | bool | `false` | 可选 | `required: true` 的 region 在论文缺失时 → Validator `missing-region`（error） |
| `<region>.section` | section 键 | 见下 | 可选 | 必须存在于 `sections`（`numbering-source-missing` 类 error） |
| `<region>.title` | str | None | 可选 | 用于自动生成的 region 标题段 |
| `<region>.title_style` | heading token 键 | `1` | 可选 | — |
| `<region>.heading_numbering` | bool | `false`（main 内标题除外规则由 numbering 决定） | 可选 | cover/toc 类 region 必须为 `false`（L4 warning） |
| `<region>.anchor` | str | None | 可选 | 覆盖默认投递锚点（§5.2.3）；值必须匹配 `^tf_[a-z0-9_]+$` |

region_id 词表：`cover`、`originality_statement`、`authorization_statement`、
`abstract_zh`、`abstract_en`、`toc`、`main`、`bibliography`、`acknowledgements`、
`appendices`、`achievements`。词表外 id → L2 error（扩展机制未定，OQ-11）。

默认 section 映射：`cover→cover`；`abstract_zh/abstract_en/toc→front_matter`；
`main→main`；其余 → `back_matter`。

Region 与 Heading 不混同（SPEC_V2 §9）：封面、目录是结构单元，由本表表达；
标题编号由 §3.9/§3.12 表达。

### 3.11 sections

键词表：`cover`、`front_matter`、`main`、`back_matter`。每节字段：

| 字段 | 类型 | 单位/枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `start` | enum | `continuous`/`new_page`/`odd_page`/`even_page` | `new_page` | 可选 | **偏差记录 C-5**：SPEC_V2 §10 示例用 `next_page`，v0.3 与 Word 用 `new_page`/`nextPage`；本 schema 以 `new_page` 为规范值，接受 `next_page` 为别名并 info 提示 |
| `title_page` | bool | — | `false` | 可选 | `true` 时才允许 `header_footer.first` |
| `page_number.display` | bool | — | `true` | 可选 | `false` 时 `format/restart` 不得设置（L2 error，沿用 v0.3 `format: none` 语义） |
| `page_number.format` | enum | `decimal`/`roman-lower`/`roman-upper` | `decimal` | 可选 | 写入 `w:pgNumType`，注意 sectPr 子元素顺序（SPIKE §3.5） |
| `page_number.restart` | int | ≥ 1 | None | 可选 | 与 `continue` 互斥（L2 error） |
| `page_number.continue` | bool | — | `false` | 可选 | `true` 时不写 `w:pgNumType/@w:start` |
| `header_footer.default/first/even` | str | `none` \| 部件名 | `none` | 可选 | 部件名必须解析到 shell.docx 或 reference.docx 的 header/footer 部件（L3 `unresolved-header-footer-part`，error）；声明 `even` 会启用文档级奇偶设置（§5.4 settings 白名单） |
| `page.size` / `page.orientation` | enum | 同 §3.5 | None | 可选 | 横向表格页等 override |
| `columns.count` | int | 1–4 | 1 | 可选 | > 1 时 `spacing` 必需 |
| `columns.spacing` | Length | 绝对单位 | None | 条件必需 | ≥ 0 |
| `vertical_alignment` | enum | `top`/`center`/`both`/`bottom` | `top` | 可选 | — |
| `footnote_restart` | enum | `continuous`/`each_section`/`each_page` | `continuous` | 可选 | 需目标应用支持（L4 标注兼容矩阵） |

SPEC_V2 §10 要求的类型化能力（break type / 页码策略 / first-even-default /
title page / 页面 override / columns / vertical alignment / footnote restart）
全部落为上述字段。页眉页脚的**内容**（文字、边框、PAGE 域排版）不由 YAML
表达，由被引用的 header/footer 部件承载——这是 R-004 预防措施的落地
（「YAML 仅表达规则和映射」）。迁移映射见 §8.1。

### 3.12 numbering

#### 3.12.1 chapter

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `source` | enum | `heading_1` | 可选 | `heading_1`–`heading_4`；指向级别必须存在（L4 `numbering-source-missing`，error） |
| `format` | enum | `decimal` | 可选 | `decimal`/`lower_letter`/`upper_letter`/`lower_roman`/`upper_roman`/`chinese_counting`（Renderer-neutral，禁止 Word `w:numFmt` 直写，沿用 v0.3 原则） |
| `display` | pattern | `"第{n}章"` | 可选 | 占位符 `{n}` |

#### 3.12.2 figure / table

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `enabled` | bool | `true` | 可选 | **偏差记录 C-1b**：v0.3 `mode: none` 需要关闭编号；SPEC_V2 §11 无此字段，本 schema 增加 |
| `scope` | enum | `chapter` | 可选 | `chapter`/`continuous`（对应 v0.3 `mode`） |
| `sequence_name` | str | `TF_FIGURE` / `TF_TABLE` | 可选 | `^TF_[A-Z][A-Z0-9_]*$`；全模板唯一（L4 error）；渲染为真实 SEQ 域（AGENTS.md §1.5） |
| `separator` | str | `"-"` | 可选 | 章内编号连接符 |
| `caption_prefix` | str | `图` / `表` | 可选 | — |
| `caption_pattern` | pattern | `"{prefix} {number}  {caption}"` | 可选 | 占位符 `{prefix}`/`{number}`/`{caption}` |
| `reference_forms.number` | pattern | `"{number}"` | 可选 | 交叉引用显示形式 |
| `reference_forms.label_number` | pattern | `"{prefix} {number}"` | 可选 | — |
| `reference_forms.full` | pattern | `"{prefix} {number} {caption}"` | 可选 | — |
| `appendix.prefix` | str | 附录字母 | 可选 | 附录 scope 内的编号前缀策略 |
| `appendix.continue_numbering` | bool | `false` | 可选 | `false` = 附录内按附录字母重启 |

#### 3.12.3 equation

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `enabled` | bool | `true` | 可选 | 同上 |
| `scope` | enum | `chapter` | 可选 | 同上 |
| `sequence_name` | str | `TF_EQUATION` | 可选 | 同上 |
| `display` | pattern | `"（{number}）"` | 可选 | 占位符 `{number}` |

#### 3.12.4 占位符词表（L2 校验依据）

- 标题 pattern：`{chapter}`、`{chapter_zh}`、`{section}`、`{subsection}`；
- 章 display：`{n}`；
- 题注/引用：`{prefix}`、`{number}`、`{caption}`；
- 公式 display：`{number}`。

未知占位符 → `invalid-template`（error）。最终编号（图 3-2 / 表 4-1 /
式（3-1））由 Compiler 统一计算，模板不提供编号值（AGENTS.md §3）。

### 3.13 figures

| 字段 | 类型 | 单位/枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `placement` | enum | `inline`/`floating` | `inline` | 可选 | v2 渲染器仅保证 `inline`；`floating` → L4 warning（能力标记） |
| `alignment` | enum | `left`/`center`/`right` | `center` | 可选 | — |
| `max_width` | Length | 父宽比例上下文 | `100%` | 可选 | — |
| `max_height` | Length | 绝对单位 | `220mm` | 可选 | > 0 |
| `default_width` | Length | 父宽比例上下文 | None | 可选 | **偏差记录 C-1a**：SPEC_V2 §12 无此字段；v0.3 `figure.default_width` 迁移需要，本 schema 增加，建议回写 SPEC_V2 |
| `keep_with_caption` | bool | — | `true` | 可选 | — |
| `caption.position` | enum | `top`/`bottom` | `bottom` | 可选 | — |
| `caption.style` | StyleTokenRef | — | `caption_figure` | 可选 | 必须存在于 `styles.paragraph` |
| `source_note.policy` | enum | `required`/`optional`/`forbidden` | `optional` | 可选 | **偏差记录 C-4**：SPEC_V2 §12 写作 `enabled: optional`，字段名与值域不匹配；本 schema 更名为 `policy` |
| `source_note.style` | StyleTokenRef | — | `body` | 可选 | — |
| `format_allowlist` | list[enum] | `[png, jpg, jpeg, emf]` | 可选 | `gif`/`svg` 需显式开启；论文引用名单外格式 → `unsupported-image-format`（error） |
| `dpi_warning` | int | — | `150` | 可选 | 低于阈值 → warning（R-021 防线之一） |
| `max_bytes` | int | — | None | 可选 | 超限时 error |
| `alt_text` | enum | `required`/`optional` | `optional` | 可选 | `required` 时缺 alt → Validator error |
| `subfigure_support` | enum | `none`/`basic`/`full` | `none` | 可选 | 论文使用子图而支持不足 → error |
| `crop_policy` | enum | `forbid`/`allow` | `forbid` | 可选 | — |

### 3.14 tables

| 字段 | 类型 | 单位/枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `default_style` | str | `tables.styles` 键 | `three_line` | 可选 | 键必须存在（L2 error） |
| `width` | Length | 父宽比例 | `100%` | 可选 | — |
| `autofit` | bool | — | `false` | 可选 | — |
| `repeat_header` | bool | — | `true` | 可选 | — |
| `allow_row_break` | bool | — | `false` | 可选 | — |
| `caption.position` | enum | `top`/`bottom` | `top` | 可选 | — |
| `caption.style` | StyleTokenRef | — | `caption_table` | 可选 | — |
| `styles.<name>.borders.top/header_bottom/bottom` | Length | 物理线宽 | `1.5pt`/`0.75pt`/`1.5pt` | 可选 | [0.25pt, 12pt] |
| `styles.<name>.borders.inside_vertical/inside_horizontal` | Length \| `none` | — | `none` | 可选 | — |
| `styles.<name>.cell.vertical_alignment` | enum | `top`/`center`/`bottom` | `center` | 可选 | — |
| `styles.<name>.cell.padding.top/bottom/left/right` | Length | 绝对单位 | `1mm` | 可选 | ≥ 0 |
| `overflow.strategy` | enum | `diagnose`/`scale`/`landscape_section` | `diagnose` | 可选 | 不得静默压缩到不可读（SPEC_V2 §13）；`scale` 必须同时设 `min_scale` |
| `overflow.threshold` | Length | 父宽比例 | `100%` | 可选 | 超过即触发 strategy |
| `overflow.min_scale` | float | (0,1] | `0.6` | 可选 | 低于仍超宽 → error |

自定义表格样式名允许扩展（`styles.<name>` 键不锁定词表），但必须在
`default_style` 或文档指令中可解析。

### 3.15 equations

| 字段 | 类型 | 枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `converter` | str | `default` 或注册的转换后端名 | `default` | 可选 | 未注册后端 → error（R-008） |
| `inline_style` / `block_style` | StyleTokenRef | — | `equation_inline`/`equation` | 可选 | `equation_inline` 为 character token，需在 `styles.character` 声明 |
| `alignment` | enum | `left`/`center`/`right` | `center` | 可选 | — |
| `numbered_layout` | enum | `tab_stop`/`borderless_table`/`custom_paragraph` | `tab_stop` | 可选 | 当前 Word Renderer 已固定实现 `tab_stop`：50% 居中制表位 + 100% 右对齐制表位；其余值为保留枚举 |
| `number_alignment` | enum | `left`/`center`/`right` | `right` | 可选 | — |
| `unsupported_latex` | enum | `error`/`warning` | `error` | 可选 | 不得静默降级 |
| `image_fallback` | enum | `disabled`/`explicit` | `disabled` | 可选 | **偏差记录 C-7a**：SPEC_V2 §14 写 `disabled` 语义不全；`explicit` 表示仅当文档显式请求时允许图片回退（R-008 退路「不得静默开启」的落地） |

### 3.16 fields

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `update_on_open` | bool | `true` | 可选 | 写 `w:updateFields`（R-006） |
| `cached_results` | bool | `true` | 可选 | 域结果缓存策略 |
| `mark_dirty` | bool | `true` | 可选 | TOC/REF 域标 dirty |
| `finalizer.draft` | enum | `none` | 可选 | `none`/`auto`/`word` |
| `finalizer.final_auto` | enum | `auto` | 可选 | 同上 |
| `finalizer.final_word` | enum | `word` | 可选 | 同上；`word` 依赖本机 Word（R-027），`doctor` 探测 |

finalizer 与 shell 合并的顺序（编译→合并→finalizer 还是反之）见 OQ-10，
本文建议「编译 → 合并 → finalizer」。

### 3.17 cross_references

| 字段 | 类型 | 枚举 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `default_form` | enum | `number`/`label_number`/`full` | `label_number` | 可选 | 必须存在于对应对象的 `reference_forms` |
| `page_reference` | bool | — | `false` | 可选 | `true` 时引用含 PAGEREF 域 |

### 3.18 toc

| 字段 | 类型 | 枚举/单位 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `enabled` | bool | — | `true` | 可选 | `false` 时论文含目录 region → L4 warning |
| `depth` | int | 1–4 | `3` | 可选 | `levels` 中键 > depth → L4 warning（不生效配置） |
| `title` | str | — | `目录` | 可选 | regions.toc.title 缺省时的回退值 |
| `include_page_numbers` | bool | — | `true` | 可选 | 映射 TOC 域开关 |
| `right_align_page_numbers` | bool | — | `true` | 可选 | 同上 |
| `hyperlink` | bool | — | `true` | 可选 | 同上 |
| `levels.<1-4>.leader` | enum | `none`/`dots`/`dashes`/`line`/`heavy`/`middle_dot` | `dots` | 可选 | **偏差记录 C-7b**：SPEC_V2 §15 未列 `levels`；v0.3 `toc.levelN.{leader,page_number_tab}` 迁移需要，本 schema 增加为白名单字段 |
| `levels.<1-4>.page_number_tab` | Length | 缩进上下文 | None | 可选 | > 0；省略时取页面内容宽度（沿用 v0.3） |

目录本体是真实 TOC complex field（AGENTS.md §1.5），模板只控制域开关与
各级条目样式覆盖；条目、页码不落地为静态文本。

### 3.19 bibliography

| 字段 | 类型 | 枚举/单位 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- | --- |
| `provider` | str | `default` 或注册 provider | `default` | 可选 | Provider 可替换（R-011 退路） |
| `style_file` | Path | — | `citations/style.csl` | 可选 | 存在性 + 哈希对账（§1.1） |
| `locale` | BCP47 | — | `zh-CN` | 可选 | — |
| `heading_region` | region 键 | — | `bibliography` | 可选 | 必须存在于 `regions.order` |
| `paragraph_style` | StyleTokenRef | — | `bibliography` | 可选 | — |
| `hanging_indent` | Length | 缩进上下文 | `2em` | 可选 | 与样式重复定义按 D-1 诊断 |
| `line_spacing` | LineSpacing | — | `{type: single}` | 可选 | 同 §3.8 规则 |
| `sort` | enum | `style`/`appearance` | `style` | 可选 | `style` = 交给 CSL |
| `uncited` | enum | `exclude`/`include` | `exclude` | 可选 | — |
| `missing_field_policy` | enum | `warning`/`error`/`ignore` | `warning` | 可选 | — |
| `overrides_file` | Path | — | None | 可选 | 存在性检查 |
| `presentation` | enum | `inline`/`superscript` | `inline` | 可选 | **偏差记录 C-2**：v0.3 `citation.presentation` 在 SPEC_V2 §16 无落点；本 schema 收编于此，建议回写 SPEC_V2 |

`style.csl` 的来源、版本、哈希、许可证必须录入 `provenance.yaml`
（SPEC_V2 §16，R-024）。

### 3.20 layouts

`template.yaml` 中的引用节：

| 字段 | 类型 | 默认 | 必需性 | lint |
| --- | --- | --- | --- | --- |
| `layouts.<region_id>` | Path | 无 | 可选 | region 必须在词表内；文件必须存在且通过 Layout schema |

Layout 文件 schema（声明式，禁止任意表达式，SPEC_V2 §17）：

| 字段 | 类型 | 必需性 | 校验 |
| --- | --- | --- | --- |
| `id` | str | 必需 | 必须等于被引用的 region_id |
| `blocks` | list[Block] | 必需，非空 | Block 类型词表：`image`/`spacer`/`paragraph`/`table` |

Block 字段：

- `image`：`source`（Path，必需）、`width`（Length，父宽比例上下文，必需）、
  `alignment`（left/center/right，默认 center）。
- `spacer`：`height`（Length，绝对单位，必需，> 0）。
- `paragraph`：`style`（样式名或 token，必需）、`value`（str，可含占位符）、
  `keep_with_next`（bool，可选）。
- `table`：`style`（str，必需）、`rows`（list[list[str]]，必需，单元格可含
  占位符）、`widths`（list[Length]，可选，与列数一致）。

占位符语法：`${path}`、`${path|default:默认值}`、`${path|required}`、
`${path|format:date_cn|date_iso|upper|lower}`。`path` 白名单（v0.3
CoverField 超集）：`university.name`、`university.college`、`thesis.title`、
`thesis.title_en`、`thesis.major`、`thesis.degree`、`author.name`、
`author.student_id`、`advisor.name`、`advisor.title`、`dates.completed`、
`dates.defense`。白名单外 path、未注册 filter、或类似表达式语法
（`${a+b}`）→ `invalid-template`（error）。metadata 缺失且无 default/required
策略 → 构建期 `missing-metadata`（warning，段落按 `skip_if_empty` 等价语义
跳过；`required` 时 error）。

复杂度超出声明式能力时改用 shell.docx 锚点（SPEC_V2 §17 边界条款），
不允许继续扩张 block 类型为 Word 克隆语言（R-004 退路）。

### 3.21 provenance 引用（`provenance.yaml` schema）

`template.yaml` 不内嵌 provenance；文件按固定路径 `provenance.yaml` 解析。

| 字段 | 类型 | 必需性 | 校验 / lint |
| --- | --- | --- | --- |
| `school.name` | str | 必需 | 非空 |
| `school.official_document.title` | str | 必需 | 学校规范文件名 |
| `school.official_document.version` | str | 必需 | 学校规范版本（第三版本维，§9.1）；不透明字符串 |
| `school.official_document.issued_date` | Date | 可选 | — |
| `school.official_document.source_type` | enum | 必需 | `official-docx`/`official-pdf`/`webpage`/`manual` |
| `school.official_document.source_hash` | SHA256Ref | 条件必需 | source_type 为文件类（docx/pdf）时必需 |
| `school.official_document.source_url` | str | 可选 | 仅记录，不访问（离线原则） |
| `maintainers` | list[{name, contact}] | 必需，非空 | — |
| `licenses.template_code` | SPDX id | 必需 | — |
| `licenses.school_assets` | SPDX id 或 `restricted` | 必需 | `restricted` 时 LICENSES/ 必须含说明（R-024） |
| `licenses.citation_style` | SPDX id | 条件必需 | 含 `citations/style.csl` 时必需 |
| `licenses.fonts` | SPDX id | 条件必需 | `font_policy.embed_fonts: true` 时必需 |
| `review.last_verified` | Date | 必需 | — |
| `review.verified_with` | list[str] | 必需，非空 | 建议含 `compatibility.target_apps.primary` 对应应用（L4 warning 不含） |

缺失字段 → `provenance-incomplete`（error 于必需项，warning 于可选项的
建议补齐项）。SPEC_V2 §18「模板 pack 必须检测缺失 provenance」落实为：
目录形态 lint 与 `template pack` 均强制上述校验。

## 4. 样式 precedence 规则

版式信息有三个来源：reference.docx 样式、template.yaml 显式属性、渲染器
内置默认。SPIKE §1.2.3 实证：以 `Document(reference.docx)` 起建后，渲染器
`configure_styles()` 会无条件把 YAML 值写进同名样式（Normal 的
firstLineIndent 从 None 被改写为 480 twips）。v2 必须显式定义优先级，否则
reference.docx 的样式承诺不可信（SPIKE §5 Q1）。本章给出三方冲突时的确定性
规则（§4.1–§4.2）与 extends 继承的合并语义（§4.3）。

### 4.1 字段三分类（决策 D-1）

**决策 D-1（属性级 precedence）**：所有影响版式的属性按语义归入三类，
优先级确定且三类互不重叠：

| 类别 | 定义 | 权威来源 | 冲突处理 |
| --- | --- | --- | --- |
| A 结构语义类 | 编译器必须知道的语义：page 几何（§3.5）、sections 策略（§3.11）、numbering 策略（§3.12）、regions（§3.10）、toc 域开关（§3.18）、fields 策略（§3.16） | template.yaml 唯一权威 | reference.docx 中的对应值仅作漂移比对（§4.2 `template-reference-drift`，L3 warning），不生效 |
| B 样式覆盖白名单 | 本文件显式列出的少量版式字段：§3.8 body（`alignment`/`first_line_indent`/`line_spacing`/`spacing`/`widow_control`）、§3.9 headings（`page_break_before`/`keep_with_next`）、§3.18 `toc.levels`（`leader`/`page_number_tab`）、§3.19 bibliography（`hanging_indent`/`line_spacing`） | YAML 写了 → YAML 生效并回写样式（构建产物内）；未写 → reference.docx token 样式生效 | 生效时产生 §4.2 `yaml-overrides-style`（info）诊断 |
| C 纯样式类 | 字体、字号、颜色、加粗、边框等其余版式属性 | reference.docx 唯一权威 | template.yaml 不允许表达（`extra=forbid` 自然拒绝，§2.1） |

优先级总序：**B 类 YAML 显式值 > reference.docx 样式 > 渲染器内置默认**。
渲染器内置默认仅在三方均未提供值时兜底（如可选 token 未映射时的排版兜底）；
v2 渲染器**禁止**无条件改写 reference.docx 提供的样式——configure_styles
只允许写入 B 类 YAML 显式值，且只作用于内存副本（SPIKE §1.2.1 实证
`Document(path)` 就地编辑会覆盖模板本体，加载时必须先在内存/临时副本中
复制，模板包内文件只读）。

确定性要求：同一（template.yaml, reference.docx）输入下每个属性的有效值
唯一确定，与渲染器运行环境无关；B 类字段的逐属性来源落入 build manifest
（§4.2、§9.4）。

### 4.2 声明方式与诊断要求

- B 类字段在 YAML 中出现 → 构建期写入目标 token 样式（内存副本），并输出
  `yaml-overrides-style`（info）：字段路径、token、样式名、YAML 值、
  reference.docx 原值，全部落入 build manifest，保证可归因、可回查。
- A 类字段 YAML 值与 reference.docx sectPr 对应值不一致 →
  `template-reference-drift`（L3 warning，§3.5 已引用）；一致时静默。
  该诊断用于发现「学校下发的 docx 与文字规范不一致」的常见事故（R-025），
  不阻断构建。
- C 类属性出现在 YAML → `invalid-template`（L2 error，extra=forbid）。
- 渲染器不得把内置默认写回 reference.docx 文件；任何对样式部件的修改只
  发生在构建产物内（R-026 预防：旧模板不被静默改变）。
- B 类白名单的扩充只能通过 schema 演进（新增字段并更新本表）进行；渲染器
  不得为单个模板增加属性分支或学校特例（R-012 预防，CI 静态检查模板 ID）。

### 4.3 extends 继承合并语义（决策 D-2）

**决策 D-2（继承合并）**：

1. **合并字段白名单**：仅以下节参与继承合并：`word`（策略字段与
   `anchors`，文件路径字段见第 3 条）、`page`、`fonts`、`font_policy`、
   `styles`、`body`、`headings`、`regions`、`sections`、`numbering`、
   `figures`、`tables`、`equations`、`fields`、`cross_references`、`toc`、
   `bibliography`、`layouts`。header（§3.1）、`compatibility`（§3.2）、
   `extends` 自身、`provenance.yaml` **不继承**，每个包必须自带（学校
   来源与许可证不可传递，R-024）。
2. **合并算法**：map 深合并（子键覆盖父键，只覆盖显式出现的键）；list
   一律 replace，不 concat（SPEC_V2 §4.2）；标量子覆盖父。父模板先解析
   为 resolved 形态，再与子模板合并。
3. **文件引用**：`word.reference_docx`/`word.shell_docx`、
   `bibliography.style_file`、`layouts.*` 按「声明方包内解析」：子模板未
   声明时沿继承链定位父包内对应文件；声明了则必须解析到子包内文件。
   assets 不跨包并包——子包引用父包资源路径 → `missing-template-asset`
   （L1 error）。
4. **禁环与深度**：继承链必须无环；解析时检测到环 →
   `template-inheritance-cycle`（L2 error，报完整环路径）。链长 > 8 →
   `inheritance-depth-exceeded`（L2 error，防误配与解析失控）。
5. **版本与哈希锁定**：父模板按 §3.3 `version`（SemverRange）在本地模板
   根中解析满足条件的最高版本；`sha256` 提供时对父包内容哈希强校验
   （不一致 → `hash-mismatch`，error）。禁止网络加载（§3.3）。
6. **manifest 记录与可查性**：lint/build manifest 记录完整继承链（每级
   id、version、resolved sha256）与逐字段来源包；`thesisforge template
   inspect --resolved` 输出合并后的最终 template.yaml 及字段来源标注
   （SPEC_V2 §4.2）。

## 5. reference.docx 与 shell.docx 契约

两部件均为 OOXML OPC 包，共用安全策略（§5.5）。职责划分沿用 SPEC_V2
§4.3：reference.docx 承载 styles/theme/fontTable/page setup/header-footer/
numbering base/settings/default language；shell.docx 承载复杂前置页与投递
锚点。本章把 SPIKE 实证结论落成契约：标注「实证」的条目来自 SPIKE §1–§3，
标注「未实证」的为设计外推，实现前必须先补 spike 验证（R-005 预防：不支持
的特性报错，不做部分合并）。

### 5.1 reference.docx 契约

1. OpenXML 校验通过（L3 `invalid-word-asset`，error）；正文为空或仅含
   允许清理的占位段落；加载时占位段落被移除并记录（L3 info），含其他正文
   内容 → `reference-body-not-empty`（L3 warning）。
2. 必须包含 §3.7.1 全部必需 token 对应样式，缺失 → `missing-token-style`
   （error）；类型不匹配 → `style-type-mismatch`（error）（§3.7.2）。实证：
   python-docx 默认包不含 TF 样式，reference.docx 是样式的唯一来源
   （SPIKE §1.1）。
3. token 样式必须使用显式 `rFonts`，不得引用 theme 字体属性
   （`majorHAnsi`/`minorHAnsi` 等）→ L4 `theme-font-reference`（warning）。
   实证：全部 rFonts 显式时 theme 字体惰性，不构成阻塞（SPIKE §1.1）。
4. `docDefaults`/`latentStyles` 为包级单例（SPIKE §1.2.4）：合并场景只
   允许保留一份，归属见 §5.3/§5.4。
5. 消费方式：渲染器以 `Document(reference.docx)` 起建新文档时必须作用于
   副本（SPIKE §1.2.1 实证就地编辑风险）；`fontTable.xml`/`theme1.xml`
   等部件在 python-docx 中只暴露 blob，须经 `part.blob` 反序列化/回写
   （SPIKE §1.2.2）。
6. 被 §3.11 `header_footer.*` 引用的 header/footer 部件遵循 §5.2.4 命名
   约定。

### 5.2 shell.docx 契约与锚点协议

允许内容（SPEC_V2 §4.3）：封面、声明页、学校 Logo、预先设计的表格、
section breaks、content controls 或 bookmarks、正文/目录/参考文献插入锚点。

#### 5.2.1 锚点定义与唯一性校验

- 锚点以书签对（`w:bookmarkStart`/`w:bookmarkEnd`）承载，名称来自
  `word.anchors`（§3.4，默认 `tf_body`/`tf_toc`/`tf_bibliography`）。
  v2 以书签为规范实现；`w:sdt`（content control）锚点为保留扩展（未实证），
  检测到同名 sdt → L3 info，提示改用书签。
- `bookmarkStart` 必须位于所属段落 `pPr` 之后，书签必须成对（SPIKE
  §1.2.2、§3.4 实证）；不成对 → L3 `bookmark-unpaired`（error）。
- 每个锚点名在 shell.docx 中恰好出现一次：重复 → `anchor-duplicate`
  （L3 error）；存在未在 `word.anchors` 声明的 `tf_*` 书签 →
  `anchor-undeclared`（L3 warning）。
- 锚点段落本身应为空段落（允许带 `pPr`）；含内容 → L3 warning，投递时
  该内容随锚点段落一并移除（§5.2.3 第 5 条）。

#### 5.2.2 缺失锚点处理

- `body` 锚点缺失 → `missing-body-anchor`（error，**阻断**；SPEC_V2 §4.3，
  SPIKE §4.7 已实现为 SystemExit）。
- `toc`/`bibliography` 锚点缺失且论文启用对应 region → `anchor-fallback`
  （warning）：对应内容按 `regions.order` 顺序并入 body 槽投递，保证可
  构建；模板作者应在 README「已知限制」中说明。

#### 5.2.3 region → anchor 投递协议（决策 D-4）

**决策 D-4（分槽投递与锚点消费）**：

1. **偏差记录 C-8**：SPEC_V2 未定义编译产物与 shell 的对齐方式。按 SPIKE
   §4.3 建议，本 schema 增加契约：Compiler 必须输出 region 边界 manifest
   （各 region 在 compiled.docx 正文中的节点区间，region 键 ∈ §3.10 词表），
   PackageEditor 按 manifest 分槽投递；禁止「首个分节符之后全部导入
   tf_body」的近似（SPIKE §4.3 实证该近似导致前置内容错位、roman 重启
   重复）。
2. 投递映射：cover 等 shell 持有 region 的 compiled 对应节点丢弃；
   front_matter 内容 → shell 前置区（首个分节符之前）；`main`/
   `back_matter` → `body` 锚点；TOC 域 → `toc` 锚点；bibliography →
   `bibliography` 锚点。region 的 `<region>.anchor`（§3.10）可覆盖默认
   投递槽。
3. `toc` 锚点的投递物是真实 TOC complex field（含 cached result 与 dirty
   标记，§3.16/§3.18），不是静态目录文本（SPIKE §5 Q5 的回答；AGENTS.md
   §1.5）。
4. compiled.docx 的 final sectPr 必须显式丢弃（SPIKE §3.3 实证：不丢弃会
   以 compiled 正文节属性覆盖 shell 的 main section 设计）；导入内容中的
   内部 sectPr 保留原样（SPIKE §5 Q6 的回答：节属性在编译期已由 §3.11
   决定，合并期不重写）。
5. 锚点被消费后移除锚点段落及书签对（SPIKE §2.1 的选择，§3.4 实证书签
   必须成对清理）；保留锚点以支持二次合并/增量构建的需求见 OQ-4。
6. finalizer 与合并的顺序见 OQ-10（§3.16 已记录，本文建议「编译 → 合并
   → finalizer」）。

#### 5.2.4 header/footer 部件命名约定

§3.11 `header_footer.default/first/even` 的值解析为 `word/<值>.xml` 部件
（header 或 footer 类型）。模板作者必须为被 YAML 引用的部件起语义名
（如 `main_default.xml`；OPC 允许任意部件名）；机器名（`header2.xml`）
允许被 sectPr 内部引用，但不得出现在 YAML 中；值无法解析到部件 → L3
`unresolved-header-footer-part`（error，§3.11 已引用）。合并搬运产生的
重命名部件（§5.3）同样只对 sectPr 内部可见，不接受 YAML 引用。

### 5.3 合并搬运清单（PackageEditor carry-list）

采用 SPIKE §2.2 实证台账为规范。「实证」= SPIKE 已验证；「未实证」=
SPIKE 显式 `NotImplementedError` 拦截的路径，v2 实现前必须补实证。

| 对象 | 规则 | 来源 |
| --- | --- | --- |
| relationships（`r:id`/`r:embed`） | 导入节点引用的 rId 全部重映射，allocator 取 shell 现有最大 rId 编号 +1 递增（确定性，SPIKE §4.8）；目标部件复制进包 | SPIKE §2.2/§3.1 实证（双方同出 python-docx 默认包，rId 冲突是必然事件） |
| 部件名冲突 | 数字后缀递增重命名（header3.xml、image2.png…），rels `Target` 同步改写 | SPIKE §2.2/§3.2 实证 |
| styles | 按导入内容引用 + `basedOn`/`next`/`link` 闭包最小搬运；冲突策略见 D-3；`docDefaults`/`latentStyles` 保留 shell 不合并 | SPIKE §2.2 实证 |
| numbering.xml | shell 未引用 numId → compiled numbering.xml 整体替换；shell 已引用 → 双侧 numId/abstractNumId 确定性重映射（compiled 侧平移至 max+1 起）后合并 | 前者 SPIKE §2.2 实证；后者未实证（SPIKE §3.7），OQ-3 |
| footnotes part | shell 无 footnotes.xml → 整体搬运 + 登记 relationship + Content Types Override，`w:id` 不重映射（分隔符/续注 id −1/0 保留）；shell 已有 → `w:id` 双侧重映射后合并 | 前者 SPIKE §2.2 实证；后者未实证（SPIKE §3.7），OQ-3 |
| `[Content_Types].xml` | header/footer/footnotes 等部件从 compiled CT 复制 Override 并改写为新部件名；扩展名级 Default 不复制 | SPIKE §2.2 实证 |
| 部件级 rels 递归 | 被搬运部件内部再引用资源（如 header/footer 内嵌图片）需递归搬运并重映射部件内部 `r:id`；Alpha 拦截报错 `unsupported-shell-feature`（error），支持范围见 OQ-2 | SPIKE §3.6 未实证 |
| settings.xml / theme1.xml / fontTable.xml / docProps | 不合并，归属见 §5.4（D-5） | SPIKE §2.2/§4.6 |

**决策 D-3（样式冲突策略）**：冲突样式先按 style token 对齐（§3.7 token
→ 样式名为合并键），之后 **shell-wins**：保留 shell 同名定义，compiled
定义不搬运。token 无映射的冲突（导入内容引用了 shell 同名但无 token 对应
的样式，如 Normal、Heading1）→ L3 `style-conflict-unmapped`（warning，
合并继续，台账完整记录）。`compiled-wins` 仅作为 lint 诊断比对模式
（`template lint --merge-simulation`）输出差异，不作为合并行为。依据：
SPIKE §4.4 建议；SPIKE §2.3 实证 compiled-wins 会回流污染 shell 前置页
（Normal firstLineIndent=480 导致封面占位段落出现首行缩进）。shell-wins
下前置页样式治理的粒度问题见 OQ-5。

合并输出必须包含台账（ledger）并落入 build manifest：rId 映射、部件重命名、
样式冲突与策略、未搬运项及原因（SPIKE §4.2；格式参照
`spikes/phase0/docx-template/output/merge-report.json`）。合并后校验闭环：
OpenXML 校验 + L3 锚点/样式/relationship 检查 + 目标应用冒烟（SPIKE §4.7）。
allocator 与重命名规则保证相同输入产出相同合并结果（ZIP 时间戳除外，
SPIKE §4.8；R-019）。

### 5.4 settings/theme/fontTable 归属与白名单（决策 D-5）

**决策 D-5（包级单例部件归属）**（SPIKE §4.6 建议、§5 Q3 的回答）：

- `settings.xml`：shell.docx 持有（无 shell 时 reference.docx 持有）。
  编译产物的 settings 不拷贝；仅以下白名单字段由 PackageEditor 按
  template.yaml 语义在合并后统一写入：`evenAndOddHeaders`（任一 section
  声明 `header_footer.even` 时置位，§3.11）、`updateFields`
  （`fields.update_on_open`，§3.16）、`mirrorMargins`
  （`page.mirror_margins`，§3.5）。白名单外字段以持有方为准。
- `theme1.xml`：shell 持有（无 shell 时 reference 持有），不合并；token
  样式显式 rFonts 前提下 theme 字体惰性（§5.1 第 3 条、SPIKE §1.1）。
- `fontTable.xml`：reference.docx 持有基线，合并不替换。
- `docProps`：保留 shell（SPIKE §2.2 实证不合并）；论文 metadata（标题/
  作者等）写入合并产物 docProps 的机制未定 → OQ-12。

### 5.5 安全策略（R-020）

检测在两个层面强制执行（SPIKE §5 Q9 的回答）：L1 lint 尽早失败；
PackageEditor 合并时兜底拦截（SPIKE 已在合并时拦截外部 rel）。

| 威胁 | 检测方法 | 处置 |
| --- | --- | --- |
| 宏 | 包内存在 `vbaProject.bin`；或主文档 Content-Type 为 macroEnabled 系列 | `macro-detected`（error，拒绝加载；`macro_policy` 仅允许 `forbid`，§3.4） |
| 外部关系 | 遍历全部 `.rels`，`TargetMode="External"` 逐条比对 `external_relationships` 策略与白名单（§3.4） | `forbid` → `external-relationship`（error）；`allowlist` → 白名单外 error，命中 info 并落台账 |
| OLE/嵌入对象 | 存在 `word/embeddings/`、`word/activeX/` 部件，或 `w:object`/`w:OLEObject` 元素 | `ole-detected`（error） |
| 外部字段代码 | 字段指令含 `DDE`/`DDEAUTO`/`INCLUDETEXT`，或 `INCLUDEPICTURE` 指向外部 Target | error（同外部关系策略） |
| SVG 外部引用 | SVG 资产含 `script`/`foreignObject`/外部 `href` | error（§1.1 注） |
| 路径攻击 | §1.3 全部规则 | `package-path-unsafe`（error） |

不提供「忽略安全警告继续」选项（R-020 退路）。

## 6. Lint 分层 L1–L5 实现要点

对应 SPEC_V2 §19，逐层落到可实现的检查。执行模型：每层可独立运行
（`template lint --level Ln`），默认 L1→L5 顺序执行；任一层出现 error 时
更高层跳过（避免在坏资产上做语义检查产生噪音）；全部检查离线、确定性
（R-020；字体探测属 `doctor` 职责，不在 lint 内）。所有问题输出结构化
`ValidationIssue`（码、级别、字段路径/部件路径、消息；AGENTS.md §4），
禁止散落 `print()`。各码默认级别见下表；`error` 阻断加载/打包/构建。

### 6.1 L1 Package

| 检查 | 码 | 级别 | 实现要点 |
| --- | --- | --- | --- |
| 必需文件存在 | `missing-package-file` | error | §1.1 必需性列逐条核对 |
| 路径安全 | `package-path-unsafe` | error | §1.3 五条规则，含符号链接解引用检查 |
| 哈希对账 | `hash-mismatch` | error | style.csl ↔ provenance（§1.1）；.tftpl entries ↔ manifest（§7.4） |
| 宏/外部关系/OLE | §5.5 各码 | error | 纯 ZIP 条目/Content-Types/rels 扫描，不解析 XML 正文 |
| 隐藏文件/平台垃圾 | `package-path-conflict` 等 | warning | §1.2；打包时剔除重建 |
| header 前置解析 | §3.1 各码 | error | 只解析 header 与 `schema_version`（§8.3），结果供后续层使用 |
| CHANGELOG 版本 | `changelog-version-mismatch` | error（目录形态开发期 warning） | 顶部版本号 ↔ `header.version`（§1.1） |
| README/已知限制 | `readme-missing` | error | §1.1 |
| provenance 存在与完整 | `provenance-missing`/`provenance-incomplete` | error / 部分 warning | §1.1、§3.21 |

### 6.2 L2 Schema

| 检查 | 码 | 级别 | 实现要点 |
| --- | --- | --- | --- |
| YAML 语法/编码 | `invalid-template` | error | UTF-8、safe_load |
| 模型校验 | `invalid-template` | error | `extra=forbid`、类型、枚举、必需性；错误保留完整字段路径（§2.1，沿用 v0.3 §12） |
| 单位解析 | `invalid-template` | error | §2.2 词法算法 + §2.3 上下文矩阵（allowed_units/positive） |
| SemverRange 解析 | `invalid-template` | error | §2.4 |
| YAML 内交叉引用 | 各节定义码 | error | token 引用（§3.8/§3.9/§3.13–3.15/§3.19）、region→section（§3.10）、layout 引用与占位符白名单（§3.20）、pattern 占位符词表（§3.12.4） |
| extends 解析 | `missing-template`/`unsatisfied-parent-version`/`hash-mismatch`/`template-inheritance-cycle`/`inheritance-depth-exceeded` | error | §4.3 算法；本地模板根解析，禁止网络 |
| anchors 声明 | `invalid-template` | error | 键词表与三键值互异（§3.4） |

### 6.3 L3 Word assets

| 检查 | 码 | 级别 | 实现要点 |
| --- | --- | --- | --- |
| DOCX OpenXML 校验 | `invalid-word-asset` | error | 与 `qa/tools/openxml_validate.py` 同级检查 |
| token 样式存在/类型 | `missing-token-style`/`style-type-mismatch` | error | styles.xml 按主名 + 别名（§3.7.3）解析；命中别名另报 info |
| 样式引用闭包 | `invalid-template` | error | `basedOn`/`next`/`link` 指向必须存在（§3.7.2） |
| 锚点协议 | §5.2 各码 | error/warning | 书签配对、唯一性、body 必需 |
| relationships 完整 | `invalid-word-asset` | error | 每个 `r:id` 有 rel、Target 部件存在 |
| header/footer 部件解析 | `unresolved-header-footer-part` | error | §5.2.4 命名约定 |
| shell 节策略比对 | `section-policy-mismatch` | warning | shell sectPr 与 §3.11 声明比对（页码格式/重启/页眉页脚引用） |
| A 类漂移比对 | `template-reference-drift` | warning | §4.2 |
| sectPr 子元素顺序 | `invalid-word-asset` | error | `pgNumType` 在 `cols`/`docGrid` 之前（SPIKE §3.5） |
| numbering/footnotes id 空间 | `numbering-id-conflict` | error | 双侧占用检测（§5.3）；OQ-3 落实前按不支持报错 |
| theme 字体引用 | `theme-font-reference` | warning | §5.1 第 3 条 |

### 6.4 L4 Semantic

| 检查 | 码 | 级别 | 实现要点 |
| --- | --- | --- | --- |
| required region 有 section 策略 | `numbering-source-missing` | error | region→section 解析（§3.10 默认映射）后策略存在 |
| 条件必需 token | `missing-template-style` | error | 启用 figures/tables/equations 时的 caption/equation token（§3.7.1） |
| numbering source 存在 | `numbering-source-missing` | error | §3.12.1 指向的标题级别存在 |
| citation style 存在/哈希 | `missing-template-asset`/`hash-mismatch` | error | §3.19/§1.1 |
| 矛盾属性 | `invalid-template` | error | `first_line_indent` 与 `hanging_indent` 同正（§2.3）；`page_number.display: false` 带 format/restart（§3.11）；`numbering.enabled: false` 带 pattern（§3.9） |
| outline level 一致 | `outline-level-mismatch` | warning | heading token 样式 outline level ↔ 级别（§3.7.2） |
| body 字号绝对 | `non-absolute-body-size` | error | §2.2 em 解析基线 |
| 兼容矩阵标注 | `review-incomplete` | warning | `review.verified_with` 含 primary 应用（§3.21）；`footnote_restart` 等能力需目标应用支持（§3.11） |
| 不生效配置 | `ineffective-config` | warning | `toc.levels` 键 > depth（§3.18）；cover/toc 类 region 开启 heading_numbering（§3.10） |
| 能力标记 | `unsupported-capability` | warning | `figures.placement: floating`（§3.13）等 v2 未保证能力 |

### 6.5 L5 Fixture

| 检查 | 码 | 级别 | 实现要点 |
| --- | --- | --- | --- |
| minimal fixture 构建 | `fixture-build-failed` | error | 零 error 构建（§1.1） |
| full/edge fixture 构建 | `fixture-build-failed` | error（存在时） | 覆盖模板声明的全部 region 与对象类型（§1.1） |
| expected XML 断言 | `expected-xml-mismatch` | error | 对构建产物执行 XPath 断言集（schema 见下） |
| 产物 OpenXML 校验 | `invalid-word-asset` | error | 构建产物复用 §6.3 工具链 |
| 视觉基线 | `visual-baseline-drift` | warning | 仅相对回归，必须标注渲染引擎（R-028）；权威引擎与容差未定 → OQ-8 |

**偏差记录 C-9**：SPEC_V2 §19 只列 L5 检查项，未定义
`expected/manifest.json` 结构。本 schema 定义：

```json
{
  "version": 1,
  "builds": [
    {"fixture": "fixtures/minimal", "output": "minimal.docx"}
  ],
  "assertions": [
    {
      "build": "fixtures/minimal",
      "part": "word/document.xml",
      "xpath": "//w:p[w:pStyle/@w:val='TFHeading1']",
      "expect": "count >= 1"
    }
  ],
  "visual": [
    {
      "build": "fixtures/full",
      "engine": "word-16.x-windows",
      "image": "expected/visual/full-p1.png",
      "page": 1,
      "tolerance": "exact"
    }
  ]
}
```

| 字段 | 类型 | 必需性 | 校验 |
| --- | --- | --- | --- |
| `version` | int，常量 `1` | 必需 | 其他值 → `invalid-template`（error） |
| `builds[]` | {fixture, output} | 必需，非空 | fixture 必须存在于包内 |
| `assertions[]` | {build, part, xpath, expect} | 可选 | `expect` 为受限表达式：`count (=,!=,>=,<=,>,<) int`、`exists`、`not-exists`、`text = "..."`；禁止任意表达式求值（与 §3.20 同一原则，R-004 退路） |
| `visual[]` | {build, engine, image, page, tolerance} | 可选 | `engine` 必填（R-028）；`tolerance` ∈ `exact`/`phash-N`/`skip` |

## 7. `.tftpl` 打包格式

`.tftpl` 是受约束的 ZIP：目录形态（§1）的确定性快照 + `manifest.json`
（SPEC_V2 §21）。命令：

```bash
thesisforge template pack ./template -o dist/example-university-1.0.0.tftpl
thesisforge template verify dist/example-university-1.0.0.tftpl
```

### 7.1 manifest.json 结构（偏差记录 C-10）

**偏差记录 C-10**：SPEC_V2 §21 列出内容项但未定义字段级结构。本 schema
定义 `manifest.json`（打包产物根，§1.2 保留路径）：

| 字段 | 类型 | 必需性 | 校验 / 说明 |
| --- | --- | --- | --- |
| `manifest_version` | int，常量 `1` | 必需 | 其他值 → `unsupported-manifest-version`（error） |
| `generator` | {name, version} | 必需 | name 为 `thesisforge`；version 为打包宿主版本 |
| `template` | {id, version, schema_version, language} | 必需 | 与 template.yaml header 一致，不一致 → `manifest-mismatch`（error） |
| `compatibility` | §3.2 对象复制 | 必需 | verify 时先于此检查宿主（§3.2） |
| `entries` | list[{path, sha256, size}] | 必需 | **确定性顺序**：按 path 的 UTF-8 字节序字典序；sha256 为 `SHA256Ref`（§2.1）；覆盖包内除 `manifest.json`/`signature.json` 外全部文件 |
| `inheritance` | list[{id, version, sha256}] | 条件必需 | 模板声明 `extends` 时记录打包时解析的完整继承链（§4.3 第 6 条） |
| `provenance_hash` | SHA256Ref | 必需 | provenance.yaml 内容哈希 |
| `sbom` | {path, sha256} | 可选 | 指向 `LICENSES/SBOM.spdx.json`（§1.1，R-024） |
| `signature` | {algorithm, path} | 可选 | §7.3 |

### 7.2 确定性打包（决策 D-6）

**决策 D-6（确定性快照）**：相同目录输入产出字节级相同的 `.tftpl`
（R-019）：

1. entry 顺序：`manifest.json` 居首，其余按 path 的 UTF-8 字节序字典序；
2. ZIP entry 时间戳固定为 `1980-01-01T00:00:00`（DOS 纪元），不取文件
   mtime；
3. 压缩方式固定 DEFLATE level 9；文件名 UTF-8（general purpose bit 11
   置位）；
4. 剔除项：§1.2 隐藏文件、`__MACOSX/`、`.DS_Store`、目录形态下误置的根
   `manifest.json`（剔除重建）；
5. `pack` 前必须通过 L1–L3，失败不产出包。

### 7.3 签名（可选）

- 签名文件 `signature.json`：{algorithm, public_key_id, signed_hash}，
  `signed_hash` 为 `manifest.json` 规范字节（UTF-8、无尾部空白）的哈希；
  算法词表首版仅 `ed25519`。
- 未签名不是错误：`verify` 输出 info；签名存在但校验失败 →
  `signature-invalid`（error）。
- 信任模型（密钥分发、撤销、模板市场集成）未定 → OQ-6。

### 7.4 解包防护（R-020）

「sandbox extraction」落实为：

1. 解压目标为新建临时目录，禁止就地覆盖；
2. 逐 entry 执行 §1.3 路径校验（Zip Slip：`..` 段、绝对路径、盘符、
   反斜杠、符号链接 entry 一律拒绝，`package-path-unsafe`，error）；
3. 解压炸弹：单文件解压后 > 64 MB 或总量 > 512 MB → error（§1.3 默认
   阈值）；压缩率 > 100:1 且压缩前 > 1 MB 的 entry 先流式计数解压，超限
   即中止；
4. 先读 `manifest.json` 校验 `manifest_version` 与 `compatibility`，再逐
   entry 对账 `entries` 哈希（`hash-mismatch`，error）；
5. `verify` = 上述防护 + L1–L3 全量 + 签名检查。

## 8. v0.3 → v2 迁移设计

对象：`src/thesis_forge/templates/model.py`（v0.3 单 YAML）+
`docs/TEMPLATE_SPEC.md`。原则：迁移必须显式（R-026），自动映射 + 人工核对
台账，不静默解释旧模板。

### 8.1 字段映射表

v0.3 字段 → v2 落点。「→ reference.docx」表示由迁移工具编程注入样式部件
（路线同 SPIKE 路线① `build_reference.py`）；「人工」表示工具无法决定，
台账列为 manual-required。

| v0.3 字段 | v2 落点 | 说明 |
| --- | --- | --- |
| `id` / `name` | `header.id` / `header.name` | id 需符合 §3.1 正则，不符合时工具改写并记录 |
| `year` | 无直接落点 | 建议人工录入 `provenance.yaml` `school.official_document.version`；工具产 warning |
| `page.size`/`orientation` | `page.size`/`orientation` | 直迁 |
| `page.margin.top`/`bottom` | `page.margin.top`/`bottom` | 直迁 |
| `page.margin.left`/`right` | `page.margin.inner`/`outer` + `mirror_margins: false` | 语义映射：v0.3 无镜像边距；`false` 时 `inner≡left`、`outer≡right`（§3.5） |
| `page.header_distance`/`footer_distance`/`document_grid` | §3.5 同名 | 直迁 |
| `cover.items[]`（field/text/prefix/suffix/skip_if_empty/style） | `layouts/cover.yaml` blocks 或 shell.docx | 占位符 path 白名单兼容（§3.20 为 CoverField 超集，另含 `dates.defense`）；prefix/suffix 拼入 paragraph `value` 字面量；item 级 `style`（ParagraphStyleSpec）无 YAML 落点 → reference.docx 封面样式 + 人工核对 |
| `list.ordered`/`unordered`（levels/marker/prefix/suffix/缩进） | reference.docx numbering base + 列表样式 | **偏差记录 C-11**：SPEC_V2 无 lists 节；v2 由 reference.docx numbering base 承载，工具生成后人工核对，建议回写 SPEC_V2 |
| `body.*`（font/size/alignment/first_line_indent/line_spacing/spacing/widow_control 等） | 白名单字段 → §3.8 `body`；font/size/color/bold 等 → reference.docx `body` token 样式 | 按 §4.1 三分类自动拆分 |
| `heading.level1–3.*` | 白名单（page_break_before/keep_with_next）→ §3.9；其余 → reference.docx `TF Heading N` 样式 | v0.3 无级别 4；v2 级别 4 默认关闭编号（§3.9） |
| `semantic_styles.*`（abstract/acknowledgements/achievements 的 title/body/keywords） | reference.docx 对应样式 + `regions.<region>.title` | v2 YAML 不承载纯样式（§4.1 C 类） |
| `toc.title`、`toc.level1–3`（leader/page_number_tab/缩进与其余样式） | `toc.title` → `regions.toc.title`；`levels.<n>.leader`/`page_number_tab` → §3.18；其余样式 → reference.docx TOC N 样式 | §3.18 C-7b 已记录 |
| `bibliography.title`/`entry` | `regions.bibliography.title`；`paragraph_style` + reference.docx | §3.19 |
| `figure.numbering`（mode/separator） | `numbering.figure.scope`/`separator`；`mode: none` → `enabled: false` | §3.12.2 C-1b |
| `figure.caption`（position/prefix/font/size/alignment） | `figures.caption.position` + `numbering.figure.caption_prefix`；font/size/alignment → reference.docx `caption_figure` 样式 | — |
| `figure.default_width` | `figures.default_width` | §3.13 C-1a |
| `table.style`（three_line/grid/plain） | `tables.default_style` + `tables.styles.<name>` | grid/plain 展开为自定义样式键（§3.14 允许扩展） |
| `table.three_line.*` | `tables.styles.three_line.borders.top`/`header_bottom`/`bottom` | 直迁 |
| `table.numbering`/`caption` | 同 figure 对应规则 | — |
| `equation.numbering`/`alignment` | §3.12.3 / §3.15 `equations.alignment` | — |
| `sections.<cover/front_matter/main>.start` | §3.11 `sections.*.start` | 直迁；v2 新增 `back_matter` 取默认 |
| `sections.*.page_number.format`/`restart` | `page_number.display`/`format`/`restart` | `format: none` → `display: false`（§3.11） |
| `sections.*.header`/`footer`（enabled/text/different_first_page/default/first/even 变体及 text/style/bottom_border/page_number 排版） | 部件化：工具生成 reference.docx（或 shell.docx）header/footer 部件 + §3.11 `header_footer.default`/`first`/`even` 引用；`different_first_page: true` → `title_page: true` + `first` 部件 | **偏差记录 C-12**：SPEC_V2 §10 只列 first/even/default 能力，内容部件化迁移为本 schema 补充；文字/边框/页码排版进部件（§3.11，R-004），生成后人工核对 |
| `sections.*.header/footer.*.page_number`（PageNumberDisplaySpec 前后缀、共几页等） | 部件内 PAGE/NUMPAGES 域排版 | 不由 YAML 表达（§3.11 说明）；工具生成真实域 + cached result（AGENTS.md §1.5） |
| `citation.style` | `bibliography.style_file` + `citations/style.csl` | 工具按名解析已注册 CSL；未知名 → 人工 |
| `citation.presentation` | `bibliography.presentation` | §3.19 C-2 |

### 8.2 `template migrate` 命令行为（决策 D-7）

**决策 D-7（迁移行为）**：

```bash
thesisforge template migrate legacy-template.yaml -o ./migrated-package
```

1. 输入 v0.3 单 YAML，输出**目录形态**包骨架：`template.yaml`（可自动
   映射字段，`schema_version: 2`）+ `reference.docx`（样式/页眉页脚由
   v0.3 字段编程注入，路线同 SPIKE 路线①）+ `provenance.yaml` 骨架
   （必填项留空并标注 TODO）+ `README.md` 骨架；fixtures 不生成，台账
   提示为 Beta 前人工补齐项（§1.1）。
2. 输出逐字段台账（`migration-report.json` + 终端摘要），每条三态：
   `migrated`（含落点路径）、`manual-required`（含原因与建议操作）、
   `dropped`（含理由；仅允许无语义损失的字段）。
3. 目标目录非空时拒绝覆盖（`--force` 显式开启）；迁移幂等，可重复执行。
4. 迁移产物立即跑 L1–L3：出现 error 时命令非零退出，台账列出剩余人工
   步骤。迁移不承诺「零人工」，承诺「无静默失真」（R-026）。

### 8.3 schema_version 拒绝策略

加载顺序：先读 header `schema_version`（L1 前置解析，§6.1），再决定
解释器。

| 情况 | 行为 |
| --- | --- |
| `schema_version: 2` | 按本文件加载 |
| 缺失或为低于 2 的值 | `unsupported-schema-version`（error）：不尝试按 v2 解释（R-026 退路），错误信息附 `template migrate` 指引；v0.3 加载器独立存在，v2 管线不 fallback |
| 大于宿主支持版本 | `unsupported-schema-version`（error）：提示升级 ThesisForge；`compatibility.thesisforge` 二次确认（§3.2） |

「旧模板不能被静默按新 schema 解释」（SPEC_V2 §20）落实为：v2 加载器对
非 `2` 一律 error，不存在「尽力解析」模式。

## 9. 版本三维与升级规则

### 9.1 三个版本维度（SPEC_V2 §20 细化）

| 维度 | 载体 | 变化含义 | 检查点 |
| --- | --- | --- | --- |
| `schema_version` | template.yaml header（常量 2） | 包结构/解释器版本 | 加载时（§8.3）；打包写入 manifest（§7.1） |
| `version`（Semver） | template.yaml header | 模板自身语义版本 | CHANGELOG 对账（L1）；extends 解析（§4.3）；缓存键与 build manifest（§9.4） |
| 学校规范版本 | `provenance.yaml` `school.official_document.version`（不透明字符串，§3.21） | 学校依据文件改版 | 不自动比较；变化时必须人工更新 `review.last_verified` 并重跑 L5；lint 检查 `last_verified` 不早于 `issued_date`（`provenance-stale`，warning） |

三维独立演进：schema 升级不要求学校规范变化；学校规范改版通常触发模板
minor/major，但不强制改 schema。

### 9.2 升级规则与可检查点

SPEC_V2 §20 规则落为可执行检查：

- **patch**（修复不改变预期版式）：同 fixtures 构建的 expected XML 断言
  应全部维持；断言变化而 version 仅 bump patch → L5 `suspect-version-bump`
  （warning）。
- **minor**（新增可选能力或学校规则）：只允许新增可选字段、region、
  样式；移除或改义字段属 major。无法完全自动判定，纳入 status 流转的
  review 清单（§9.3）。
- **major**（改变版式、字段或兼容行为）：必须更新 CHANGELOG 的迁移说明；
  被 `extends` 引用时对子模板的影响由 §4.3 版本区间与 `sha256` 锁定
  控制。
- **schema migration 必须显式**：见 §8.2/§8.3。
- **compatibility 检查**：加载与 verify 时宿主版本不满足
  `compatibility.thesisforge` → `incompatible-thesisforge`（error，§3.2）。

### 9.3 status 生命周期语义

| status | 语义 | 机器行为 |
| --- | --- | --- |
| `draft` | 开发中，不进入分发 | `template pack` 拒绝（`template-not-releasable`，error，`--allow-draft` 除外）；extends 解析到 draft → warning |
| `active` | 可依赖，升级遵守 §9.2 | 正常 |
| `deprecated` | 可用但不再演进 | 加载/extends 解析 → `template-deprecated`（warning，附 README 替代指引）；`pack` 允许 |
| `archived` | 历史留存 | 新构建/extends 解析 → `template-archived`（warning；构建允许，保证旧论文可复现，R-026）；`pack` 拒绝 |

### 9.4 resolved template 记录

每次构建的 build manifest 必须记录：三维版本、继承链与各级 sha256
（§4.3 第 6 条）、合并台账（§5.3）、B 类覆盖诊断（§4.2）、resolved
template 快照（`template inspect --resolved` 等价内容；SPEC_V2 §20
「build manifest 记录 resolved template」）。快照是构建归因的唯一权威，
后续模板升级不影响已构建论文的归因（R-019/R-026）。

## 10. 开放问题清单

### 10.1 偏差记录汇总

| 编号 | 位置 | 内容 | 处置建议 |
| --- | --- | --- | --- |
| C-1a | §3.13 | `figures.default_width` SPEC_V2 §12 无，v0.3 迁移需要而增加 | 回写 SPEC_V2 |
| C-1b | §3.12.2 | `numbering.enabled`（关闭编号）SPEC_V2 §11 无 | 回写 SPEC_V2 |
| C-2 | §3.19 | v0.3 `citation.presentation` 收编于 bibliography | 回写 SPEC_V2 |
| C-4 | §3.13 | `source_note.enabled: optional` 更名 `policy` | 回写 SPEC_V2 |
| C-5 | §3.11 | `new_page` 为规范值，`next_page` 作别名 | 回写 SPEC_V2 |
| C-6 | §3.7.3 | `styles/aliases.yaml` 结构补充定义 | 回写 SPEC_V2 |
| C-7a | §3.15 | `image_fallback` 增加 `explicit` 语义 | 回写 SPEC_V2 |
| C-7b | §3.18 | `toc.levels` 白名单字段补充 | 回写 SPEC_V2 |
| C-8 | §5.2.3 | Compiler 输出 region 边界 manifest（SPIKE §4.3 建议） | 回写 SPEC_V2 §4 |
| C-9 | §6.5 | `expected/manifest.json` 结构定义 | 回写 SPEC_V2 §19 |
| C-10 | §7.1 | `.tftpl` `manifest.json` 字段级结构 | 回写 SPEC_V2 §21 |
| C-11 | §8.1 | v0.3 `list.*` 落点为 numbering base，SPEC_V2 无 lists 节 | SPEC_V2 增补或显式声明列表几何不由 YAML 表达 |
| C-12 | §8.1 | v0.3 页眉页脚内容字段部件化迁移 | 回写 SPEC_V2 §10 |

### 10.2 开放问题

| 编号 | 位置 | 问题 | 状态 / 下一步 |
| --- | --- | --- | --- |
| OQ-1 | §3.15 | 公式编号布局（tab_stop/borderless_table/custom_paragraph）默认值暂定 | 待公式 spike（SPEC_V2 §14 要求 Phase 0 实测固定） |
| OQ-2 | §5.3 | 部件级 rels 递归搬运（header/footer 内嵌图片）支持范围 | Alpha 拦截报错；Beta 前补 spike（SPIKE §3.6、§5 Q8） |
| OQ-3 | §5.3 | numbering/footnotes 双侧 id 占用的重映射合并未实证 | 实现前补 spike；落实前 L3 按不支持报错（SPIKE §3.7、§5 Q4） |
| OQ-4 | §5.2.3 | 锚点消费即移除，二次合并/增量构建是否需要保留锚点 | 与增量构建需求一并评估（SPIKE §5 Q7） |
| OQ-5 | §5.3 | shell-wins 下前置页样式回流治理粒度（token 映射细化 vs 白名单） | 随第一个真实学校 shell 模板复盘（SPIKE §2.3） |
| OQ-6 | §7.3 | `.tftpl` 签名信任模型（密钥分发/撤销/模板市场集成） | 分发渠道明确后定 |
| OQ-7 | §8.2 | 半自动迁移（cover/list/页眉部件）的人工核对流程与验收标准 | 首个 v0.3 真实模板迁移复盘后固化 |
| OQ-8 | §6.5 | 视觉基线权威引擎与容差标准 | 与 R-028 处理一并定 |
| OQ-9 | §2.2 | 嵌套上下文（表格单元格内 %）的 base 未定义 | schema 暂禁止嵌套 %（L2 error）；表格模型定型后评估 |
| OQ-10 | §3.16 | finalizer 与 shell 合并的顺序 | 建议「编译 → 合并 → finalizer」；待 finalizer spike 验证 |
| OQ-11 | §3.10 | region_id 词表扩展机制 | 学校模板实践后评估 |
| OQ-12 | §5.4 | 论文 metadata 写入合并产物 docProps 的机制（合并期不搬运 compiled docProps） | 与 finalizer/metadata 设计一并定 |

## 附录 A 决策摘要

| 编号 | 位置 | 决策 | 依据 |
| --- | --- | --- | --- |
| D-1 | §4.1 | 属性级 precedence：B 类 YAML 显式值 > reference.docx 样式 > 渲染器内置默认；字段三分类互不重叠；渲染器禁止无条件改写、禁止就地编辑模板文件 | SPIKE §1.2.3 实证 configure_styles 改写；SPIKE §5 Q1 |
| D-2 | §4.3 | extends 合并：白名单节 map 深合并、list 一律 replace、禁环、链长 ≤ 8、manifest 记录继承链与哈希、`template inspect --resolved` 可查 | SPEC_V2 §4.2 |
| D-3 | §5.3 | 样式冲突按 token 对齐后 shell-wins；无映射冲突 warning 并记录台账；compiled-wins 仅作诊断比对模式 | SPIKE §4.4 建议、§2.3 回流实证 |
| D-4 | §5.2.3 | region manifest 分槽投递；tf_toc 投递真实 TOC 域；丢弃 compiled final sectPr、保留内部 sectPr；锚点消费即移除 | SPIKE §4.3、§2.1、§3.3，§5 Q5–Q7 |
| D-5 | §5.4 | settings/theme 归 shell，fontTable 归 reference；settings 白名单（evenAndOddHeaders/updateFields/mirrorMargins）由 YAML 语义写入而非 compiled 拷贝 | SPIKE §4.6 建议、§5 Q3 |
| D-6 | §7.2 | `.tftpl` 确定性打包：entry 排序与时间戳固定、压缩参数固定、pack 前置 L1–L3 | SPEC_V2 §21，R-019 |
| D-7 | §8.2 | migrate 三态台账 + 产物过 L1–L3；`schema_version` 非 2 一律拒绝，不静默解释 | SPEC_V2 §20，R-026 |
