# Phase 0 引用引擎对比实证报告（GB/T 7714-2025）

- 日期：2026-08-14
- 环境：macOS；pandoc 3.8.2.1（自带 Haskell citeproc）；Python 3.14.4（`.venv`）；citeproc-py 0.10.7
- 语料：`corpus/gbt7714-corpus.bib`（28 条，biblatex 扩展字段）
- 本报告只记录实证事实；所有结论均可用 `render_*.py` / `compare.py` / `build_golden.py` 复现。

## 1. Corpus 设计

28 条 BibTeX 条目，每条附 `%` 注释说明覆盖点。类型分布：

| 类别 | 条目 | GB/T 类型标识 |
|------|------|--------------|
| 期刊文章 | zh-article-3（3 著者+DOI）、zh-article-etal（5 著者触发"等"）、en-article-etal（4 著者，langid=english）、en-article-doi、zh-article-no-volume（缺卷）、zh-article-no-pages（缺页码）、en-article-online-first（无卷期页，仅 DOI）、mixed-article（中文著者+西文刊名） | [J] |
| 专著 | zh-book、en-book-edition（第 2 版）、zh-book-translator（译著）、org-book（机构著者） | [M] |
| 专著析出 | zh-incollection、en-incollection | [M]// |
| 会议析出 | zh-inproceedings、en-inproceedings（4 著者） | [C]// |
| 汇编 | collection-g（仅编者） | [G] |
| 报纸 | zh-newspaper（entrysubtype=newspaper，date+版次） | [N] |
| 学位论文 | zh-mastersthesis、zh-phdthesis | [D] |
| 科技报告 | zh-techreport（含报告号） | [R] |
| 标准 | standard-gb（GB/T 7714-2015 本身） | [S] |
| 专利 | zh-patent（含专利号） | [P] |
| 电子资源 | zh-online（发布日期+引用日期+URL）、en-online-noauthor（无著者） | [EB/OL] |
| 数据集 | zh-dataset | [DS] |
| 舆图 | zh-map | [CM] |
| 档案 | zh-archive | [A] |

边界情形覆盖：>3 著者截断（3 条）、无著者（en-online-noauthor）、机构著者（org-book）、
中英文混合（mixed-article）、缺卷（1）、缺页码（1）、无卷期页（1）、含 DOI（3）、
含引用日期+URL（2）。

派生物 `corpus/gbt7714-corpus.csl.json` 由 `pandoc -f bibtex -t csljson` 生成，
作为 citeproc-py 的输入（保证两个 CSL 引擎看到完全相同的数据，差异只来自引擎本身）。

## 2. CSL 样式来源事实

| 项 | 值 |
|----|----|
| 文件 | `corpus/china-national-standard-gb-t-7714-2025-numeric.csl` |
| 来源 URL | https://raw.githubusercontent.com/citation-style-language/styles/master/china-national-standard-gb-t-7714-2025-numeric.csl |
| SHA256 | `3b5ab6249ce23b57954c9a4a67e0df422d8759b0573cae7e7de2f2ef94895faf` |
| 仓库 commit | `440c9c9f38136fc4a90dca2d3ba974ae08988274`（2026-05-10，"Format comments"） |
| 样式标题 | China National Standard GB/T 7714-2025 (numeric, 中文) |
| 作者 | Zeping Lee |
| 许可证 | CC-BY-SA-3.0（样式文件 `<rights>` 声明） |
| 关键参数 | `default-locale="zh-CN"`；`et-al-min="4" et-al-use-first="3"`；`second-field-align="flush"`；`page-range-format="expanded"` |

**2025 版存在**：官方仓库同时提供 2025 的 numeric / author-date / note 三件套
（另有 2015 三件套与 1987/2005 旧版）。本次直接使用 2025 numeric，无需回退。

## 3. pandoc vs citeproc-py

输入完全相同（同一 CSL JSON + 同一 CSL）。**28 条中仅 5 条一致（忽略空白后），一致率 17.9%**。

差异分类（见 `results/comparison.json`）：

| 差异类别 | 条数 | 说明 |
|---------|-----|------|
| `identical` | 5 | 全部为含 DOI/URL 的条目（[J/OL]、[EB/OL]、[DS/OL] 类） |
| `type-marker-group-dropped` | 21 | citeproc-py 把 `[文献类型标识/载体标识]` 组整体丢弃：CSL 中该组为 `entry-type-id` + `entry-medium-id` 两个子节点，只要载体（OL）为空，citeproc-py 连 [J]/[M]/[D] 一起抑制。**这违反 CSL group 语义**（group 应仅在全部子节点为空时抑制），是 citeproc-py 的引擎级缺陷 |
| `type-marker-dropped+other` | 1 | en-book-edition：除丢 [M] 外，版本项渲染为 "2nd 版"（pandoc 为 "2 版"），序数词与中文标签混排 |
| `spurious-version-label` | 1 | zh-dataset：`version` 变量为空，citeproc-py 仍输出其 short 标签 "V."；pandoc 正确抑制 |

