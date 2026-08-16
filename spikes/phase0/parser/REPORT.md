# Phase 0 Spike：Parser 后端选型实证报告

- 日期：2026-08-14
- 关联风险：R-001（正则 Parser 不可持续）、R-002（Pandoc 二进制分发）、R-003（SourceMap 不完整导致诊断无法定位）
- 关联决策：ADR-0001（Parser 后端选型，本报告只提供事实，不给结论）
- 目录：`spikes/phase0/parser/`

## 1. Spike 方法

候选后端：

- **A. pandoc JSON AST**（本机 pandoc 3.8.2.1，`/opt/homebrew/bin/pandoc`，arm64 Mach-O 单二进制 **253 MB**）
- **B. markdown-it-py**（4.2.0）+ mdit-py-plugins（0.6.1），纯 Python，已装入 `.venv`
- **C. 保留手写 parser 并工程化加固**（`src/thesis_forge/core/parser.py`，396 行，正则 + 逐行扫描）

方法：

1. 依据 `docs/MARKDOWN_SPEC.md` 构造覆盖全部项目语法的单文件 fixture
   `fixtures/full-syntax.md`（front matter、1–4 级标题 + `{#id}`、六种 `:::`
   容器、容器头 kv 元数据、单/多/带 locator citation、七种前缀 crossref、
   脚注引用/定义/续行、行内与块级数学、有序（起始序号 3）/无序/嵌套列表、管道表）。
   该 fixture 先经现有 parser 验证可完整解析（19 个 block、3 条 citation、
   7 条 crossref、2 条脚注）。
2. 每个后端各写一个可重复运行的分析脚本，**所有结论由脚本机械提取**
   （不是手工读 AST 的印象），结果落盘 JSON：
   - `parse_pandoc.py` → `results/pandoc-analysis.json`
   - `parse_markdown_it.py` → `results/markdown-it-analysis.json`
   - `compare.py` → `results/coverage.json`（语法 × 后端覆盖矩阵）
3. 复跑方式：

```bash
cd spikes/phase0/parser
../../../.venv/bin/python compare.py   # 依次驱动三个后端，再生成全部结果
```

## 2. 逐项实证结果

### 2.1 pandoc 扩展名组合实测

测了三个组合（`pandoc --list-extensions=<reader>` 验证支持集）：

| 组合 | 命令 | 实测结论 |
|---|---|---|
| M | `pandoc -f markdown+fenced_divs+citations+footnotes+header_attributes+yaml_metadata_block+tex_math_dollars+pipe_tables -t json` | 学术扩展最全（citations 原生），但 **markdown reader 不支持 sourcepos 扩展**（扩展清单中不存在），任何方式（含 Lua filter）都拿不到位置 |
| X | `pandoc -f commonmark_x+sourcepos -t json` | 唯一能输出位置的路线；**commonmark_x 不支持 citations 扩展**（运行直接报错 `The extension citations is not supported for commonmark_x`），footnotes/fenced_divs/attributes/tex_math_dollars/pipe_tables/yaml_metadata_block 均可用 |
| M′ | `pandoc -f markdown-citations -t json` | 备选：关掉 citations 后 `@fig:x`、`[@key]` 全部保留为纯文本，可统一后处理，但仍无位置 |

**关键事实：pandoc 无法在同一趟解析中同时拥有原生 citation 节点和 sourcepos**。
要位置就得用 commonmark_x，然后自行从文本后处理 citation/crossref。

### 2.2 项目语法 → pandoc AST 映射（实测）

