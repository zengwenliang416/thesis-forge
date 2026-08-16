# Phase 0 实证报告：Word 字段生命周期（TOC / SEQ / REF / PAGE）

日期：2026-08-15。环境：macOS（外部卷 /Volumes/zwl），Microsoft Word 16.107.2，
LibreOffice 26.2.3.2（soffice），WPS（本次未纳入自动结论，见 §4）。
解释器：项目 `.venv/bin/python`。

本目录脚本可重复运行，顺序：

```bash
.venv/bin/python spikes/phase0/fields/build_samples.py
.venv/bin/python spikes/phase0/fields/inspect_fields.py
.venv/bin/python spikes/phase0/fields/verify_structure.py
.venv/bin/python spikes/phase0/fields/verify_lo_refresh.py
.venv/bin/python spikes/phase0/fields/verify_apps.py   # 驱动本机 Word，约 10–15 分钟
```

## 1. 样本与「生成态」的构建方式

`samples/` 下两份样本，templates/schools 两个模板各一份：

| 样本 | 源 | 模板 | 内容 |
| --- | --- | --- | --- |
| `complete-thesis-example.docx` | `examples/complete-thesis/thesis.md` | `example-university/2026.yaml` | TOC、图/表/公式 SEQ、8 个 REF、脚注、lowerRoman+decimal 页码 |
| `minimal-hut.docx` | `samples/minimal-source.md`（本 spike 构造） | `hunan-university-of-technology/master-2026.yaml` | 仅 1 章标题 + TOC + 1 个图题注 + 1 个 REF，upperRoman+decimal 页码 |

关键：构建走 `build_service` 完整管线，但通过
`ApplicationDependencies(document_refresher=_NoRefresh())` 注入 no-op refresher
绕开 FINALIZE 阶段的 LibreOffice finalizer（`build_samples.py:29`），
保留渲染器生成的原始字段状态。这是不动既有代码的官方扩展点。

## 2. 字段清单实证（results/fields-inventory.json）

生成态 DOCX 的事实（`inspect_fields.py` 解包提取）：

- **TOC**：`word/document.xml` 中 1 个 `TOC \o "1-3" \h \z \u` 字段，
  fldChar begin 带 `w:dirty=true`，有 separate/end，**cached result 为空**
  （无任何缓存条目）。段落被 `tf_toc_index` 书签包裹（供 LO finalizer 定位）。
- **SEQ**：题注/公式编号为 `SEQ TF_Figure_1 \r 1 \* ARABIC` 形式
  （`\r` 钉值 + cached result "1"），dirty=true。
  complete 样本 3 个（图/式/表），minimal 样本 1 个。
- **REF**：交叉引用为 `REF tf_fig_architecture \h` 形式，dirty=true，
  cached result 为编译期算好的显示文本（如 `图1-1`、`(2-1)`、`表2-1`、
  算法/代码清单引用缓存的是标题文字）。complete 样本 8 个，minimal 1 个。
- **PAGE/NUMPAGES**：只在 footer 部件。complete（example 模板，含总页数）
  为 footer1/footer2 各 PAGE+NUMPAGES；minimal（HUT 模板，奇偶+首页+多节）
  为 5 个 footer 各一个 PAGE。cached result 恒为 "1"，dirty=true。
- **settings.xml**：`<w:updateFields w:val="true"/>` 存在。
- **bookmark**：`tf_chap_*` / `tf_sec_*` / `tf_fig_*` / `tf_tbl_*` /
  `tf_eq_*` / `tf_alg_*` / `tf_lst_*` / `tf_toc_index` 全部成对出现
  （bookmark pairing 校验通过）。

## 3. 结构校验（results/structure-checks.json）

`verify_structure.py` = `qa/tools/openxml_validate.py` 13 项门禁 + 6 项 XPath 断言。
两个样本全部通过：

- openxml_validate 全过（ZIP/rels/XML/书签配对/字段配对/sectPr/样式与编号引用等）；
- TOC 指令恰为 `TOC \o "1-3" \h \z \u` 且 cached 为空；
- SEQ 数 == fig/tbl/eq 书签数（3==3、1==1）；
- 全部 REF 目标均在 bookmark 清单内；
- PAGE/NUMPAGES 只在 footer；
- pgNumType fmt 序列为 `[none?(封面节), lowerRoman|upperRoman(前置节), decimal(正文节)]`，
  与模板一致。

## 4. 三软件「无修复打开」结论（results/no-repair.json）