两引擎的共同行为（非差异，但影响 GB/T 符合性）：

- 均**不按条目语言切换 locale**：`langid={english}` 的西文条目同样输出 "等"（4 著者截断本身正确触发）与全角标点（，：（））。实证：pandoc 渲染 `en-article-etal` 为 "Smith J，Doe J，Roe R，等. …"。
- pandoc 对含 DOI/URL 的条目一律附加载体标识 `/OL`（印刷期刊文章含 DOI → [J/OL]）。是否符合 GB/T 7714-2025 对"纯 DOI 期刊文章"的要求，已在 golden 中标 `pending-human-review`。

citeproc-py 附带诊断（`results/citeproc_py.json` → `native_bibtex_source_diagnostic`）：
其**自带 BibTeX source 对本 corpus 直接崩溃**（`KeyError: 'collection'`）；且其字段映射表
（`.venv/.../citeproc/source/bibtex/bibtex.py`）不含 `url`/`urldate`/`school`/`translator`/
`langid`/`date` 等字段，`incollection` 被错映射为 article-journal。结论：选 citeproc-py
必须另配 BibTeX→CSL JSON 前端（本 spike 用 pandoc 承担）。

## 4. pandoc BibTeX 前端的表达力限制（实证）

以 .bib 为唯一输入时，以下 GB/T 类型**无法**经 pandoc BibTeX 阅读器到达正确 CSL type：

| corpus 条目 | BibTeX 类型 | pandoc 产出 CSL type | 渲染标识 | 目标 |
|------------|------------|---------------------|---------|------|
| standard-gb | @standard | legislation | [Z] | [S] |
| zh-map | @map | （空） | [Z] | [CM] |
| collection-g | @collection | book | [M] | [G]（且 2025 官方 CSL 本身无 [G] 分支） |
| zh-archive | @unpublished | manuscript | [A] ✓ | [A]（但 archive/收藏地字段被 pandoc 丢弃，收藏信息无法著录） |

其余类型映射正常：article→article-journal [J]、book→book [M]、incollection→chapter [M]//、
inproceedings→paper-conference [C]//、entrysubtype=newspaper→article-newspaper [N]、
mastersthesis/phdthesis→thesis [D]、techreport/report→report [R]、patent→patent [P]、
online→webpage [EB/OL]、dataset→dataset [DS]。

其他前端事实：`@misc` 产出空 CSL type（不可用）；`eprint`/`medium` 字段被丢弃；
会议 `eventtitle` 被映射为 CSL 1.0.1 的 `event` 而非 2025 样式使用的 `event-title`
（本 corpus 的会议条目都带 booktitle，走的是样式的 container-title 分支，未受影响）。

## 5. 手写 Gbt7714Formatter 差距清单

`render_thesisforge.py` 结果：**28 条中 16 条可渲染，12 条失败**。

失败明细（原因来自 loader 自身异常）：

- 11 条 `UnsupportedBibliographyTypeError`：incollection×2、collection、techreport、standard、
  patent、online×2、dataset、map、unpublished；
- 1 条 `MissingBibliographyFieldError`：zh-newspaper（@article 用 biblatex `date` 而非 `year`）。

16 条可渲染条目与 pandoc 输出的结构化差异（`results/comparison.json` → `checks`）：

| 差异 | 涉及条目数 | 示例 |
|------|-----------|------|
| 半角标点（,.:()）vs CSL 全角（，：（）） | 16/16 | `中华放射学杂志, 2024, 58(3):` vs `中华放射学杂志，2024，58（3）：` |
| 无 "等/et al" 截断（>3 著者全部列出） | 3 | zh-article-etal 5 著者全列；pandoc "刘洋，赵敏，孙建国，等." |
| 丢版本项 | 1 | en-book-edition 无 "2 版" |
| 丢译者 | 1 | zh-book-translator 无 "周琪，刘绯，译." |
| 无载体标识 /OL | 3 条含 DOI | [J] vs [J/OL]（是否符合标准待人工确认） |
| 缺卷号时输出 "年, (期)" | 1 | "2023, (6)" vs "2023（6）" |

手写 formatter 并非处处落后：**西文著者姓全大写**（"KUHN TS"）与 GB/T 7714-2015
对欧美著者"姓的字母全大写"的要求一致，而官方 CSL 样式不做大写转换（"Kuhn T S"）。
2025 版标准对应条款需人工核对后定论（已在 golden 复核策略中标注）。

## 6. Golden 初校结果

