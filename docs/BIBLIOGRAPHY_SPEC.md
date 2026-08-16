# ThesisForge Bibliography Spec v0.1

ThesisForge V1 的参考文献子系统是本地、确定性、renderer-neutral 的：

```text
Local BibTeX
    ↓
BibliographyDatabase
    ↓
Validation / CitationFormatter
    ↓
CitationRun.text + BibliographyInstruction
    ↓
DOCX editable text
```

核心 `inspect`、`validate` 和 `build` 不访问网络，也不要求 `citeproc-py`。

## Front Matter

```yaml
render:
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
```

`bibliography` 相对 Markdown 文件目录解析，并服从
`ValidationContext.resource_roots` 的本地资源边界。路径越界返回
`resource-path-escape`，文件不存在返回 `missing-bibliography`。

`citation_style` 选择引用样式（ADR-0004，修复 D-07：该配置真正生效）。文档
Front Matter 优先，缺省时回落到模板的 `citation.style`。取值大小写不敏感，
`GB-T-7714-2025`、`gbt7714`、`gbt7714-2025`、`gbt7714-2025-numeric` 均归一化
为内置样式 id `GB-T-7714-2025`。无法识别的样式不会静默回落默认引擎：
Validator 返回结构化 `unsupported-citation-style`（severity=error，details 含
`supported_styles`），直接调用 Compiler 则抛 `UnsupportedCitationStyleError`。

## CitationProvider

bibliography 子系统对外只暴露 `CitationProvider` 抽象（输入 records +
ordinals/locator，输出正文引用标记与文后条目文本），不暴露 provider 专有对象。
`resolve_citation_provider(style)` 按样式名选择 provider；V1 只注册内建手写
GB/T 7714-2025 provider（`BuiltinGbt7714Provider`，离线、确定性、无运行时
依赖）。外部 provider（如 pandoc citeproc）将来按同一协议接入：子进程调用、
CSL JSON 通道、构造期 `probe_executable_version` 探测版本，不可用时以
`ProviderInfo(available=False, diagnostics=...)` 报告而非中途抛错。

## Placement Marker

```markdown
# 参考文献 {#chap:references}

::: bibliography
:::
```

`::: bibliography` 只表示 bibliography instruction 的放置位置，不覆盖 Front
Matter 中的文件或样式配置。未提供 marker 时，只要存在有效 citation，Compiler
就在正文指令末尾追加 bibliography instruction。

多个 marker 不会重复输出条目；第一个 marker 消费 referenced-only bibliography，
后续 marker 不生成重复条目。没有 citation 时 marker 不生成伪造记录或空白条目。

## Supported BibTeX Subset

V1 支持以下 entry type（ADR-0004 §2.2，对齐 28 条 golden corpus 验收范围）：

| Type | 类型标识 | Required fields | Optional formatting fields |
| --- | --- | --- | --- |
| `article` | [J] | `author`, `title`, `journal`, `year`（或 biblatex `date` 派生） | `volume`, `number`, `pages`, `doi` |
| `article` + `entrysubtype=newspaper` | [N] | `author`, `title`, `journal`, `date` | `pages`（版次） |
| `book` | [M] | `author`, `title`, `publisher`, `year` | `address`, `edition`, `translator` |
| `incollection` | [M]// | `author`, `title`, `booktitle`, `year` | `editor`, `address`, `publisher`, `pages` |
| `inproceedings` | [C]// | `author`, `title`, `booktitle`, `year` | `address`, `publisher`, `pages` |
| `collection` | [G] | `title`, `publisher`, `year`（著者可由 `editor` 替代） | `author`, `address` |
| `mastersthesis` | [D] | `author`, `title`, `school`, `year` | `address` |
| `phdthesis` | [D] | `author`, `title`, `school`, `year` | `address` |
| `techreport` | [R] | `author`, `title`, `institution`, `year` | `address`, `number`（报告编号） |
| `standard` | [S] | `title`, `year`（通常无个人著者，题名居首） | `author`, `number`（标准号）, `address`, `publisher` |
| `patent` | [P] | `author`, `title`, `number`, `year` | `address`, `publisher` |
| `online` / `electronic` | [EB/OL] | `title`, `url`（著者可缺省，题名居首） | `author`, `date`, `urldate` |
| `dataset` | [DS] | `author`, `title`, `publisher`, `year` | `address`, `url`, `urldate` |
| `map` | [CM] | `author`, `title`, `publisher`, `year` | `address` |
| `unpublished` | [A] | `author`, `title`, `year` | `note` |

biblatex 扩展字段同步支持：`date`（无 `year` 时按前 4 位派生 year；报纸条目
必须）、`urldate`（引用日期）、`entrysubtype=newspaper`（报纸）、`translator`、
`editor`、`edition`、`langid`/`language`（条目语言判定）、`note`。

字段名和 entry type 不区分大小写。值支持花括号、嵌套花括号、双引号和 bare
token；`%` 行注释会被忽略。作者/编者/译者使用 BibTeX `and` 分隔。页码中的
连续连字符会规范为单个 `-`。