| 样本 | Word 16.107.2 | LibreOffice 26.2.3.2 | WPS |
| --- | --- | --- | --- |
| complete-thesis-example（原样） | 首开 fail：弹窗阻塞 150s；会话内多次回答后复核 pass（11.1s，无弹窗，见 §5 抑制观察） | pass（4.7s 导出 PDF 351940B） | 未测（见下） |
| minimal-hut（原样） | 首开 fail：弹窗阻塞 150s；会话内多次回答后手工复核 4.1s 无弹窗打开 | pass（4.4s 导出 PDF 139451B） | 未测 |
| \*-no-updatefields | fail：弹窗阻塞 150s | pass | 未测 |
| \*-keep-updatefields-nodirty | fail：弹窗阻塞 150s | pass | 未测 |
| \*-no-updatefields-nodirty | **pass：静默打开、未探测到对话框** | pass | 未测 |

**重要澄清：Word 的 fail 不是「修复提示」。** 用 System Events 读取对话框文本，
实际内容是：

> 「该文档包含的域可能引用了其他文件。是否更新该文档中的这些域？」
> 按钮：否（N) / 是（Y)

这是字段更新确认框（模态，不点击则「打开」不完成）。三格对照变体证明
`w:updateFields` 与 `w:fldChar w:dirty` **各自独立触发**该弹窗；
两者都去掉后 Word 静默打开（pass）。no_repair_open 目前无法区分
「字段更新确认框」与「修复提示」，只能统一判 fail——这本身是 qa 工具的改进点。

WPS 未纳入自动结论：wpsoffice 无脚本接口判断修复提示，
no_repair_open 对 WPS 只会给 `pending-human-review`；本次未人工开 WPS 窗口确认，
如需可重跑 `verify_apps.py --with-wps` 后人工核对。

## 5. Word 字段刷新行为实证（results/word-refresh.json）

方法（`verify_apps.py`，AppleScript 驱动 Word，全程「关闭不保存」，
每个实验前后校验样本 sha256 不变）：

1. 打开样本；若弹 updateFields 确认框则点「否（N)」——
   保留生成态，抓取真实「刷新前」快照；
2. 抓取：TOC 条目数与文本、main story 全部字段 code/result、
   六种页眉页脚 story 的字段 code/result；
3. `update`（table of contents）+ 逐字段 `update field`（main + 页眉页脚）；
4. 再抓取「刷新后」快照；
5. `save as ... format PDF` 导出 `samples/<stem>-word-refreshed.pdf`；
6. 关闭不保存。

### 观察结果（results/word-refresh.json，两样本一致）

**打开阶段**：
- 两个原始样本打开时都弹出模态确认框
  「该文档包含的域可能引用了其他文件。是否更新该文档中的这些域？」（否/是）。
  不点击文档不会完成打开。点「否（N)」后文档以生成态打开。
- 打开后（拒绝更新）的字段快照（`before_update`）：
  TOC 字段 result 为**空**（AppleScript 读为 missing value）；
  REF 显示 cached（`图1-1`/`(2-1)`/`表2-1`/标题文字）；
  SEQ 显示 cached "1"。
- 物理证据 `samples/*-word-declined.pdf`（拒绝更新状态下导出）：
  「目录」标题下**无任何条目**；正文 REF/SEQ 显示 cached 值；
  页脚 PAGE/NUMPAGES 显示**真实值**（如 `第i页/共6页`、罗马/阿拉伯混排正确）——
  PAGE/NUMPAGES 由 Word 排版引擎动态求值，cached "1" 不影响显示；
  同时证明 **Word 导出 PDF 不会自动填充空 TOC**。

**弹窗触发源（3 格对照变体，各 2 个样本，结论一致）**：

| 变体 | updateFields | fldChar dirty | 打开时弹窗 |
| --- | --- | --- | --- |
| 原样本 | ✓ | ✓ | 是 |
| `-no-updatefields` | ✗ | ✓ | **是** |
| `-keep-updatefields-nodirty` | ✓ | ✗ | **是** |
| `-no-updatefields-nodirty` | ✗ | ✗ | **否（静默打开）** |

即 Word Mac 16.107.2 上 `w:updateFields` 与 `w:dirty` **各自独立**触发同一确认框；
两者都剥掉才静默打开。变体打开后的字段快照与原样本相同
（TOC 空、cached 照常显示），证明 dirty/updateFields 不影响 cached 显示语义。

**弹窗的会话内抑制（补充观察）**：同一份带 dirty+updateFields 的文档，
在同一 Word 会话内首次打开必弹窗；对两个原样本重复打开并回答「否」多次后，
Word 停止弹窗、静默打开（no-repair 复核 complete-thesis-example 11.1s pass、
minimal-hut 手工验证 4.1s 无弹窗）。但只打开过一次的变体在第二次打开时仍弹窗。
抑制的确切规则未确定（与次数/最近文档状态有关），ADR 不应依赖它——
**面向用户的「首次打开」必然弹窗**这一结论不变。