`golden/gbt7714-golden-v1.json`：以 pandoc 输出为初始 golden，28 条全部结构完整
（序号、著者、题名、类型标识、出处、年卷期页机器校验通过 19 条），
**9 条标 `review: pending-human-review`**，原因分布：

- 3 条 [J/OL] 载体标识疑义（含 DOI 的印刷期刊文章是否应标 /OL）；
- 2 条西文条目用 "等" 而非 "et al"（CSL default-locale 固定 zh-CN 所致）；
- 3 条类型标识不符：collection-g（[M]≠[G]）、standard-gb（[Z]≠[S]）、zh-map（[Z]≠[CM]）；
- 1 条 zh-dataset [DS/OL] 载体标识疑义。

该 golden 独立于 `tests/fixtures/bibliography/gbt7714-v1.json`（5 类型手写 golden，未改动）。

## 7. 对 ADR-0004 的建议回答问题清单

1. **是否引入 CSL 管线？** 实证支持引入：手写 formatter 仅覆盖 5/14 类场景且存在
   "等"截断、版本、译者、标点体系等系统性差距；pandoc --citeproc 对 28 条语料全部渲染成功。
2. **选哪个 CSL 引擎？** pandoc（Haskell citeproc）28/28 结构正确；citeproc-py 0.10.7
   同输入下 23/28 与 pandoc 不一致，且存在 group 抑制（丢类型标识）与 label 抑制两个
   引擎级缺陷。若因"纯 Python、无外部进程"约束必须选 citeproc-py，需先接受：
   自研 BibTeX→CSL JSON 前端（其自带 source 对本 corpus 崩溃）+ 修复或绕过上述缺陷
   （fork？上游贡献？后处理补丁？各自的维护成本）。
3. **pandoc 的集成形态？** pandoc 是外部可执行文件，与"本地优先、确定性"兼容
   （无网络、无 API Key），但引入运行时依赖与打包复杂度（sidecar/系统依赖检测）。
4. **2025 vs 2015 标准版本策略？** 官方仓库已有 2025 三件套（本 spike 用 numeric）。
   但 2025 官方 CSL 无 [G] 分支、[S]/[CM] 无法从 BibTeX 表达——接受兜底（[M]/[Z]）、
   扩展输入格式（CSL JSON 直传）、还是自维护 CSL fork（CC-BY-SA-3.0，需署名+相同许可）？
5. **中西文混排怎么办？** 两个标准 CSL 引擎都不按条目语言切换 "等/et al" 与标点。
   选项：接受全中文 locale 输出 / 改用社区 bilingual 样式变体 / 渲染后处理。
   需要产品层先定义 ThesisForge 的目标读者期望。
6. **输入格式是否仍限 BibTeX？** [S]/[CM]/[A] 收藏信息、载体标识等需要
   BibTeX 之外的通道（biblatex 扩展字段已部分缓解；CSL JSON 是更完整的选择）。
7. **手写 formatter 去留？** 若引入 CSL 管线，建议降级为无 CSL 环境下的受限兜底
   或彻底移除；其唯一相对优势（西文姓全大写）可作为 CSL 后处理或自定义宏保留。
   注意 `docs/BIBLIOGRAPHY_SPEC.md` 已声明 V1 格式合同是受限子集、未来可替换为
   本地 CSL/citeproc backend——本 spike 为该替换提供决策依据。
8. **golden 如何进入回归？** 建议将 9 条 pending-human-review 人工定稿后，
   把 `golden/gbt7714-golden-v1.json` 固化为引擎回归基线（现状它与既有
   `tests/fixtures/bibliography/gbt7714-v1.json` 互不干扰）。

## 8. 复现步骤

```bash
cd spikes/phase0/citation
../../../.venv/bin/python render_pandoc.py        # -> results/pandoc.json
../../../.venv/bin/python render_citeproc_py.py   # -> results/citeproc_py.json
../../../.venv/bin/python render_thesisforge.py   # -> results/thesisforge.json
../../../.venv/bin/python compare.py              # -> results/comparison.{json,md}
../../../.venv/bin/python build_golden.py         # -> golden/gbt7714-golden-v1.json
```

## 9. 局限声明

- golden 的"机器初校"只做结构完整性检查（序号/著者/题名/标识/出处/年卷期页），
  不判断著录细节是否符合 GB/T 7714-2025 原文条款；9 条 pending 条目需持标准文本人工定稿。
- 西文著者大小写、[J/OL] 载体标识两处"哪边符合标准"本报告不下结论，只呈现两引擎行为差异。
- corpus 为合成条目，未覆盖：多卷书卷次、专利公告日期全格式、会议 event-title 分支
  （pandoc 前端字段名不匹配）、连续出版物整体著录。
