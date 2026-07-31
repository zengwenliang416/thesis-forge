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

V1 支持以下 entry type：

| Type | Required fields | Optional formatting fields |
| --- | --- | --- |
| `article` | `author`, `title`, `journal`, `year` | `volume`, `number`, `pages`, `doi` |
| `book` | `author`, `title`, `publisher`, `year` | `address` |
| `inproceedings` | `author`, `title`, `booktitle`, `year` | `address`, `publisher`, `pages` |
| `mastersthesis` | `author`, `title`, `school`, `year` | `address` |
| `phdthesis` | `author`, `title`, `school`, `year` | `address` |

字段名和 entry type 不区分大小写。值支持花括号、嵌套花括号、双引号和 bare
token；`%` 行注释会被忽略。作者使用 BibTeX `and` 分隔。页码中的连续连字符会规范为
单个 `-`。

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

`Gbt7714Formatter` 提供上述五类文献的确定性数字顺序制文本输出。当前合同由
`tests/fixtures/bibliography/gbt7714-v1.*` golden fixtures 锁定。

这是 ThesisForge V1 的受限格式合同，不代表对 GB/T 7714-2025 所有文献类型、姓名
语言规则、电子资源标识、析出文献变体或标点分支的完整覆盖。未来可替换为本地
CSL/citeproc backend，但不得改变离线、renderer-neutral 和验证先行的核心边界。