| 项目语法 | 组合 M（markdown） | 组合 X（commonmark_x+sourcepos） |
|---|---|---|
| YAML front matter | `meta` 字典，原生 | 同左（实测 keys=document/thesis/author/render） |
| `# 标题 {#chap:x}` | `Header`，attr id **原样保留冒号**（`chap:introduction`） | 同左，且带 `data-pos` |
| 段落 | `Para` | `Para` 外包一层 `Div(wrapper=1)` 携带位置 |
| `[@k; @k2, p. 12]` | `Cite` 原生：多 key 拆成多个 citation 项；locator 进 `citationSuffix`（实测 suffix=`, p. 12`，且 `p.` 后空格被归一化为 **nbsp** `p. 12`） | 无 Cite 节点，纯文本散在多个 wrapper Span 里，需后处理重组 |
| `@fig:xxx` | 被解析为 `Cite(AuthorInText, citationId="fig:model")`——冒号合法，可按前缀白名单再解释（实测 7 个 crossref 全部以此形式出现） | 纯文本，需正则后处理 |
| `[^label]` + 定义 + 续行 | `Note` 节点嵌在引用点；**label 丢失**（pandoc Note 匿名，只按顺序编号）；续行合并进 Note 内容 | 同左；引用点 wrapper Span 带位置（实测 `19:92-19:99`），定义内容 Span 带定义点位置（实测 `84:10-84:16`） |
| `$...$` / `$$...$$` | `Math(InlineMath/DisplayMath)` 原生 | 同左，且带位置 |
| 有序列表起始序号 | `OrderedList` 保留 `start=3` | 同左 |
| 嵌套列表 | 嵌套 `BulletList` 原生 | 同左 |
| 管道表 | `Table` 原生 | 同左，但 **Table 节点（含单元格内容）完全没有位置** |
| `::: figure {#fig:model}` | **不识别**：fenced_divs 的裸词 class 写法不允许再跟 `{...}` 属性，实测静默退化为普通段落（fixture 中 5 个带 id 容器全部退化） | 同样不识别 |
| `::: {.figure #fig:model}` | `Div(id="fig:model", classes=["figure"])` 原生 | 同左，带位置 |
| `::: bibliography`（无属性） | `Div(classes=["bibliography"])` 原生识别 | 同左 |
| 容器头 kv 元数据行 | Div 内普通 `Para` 文本（实测 `src:`/`caption:`/`width:` 三行落在一个 Para），**需自行解析** | 同左 |

容器头预处理实证：`rewrite_container_headers()`（约 20 行正则）把
`::: figure {#fig:model}` 改写为 `::: {.figure #fig:model}` 后重跑组合 M，
**6/6 容器全部恢复为 Div**（id/class/内部结构齐全）。

### 2.3 source position 专项（R-003 硬需求）

| 路线 | 粒度 | 覆盖率（实测） |
|---|---|---|
| pandoc markdown reader | 无 | 0%（AST 不带任何位置，Lua filter 也无法补——reader 根本没记录） |
| pandoc commonmark_x+sourcepos | `data-pos="file@行:列-行:列"`，行列 + 文件前缀 | 块级：Header(6/6)、CodeBlock、真 Div 直接带；Para/列表项靠 wrapper Div 间接带（wrapper Div 23 个）；**盲区：Table 子树（含所有单元格）完全无位置**。行内：每个 inline 被 wrapper Span 包裹带行列（实测 181 个），含 Math、Note 引用点/定义点 |
| markdown-it-py | 块级 `token.map=[start,end)`，0-based **仅行无列**；inline token `map=None` | 块级普遍有行；行内（含 footnote_ref、math_inline）无任何位置 |
| 现有手写 parser | 块级仅行（`SourceLocation.line`，column=None）；**行内行列齐全** | fixture 全部 inline（citation/crossref/footnote_ref）实测均带 line+column |

markdown-it 补充实测：自写 inline rule 时 `state.src` 是**段落文本**（非全文），
`state.pos` 是段内偏移，配合宿主 inline token 的 `map` 可换算列号——spike 中
用 15 行 demo rule 成功把 `@fig:model` 定位到行列。但插件自带的 token
（如 footnote_ref）不记录位置，要列号需 fork/补丁插件。

### 2.4 自定义语法扩展成本（实测 + 工作量估计）

**pandoc 路线（以组合 X 为主线）：**

| 语法 | 实现方式 | 估计 |
|---|---|---|
| `::: kind {#id}` 容器头 | 源码预处理正则改写（spike 已实现并验证 6/6） | 0.5 人日 |
| 容器头 kv 元数据 | Div 内 Para 文本自解析，可平移现有 `KV_RE` 逻辑 | 0.5 人日 |
| `@fig:xxx` crossref | 合并 wrapper Span 重组文本 + 正则 + offset→pos 回映射 | 1–2 人日 |
| `[@key; ...]` citation | 同上，另需处理多 key 拆分、locator、pandoc 的 nbsp 归一化 | 1–2 人日 |
| 未闭合 `:::` 等语法错误预检 | pandoc **静默容错**（实测未闭合容器退化为 Para，无错误无警告），诊断体系需完全自建 | 0.5–1 人日 |
| Lua filter 替代方案 | 可在 pandoc 进程内做同等变换，但引入 Lua 维护面；**无法弥补 markdown reader 无 sourcepos 的缺陷**；与 Python 后处理等价 | 持平 |