以下情况明确失败：

- BibTeX 结构未闭合或字段语法错误：`BibliographyParseError`
- citation key 重复：`DuplicateBibliographyKeyError`
- entry type 不在 V1 集合中：`UnsupportedBibliographyTypeError`
- 缺少当前类型的必填字段：`MissingBibliographyFieldError`

Validator 将上述加载错误映射为结构化 `invalid-bibliography`。加载成功后，每个
Markdown citation key 必须存在；未知 key 返回 `missing-citation`，并保留 citation
所在的 Markdown 源码行。

## Citation Ordering

ordinal 按 citation 的首次实际渲染位置分配。正文按 inline 顺序遍历；首次遇到
`FootnoteReference` 时，会在该引用点展开对应脚注定义中的 citation，因此脚注
citation 不会因为定义通常写在文末而被错误延后。未附着到可渲染 inline 的已注册
citation 在上述遍历后按稳定注册顺序处理。grouped citation 保留源码声明的 key
顺序：

```markdown
[@doe2024; @smith2025, p. 12]
```

在两个 key 首次出现且 ordinal 分别为 1、2 时，V1 输出：

```text
[1,2, p. 12]
```

重复引用复用首次分配的 ordinal。

## Referenced-Only Bibliography

bibliography 只包含 cited records，每个 key 恰好一次，并按首次引用顺序排列。
BibTeX 文件中的记录顺序不决定输出顺序，未引用记录不会输出。

## GB/T 7714-2025 V1 Contract

`Gbt7714Formatter`（经 `BuiltinGbt7714Provider` 暴露）提供上表全部类型的确定性
数字顺序制文本输出。合同由两组 golden fixture 锁定：

- `tests/fixtures/bibliography/gbt7714-v1.*`：5 类型手写 golden（保持不动）；
- `tests/fixtures/bibliography/gbt7714-2025-corpus.*`：28 条 golden corpus
  （语料复制自 `spikes/phase0/citation/corpus/gbt7714-corpus.bib`）。其中
  19 条 `passed-machine-check` 逐字节锁定为内建引擎回归基线；9 条
  `pending-human-review` 仅校验结构完整性（`must_contain`），GA 前持
  GB/T 7714-2025 标准文本人工定稿后转为逐字节。golden 更新必须人工审查，
  不得 CI 自动接受（ADR-0004 §2.6 / ADR-0006）。

### 著者截断

著者/编者/译者 ≥4 名时截断为前 3 名 + 语言对应术语（中文 "等"、西文
"et al"），参数对齐官方 GB/T 7714-2025 CSL（et-al-min=4、use-first=3）。

### 条目语言与标点

标点体系按条目语言切换：中文条目用全角（，：（）），西文条目用半角
（`, `、`: `、`()`）。语言判定规则：

1. `langid`/`language` 命中 `zh|chinese` → 中文；命中
   `en|english|american|british` → 西文；
2. 字段缺省或无法识别时，题名、著者、编者、译者任一含 CJK 字符 → 中文，
   否则 → 西文。

西文著者姓全大写、多名首字母不空格（`KUHN TS`），沿用 GB/T 7714-2015 欧美
著者姓名规则的既有行为。

### 其他著录规则

- 版本项：中文条目数字版本输出 `2 版`，西文条目输出 `2nd ed`（序数词 + ed）；
  非数字版本原样输出。
- 译者：专著含 `translator` 时著录 `译者，译.`（西文 `trans`），置于版本项后。
- 缺卷号期刊：输出 `年（期）：页`，不再出现 `年, (期)` 的缺陷格式。
- `techreport`/`standard`/`patent` 的 `number` 以 `题名：编号` 并入题名项。
- 含 DOI/URL 的印刷型条目不自动附加 `/OL` 载体标识（输出 [J]/[DS]）；`/OL`
  仅用于 `online`/`electronic` 的 [EB/OL]。

### 与官方 CSL 渲染的已知差异（有意取舍，见 golden `engine_deltas_vs_pandoc`）

- 西文著者姓全大写（官方 CSL 样式不做大写转换）；
- 西文条目按条目语言输出半角标点 + `et al`（官方 CSL 固定 zh-CN locale，
  输出全角 + "等"）；
- [G]/[S]/[CM] 由内建引擎直接支持；pandoc BibTeX 前端盲区输出 [M]/[Z]/[Z]
  （官方 2025 CSL 无 [G] 分支，任何 CSL 路径都无法产出 [G]）；
- 西文版本项输出 `2nd ed`（CSL 中文 locale 输出 `2 版`）。

这是 ThesisForge V1 的受限格式合同，不代表对 GB/T 7714-2025 所有文献类型、
姓名语言规则、电子资源标识、析出文献变体或标点分支的完整覆盖。未来可替换为
本地 CSL/citeproc backend，但不得改变离线、renderer-neutral 和验证先行的核心
边界。