**刷新阶段**（`update` TOC + 逐字段 `update field`，全部 ok，0 失败；
update_log 计数 complete=50 / minimal=5，其中包含 TOC 填充后 Word 在
TOC result 内生成的 HYPERLINK/PAGEREF 子字段——19 个条目 × 2，
加上原有 12/3 个字段）：

- TOC 被填充为真实条目（`摘要→i … 绪论→1 …`，页码与节 fmt 一致），
  **指令保持 `TOC \o "1-3" \h \z \u` 不变**；Word 在 TOC result 内自动插入
  `HYPERLINK \l "_Toc…"` + `PAGEREF _Toc… \h` 子字段。
- **全部 REF/SEQ 的 result 刷新前后完全一致**（按指令匹配比对）：
  SEQ `\r` 钉值使 F9 后仍得 "1"；REF cached 与 Word 重算一致。
- 局限：Mac Word AppleScript 无 header/footer 对象模型，
  `get story range` 只能访问第 1 节 story，本实验中 story 循环未触及
  后续节页脚的 PAGE 字段（PDF 物理证据显示页脚页码排版正确，
  PAGE/NUMPAGES 由排版引擎动态求值，本就不依赖刷新）。
- 刷新后导出 `samples/*-word-refreshed.pdf` 成功；原 docx sha256 全程不变。

### 对「无 cached 条目的 TOC 在 Word 打开时是否自动填充」的回答

**不会自动填充，且不会静默更新。** Word Mac 16.107.2 对带
updateFields/dirty 的文档是**先弹模态确认框**：
- 点「是」→ 字段更新，TOC 填充（未实测此路径，但语义明确）；
- 点「否」→ TOC 保持空，直到用户手动 F9 / 更新目录；导出 PDF 也为空。
只有完全去掉 updateFields 和 dirty 的文档才静默打开（此时 TOC 同样为空，
靠 cached result 显示——但我们 TOC 没有 cached 条目，所以显示为空目录）。

### SEQ `\r` 钉值对 Word 端 F9 重编号的影响

实测：生成态 SEQ 指令为 `SEQ TF_Figure_1 \r 1 \* ARABIC`（cached "1"），
在 Word 中全量 `update field` 后 result 仍为 "1"——**`\r` 钉值在 Word 端
F9 重编号时生效，编号被钉死在编译期计算值**。推论（字段语义，未单独实测）：
用户后续在 Word 里增删图片后 F9，编号不会按文档顺序流动重排，
而是保持钉值；这是「编译期编号权威」的语义，但意味着 Word 端编辑后
编号不再自动流动。注意 LO finalizer 会**剥掉 `\r`**（见 §6），
经 LO 刷新后的文档在 Word 中 F9 才恢复顺序重算。

## 6. LibreOffice finalizer 路径实证（results/lo-refresh-diff.json）

方法（`verify_lo_refresh.py`）：复制样本到临时目录 → 走生产同款
`refresh_document_safely(LibreOfficeDocumentRefresher, copy)`
（刷新后还原渲染器所属的 styles.xml/fontTable.xml）→ 对比前后快照。
刷新后副本保留为 `samples/<stem>-lo-refreshed.docx`。

**已证实的 LO 刷新效果**（两份样本一致）：

- TOC 被填充为真实条目（标题 + 页码，如 `摘要i Abstracti 绪论1 …`），
  指令被 LO 改写为 `TOC \f \o "1-3" \h`（**丢失 `\z \u`**，新增 `\f`）；
- TOC 条目配套新增 19 个（minimal 1 个章节对应 1 个）
  `__RefHeading___Toc…` 书签，供 TOC 超链接跳转；
- **SEQ 的 `\r` 钉值被 LO 丢弃**：`SEQ TF_Figure_1 \r 1 \* ARABIC`
  → `SEQ TF_Figure_1 \* ARABIC`（cached "1" 不变）。
  即经过 LO finalizer 后，Word 端 F9 会按文档顺序重算 SEQ；
- REF 字段指令与 cached result **均未被 LO 改动**（`REF tf_fig_architecture \h`
  原样保留，cached 仍为编译期文本）；
- PAGE/NUMPAGES cached 被改为评估值（如 `ii`/`viii`；minimal 样本出现
  `PAGE cached=0` 的封面节页脚，说明 LO 对"该节不显示页码"的评估与
  Word 显示语义可能不一致）；