**markdown-it-py 路线：**

| 语法 | 实现方式 | 估计 |
|---|---|---|
| `::: kind {#id}` 容器 | `container` 插件按名注册 6 次即可，**项目写法原样兼容**（`info=' figure {#fig:model}'` 原样保留头部串，自行解析即可）；未闭合容器静默吞到文末，需预检 | 0.5 人日 |
| 容器头 kv 元数据 | 容器内 paragraph 文本自解析（同现有逻辑） | 0.5 人日 |
| `@fig:xxx` crossref | 无现成插件，自写 inline rule（spike demo 约 30 行，段内偏移可换算列号） | 0.5–1 人日 |
| `[@key; ...]` citation | 无现成插件，自写 inline rule（多 key/locator 拆分） | 1–2 人日 |
| 标题 `{#id}` | `attrs` 插件实测**不提取**行尾 `{#id}`（attrs 为空、文本原样残留），需自行从 inline 文本提取（约 10 行） | 0.5 人日 |
| 行内列号 | 自写 rule 顺带记录；插件 token（footnote_ref 等）需补丁 | 0.5–1 人日 |

### 2.5 多文件 include

- **pandoc**：`pandoc -f commonmark_x+sourcepos main.md chap1.md` 直接接受多文件；
  实测 `data-pos` 带**文件名前缀且逐文件正确**
  （`include-main.md@6:1...`、`include-chapter.md@1:1...`）；
  首个文件的 front matter 正常解析（meta keys 实测含 thesis）。
  拼接语义 = 简单串联，章内 crossref 天然跨文件可见。
- **markdown-it-py**：`parse()` 只接受字符串，include 需调用层自行递归/拼接并
  自行维护行号偏移。
- **现有 parser**：`parse_markdown(path)` 单文件，无 include 机制。

### 2.6 错误诊断行为

| 输入 | pandoc | markdown-it-py | 现有 parser |
|---|---|---|---|
| 未闭合 `:::` 容器 | 静默退化为段落，退出码 0 | 容器静默吞到文末，无异常 | `ParseError("第 N 行的 figure 容器未闭合")` 带行号 |
| 无效 YAML front matter | 按普通文本处理 | 按普通文本处理 | `ParseError` 带行号 |

项目的诊断定位需求（`ValidationIssue.line`）在 A/B 两路都需自建一层预检/校验。

### 2.7 确定性

三条路线均机械验证：同一输入运行两次，输出逐字节/逐 token 一致
（pandoc `two_runs_byte_identical=true`；markdown-it `two_parses_token_equal=true`；
现有 parser block/citation 结构一致）。

## 3. 覆盖矩阵汇总（results/coverage.json）

状态计数（支持 / 部分支持 / 不支持，共 18 行语法特征）：

| 后端 | 支持 | 部分支持 | 不支持 |
|---|---:|---:|---:|
| C 现有手写 parser | 15 | 2（行内数学无语义节点；块级仅行号） | 1（多文件） |
| A pandoc JSON AST | 10 | 7 | 1（错误诊断） |
| B markdown-it-py | 9 | 7 | 2（行内位置、错误诊断） |

完整矩阵（含每格机制与实测证据）见 `results/coverage.json`，终端表格由
`compare.py` 打印。

## 4. 三候选对比

| 维度 | A. pandoc JSON AST | B. markdown-it-py | C. 手写 parser 加固 |
|---|---|---|---|
| 语法覆盖 | 基础语法原生最完整（数学/表格/列表/脚注结构）；**项目专属语法（容器写法、crossref）两种 reader 均不原生支持**，需预处理+后处理 | 基础语法靠插件齐全；容器写法原样兼容；citation/crossref 需自写 2 条 inline rule | 项目语法 100% 覆盖（现状即如此）；通用 Markdown 边缘语法（嵌套、转义、参考式链接等）靠正则长期补丁——正是 R-001 描述的风险 |
| source position | 仅 commonmark_x 系有，行列+文件前缀，块级覆盖好、Table 子树盲区；**与原生 citation 不可兼得** | 块级仅行；行内无位置，自写 rule 可换算列号 | 块级仅行、行内行列齐全（现状）；块级列号需补 |
| 自定义语法扩展成本 | 容器预处理 0.5 人日 + crossref/citation 后处理 2–4 人日 + 诊断预检自建 | 两条 inline rule + 容器头/kv 解析 + 预检，合计约 3–6 人日 | 0（已具备）；新增语法=继续写正则 |
| 多文件 include | 多文件参数原生可用，位置逐文件正确 | 调用层自行实现 | 调用层自行实现 |
| 分发/部署（R-002） | 单二进制 253 MB（本机 arm64）；无官方 pip 包；桌面端需按平台随包分发/签名，CLI 需用户自装或捆绑；需锁版本保证可重复 | 纯 Python wheel，进入现有 pip 分发链，零原生依赖 | 零新增依赖 |
| 确定性 | 实测逐字节可重复（锁版本前提下） | 实测可重复 | 实测可重复 |
| 迁移成本 | parser.py 整体替换：subprocess 调用 + JSON→ThesisDocument 映射层（约 300–500 行）+ 预处理/后处理/预检三层；`tests/test_parser.py`（278 行）按新语义调整；model/validator/compiler 不动 | token→ThesisDocument 映射层（约 300–400 行）+ 自写规则；测试同样需调整；model 不动 | 0 迁移；加固（块级列号、include、错误恢复、更多边缘测试）为增量成本 |
| 外部进程/性能 | 每次解析一次 subprocess + JSON 序列化（fixture 级文档实测单次约 0.3 s） | 进程内调用 | 进程内调用 |

## 5. 本 spike 未覆盖 / 建议后续验证

- 大文档（10 万字数级）下 pandoc subprocess + JSON 的吞吐与内存。
- pandoc 对嵌套 `:::` 容器、容器内再嵌表格的行为（项目语法当前禁止嵌套）。
- commonmark_x 的 CommonMark 严格性与项目语法的其他潜在冲突（如列表缩进规则差异）。
- Lua filter 路线与 Python 后处理路线的工程权衡未展开（两者能力等价，本 spike 只验证后者可行）。

## 6. 建议 ADR-0001 回答的问题清单

1. sourcepos 的最低可接受粒度是什么：现有「块级行 + 行内行列」是否已够？
   若要求块级列号，A（commonmark_x）与 B/C（自行补列）的相对成本如何权衡？
2. 是否接受「citation 无原生节点、按文本后处理」？（A 路线要 sourcepos 就必须接受；
   B 路线本就没有原生 citation。）
3. 是否接受把 pandoc 二进制（253 MB/平台）纳入分发链并锁版本？（R-002）
   若否，A 路线直接排除。
4. 项目语法是否允许向 pandoc 兼容方向调整（如容器头改为 `::: {.figure #id}`），
   还是坚持 `::: figure {#id}` 写法由预处理兼容？
5. 错误诊断（未闭合容器、非法 ID 等）由哪一层负责？A/B 都需要自建预检，
   这层预检本身是否就构成一个"小手写 parser"，从而抵消换后端的收益？
6. 脚注 label 是否必须保留到 ThesisDocument？（A 路线 label 必然丢失，只能按序编号。）
7. Table 位置盲区（A 路线）是否影响 `resource-path-escape`、表格结构错误的定位要求？
8. 多文件 include 是否已进入 V1 范围？若是，A 的多文件能力权重应提高多少？
9. C 路线的加固验收标准是什么：补多少边缘语法测试、是否引入基于状态的块扫描
   替代纯正则，即可关闭 R-001？
10. 选型后 `parse_markdown_text()` 的公共契约（ThesisDocument + SourceLocation +
    ParseError）是否冻结不变，以保证 model/validator/compiler/renderer 零改动？

## 附录 A：实测命令摘要

```bash
# 组合 M：学术扩展全开
pandoc -f markdown+fenced_divs+citations+footnotes+header_attributes+yaml_metadata_block+tex_math_dollars+pipe_tables -t json fixtures/full-syntax.md
# 组合 X：唯一有位置的路线
pandoc -f commonmark_x+sourcepos -t json fixtures/full-syntax.md
# 多文件
pandoc -f commonmark_x+sourcepos -t json fixtures/include-main.md fixtures/include-chapter.md
# citations 扩展在 commonmark_x 下直接报错
pandoc -f commonmark_x+sourcepos+citations -t json ... 
#   -> "The extension citations is not supported for commonmark_x."
# markdown-it 分析
../../../.venv/bin/python parse_markdown_it.py
# 汇总矩阵
../../../.venv/bin/python compare.py
```

全部原始数据：`results/pandoc-analysis.json`、`results/markdown-it-analysis.json`、
`results/coverage.json`。