- **settings.xml 的 `w:updateFields` 被 LO 移除**——finalizer 之后的文档
  在 Word 中打开不会再弹 §4 的确认框；
- 页眉页脚部件被 LO 整体重写（字段在 footer 部件间重新分布，数量迁移）；
- **刷新后 openxml_validate 失败**（两样本均 exit=1）：
  - complete-thesis-example：正文引用了 `FootnoteCharacters`、`IndexLink`、
    `TOC1`、`TOC2`、`TOC3` 样式，但渲染器的 styles.xml 未定义
    （example 模板无 `toc:` 配置，渲染器不生成 TOC1-3 样式；
    LO 写 TOC 条目时按内置习惯引用它们）；
  - minimal-hut：仅缺 `IndexLink`（HUT 模板有 `toc:` 配置，TOC1-3 已定义；
    minimal 无脚注故无 FootnoteCharacters 引用）。
  - 注：styles.xml 还原机制本身工作正常（刷新后 styles.xml 与原件
    sha256 一致），缺口是「渲染器样式覆盖面 < LO 输出引用的样式」。

**过程中发现的既有代码问题（未修改，仅记录）**：
`src/thesis_forge/application/office_refresh.py:592`
`_run_libreoffice_refresh` 在 darwin 上硬编码 `tempfile dir="/tmp"`。
本机 `/private/tmp` 缺失（/tmp 悬空），该路径会导致 finalizer 静默失败
（refresh 返回 False 并回滚）。本 spike 通过
`LibreOfficeDocumentRefresher.runner` 注入点替换为等价实现绕过。
建议后续把 `temporary_root` 改为 `None`（tempfile 默认，尊重 TMPDIR）。

## 7. cached result 策略评价

实证支持的结论：

- **REF/SEQ 的 cached result 是必要的且质量合格的**：在 Word 拒绝更新、
  LO 不刷新、任何不做字段求值的查看器里，cached 文本（图1-1/(2-1)/表2-1）
  就是最终显示，且与 Word 重算结果一致（刷新前后逐字段比对稳定）。
  保留 dirty + cached 是合理组合：显示有兜底，求值有权威。
- **TOC 无 cached 条目是最大的空窗**：任何不刷新字段的路径
  （Word 点「否」、直接导出 PDF、多数预览器）都会显示空目录。
  若 draft profile 面向「生成即读」场景，应让 finalizer 填充 TOC cached，
  或接受空目录并在 UI 明确提示。
- **PAGE/NUMPAGES cached 恒 "1" 无害**：Word 排版时动态求值
  （ declined PDF 中页脚显示真实罗马/阿拉伯页码）；只有 LO 刷新会写入
  评估值，且出现过 `0`（封面节），属于可接受的中间态。
- dirty/updateFields 的副作用实测：两者各自独立触发 Mac Word 的
  模态确认框。若目标产物要求「双击即开无打扰」，必须两者都不带
  （`=no-updatefields-nodirty` 变体实测静默打开）。

## 8. finalizer profiles（draft / final-auto / final-word）事实输入

| profile | 语义设想 | 本实证提供的事实 |
| --- | --- | --- |
| draft（生成态直出） | dirty+updateFields，交给 Word 打开时刷新 | Mac Word 首开**必弹模态框**，且自动化/批量场景会被阻塞 150s+；TOC 空直到用户确认；LO/WPS 无此问题（LO headless 转换 pass） |
| final-auto（LO 无头刷新） | 构建期用 LO 填好 TOC/cached | 实测可行（120s 内完成）：TOC 填充、PAGE/NUMPAGES 写入评估值、updateFields 被移除（Word 首开不再弹窗）；代价：SEQ `\r` 被剥、TOC 指令被改写（丢 `\z \u`）、新增 `__RefHeading__` 书签、页眉页脚部件重写、**openxml_validate 失败**（LO 引用的 TOC1-3/IndexLink/FootnoteCharacters 样式未在渲染器 styles.xml 定义；example 模板无 toc 配置时更严重） |
| final-word（Word 自动化刷新） | 用本机 Word 刷新后保存 | 本实证证明 AppleScript 驱动可行（update TOC + update field 全成功、指令不被改写、SEQ `\r` 保留），但需处理模态弹窗与沙盒授权，且依赖用户机器装 Word——不适合默认路径 |

补充事实：`refresh_document_safely` 的 styles.xml/fontTable.xml 还原机制
工作正常（刷新后两部件与原件 sha256 一致）；缺口是渲染器样式覆盖面，
建议在渲染器无条件补齐 TOC1-3/IndexLink/FootnoteCharacters 等 LO 会引用的样式，
或在 finalizer 后修补。

## 9. 给 ADR-0005 的建议回答问题清单

1. 「无修复打开」的定义是否要把 updateFields 确认框与真正的修复提示区分开？
   （本实证证明二者在 Word Mac 上都表现为模态阻塞，但语义完全不同；
   qa/tools/no_repair_open.py 目前无法区分，只能判 fail。）
2. 生成态（dirty + updateFields）产物面向 Mac Word 用户时，
   首开必弹确认框是否可接受？还是默认出「final-auto」（LO 刷新后）产物？
3. LO finalizer 会丢 SEQ `\r` 钉值、改 TOC 指令、移除 updateFields、
   引入未定义样式引用——这些改写是否都在接受范围内？
   TOC1-3 / IndexLink / FootnoteCharacters 样式是否应由渲染器无条件补齐？
4. LO 刷新后 openxml_validate 失败：finalizer 产物是否必须过同一套门禁？
   若是，谁负责补样式（渲染器兜底 or finalizer 后修补）？
5. draft profile 是否需要「剥掉 updateFields + dirty」选项（对照变体证明
   两者都剥掉后 Word 静默打开、TOC 留空待用户 F9）？
6. PAGE cached "0"（LO 对封面节页脚的评估值）是否需要在 finalizer 后矫正，
   还是接受（反正 Word 显示时按节语义重算）？
7. /tmp 硬编码的可移植性问题是否单独立项修复（本机已实测会踩中）？

## 10. 过程中遇到的问题（工程记录）

1. **本机 /tmp 悬空**（/private/tmp 缺失）：office_refresh.py 的 LO finalizer
   在 darwin 硬编码 `tempfile dir="/tmp"`，会直接失败回滚。本 spike 用
   `LibreOfficeDocumentRefresher.runner` 注入等价实现绕过；项目代码未改动。
2. **Word 沙盒授权**：样本在外部卷 /Volumes/zwl，Word 首次向 samples/
   写 PDF 时弹「授予文件访问权限」，需人工点「选择...」+ 确认一次
   （授权后本会话内不再出现）。全自动化环境应预置授权或用已授权目录。
3. **Word AppleScript 不能迭代 `every field`**：`repeat with f in fields of doc`
   报 -1708（"every field" 不理解 "count"），但 `count of fields of doc`
   与按下标 `field i of doc` 正常——脚本已全部改为下标迭代。
   Mac Word 无 header/footer 对象模型，`get story range` 仅覆盖第 1 节。
4. **macOS AppleDouble/锁文件污染**：外部卷会生成 `._*.docx`，
   Word 打开时生成 `~$*.docx`，脚本 glob 需显式过滤。
5. **qa/tools/no_repair_open.py 无法区分弹窗类型**：updateFields 确认框
   与修复提示在它看来都是「1 个对话框」。本 spike 通过变体矩阵 +
   System Events 读文本补上了这一层。

## 11. 产物清单

```
spikes/phase0/fields/
├── build_samples.py          # 构建生成态样本（绕开 finalizer）
├── inspect_fields.py         # 字段清单提取 → results/fields-inventory.json
├── verify_structure.py       # 结构校验 → results/structure-checks.json
├── verify_lo_refresh.py      # LO finalizer 实证 → results/lo-refresh-diff.json
├── verify_apps.py            # 三软件打开 + Word 刷新实证
├── REPORT.md                 # 本报告
├── samples/
│   ├── complete-thesis-example.docx          # 生成态样本（example 模板）
│   ├── minimal-hut.docx                      # 生成态样本（HUT 模板）
│   ├── minimal-source.md / minimal-image.png # 最小样本源
│   ├── *-no-updatefields.docx                # 对照变体：剥 updateFields
│   ├── *-no-updatefields-nodirty.docx        # 对照变体：再剥 fldChar dirty
│   ├── *-keep-updatefields-nodirty.docx      # 对照变体：留 updateFields 剥 dirty
│   ├── *-lo-refreshed.docx                   # LO finalizer 产物副本
│   ├── *-word-declined.pdf                   # Word 打开时点「否」后导出（TOC 空）
│   └── *-word-refreshed.pdf                  # Word 刷新后导出（TOC 填充）
├── results/
│   ├── fields-inventory.json
│   ├── structure-checks.json
│   ├── no-repair.json / no-repair-*.json
│   ├── word-refresh.json
│   └── lo-refresh-diff.json
└── word.sdef.xml             # Word AppleScript 字典导出（参考）
```
