# Phase 0 spike 报告：reference.docx 样式来源 + shell.docx 锚点合并

> 目的：为 ADR-0002（Template Package v2 是否采用「YAML + reference.docx + shell.docx」
> 替代单 YAML）提供实证事实。全部产物在 `spikes/phase0/docx-template/`，脚本可重复运行。
> 数据出处：`output/reference-summary.json`、`output/shell-summary.json`、`output/merge-report.json`。

## 0. 产物清单

| 产物 | 生成脚本 | 校验 |
| --- | --- | --- |
| `package-sample/reference.docx` | `build_reference.py` | openxml_validate 13/13 |
| `output/reference-inheritance.docx` | `build_reference.py`（继承验证） | openxml_validate 13/13 |
| `package-sample/shell.docx` | `build_shell.py` | openxml_validate 13/13 + soffice 转 PDF 通过 |
| `output/compiled.docx` | `merge_into_shell.py`（完整管线，不走 finalizer） | — |
| `output/merged.docx` | `merge_into_shell.py` | openxml_validate 13/13 + soffice 转 PDF 通过（372,941 字节） |
| `package-sample/`（template.yaml / provenance.yaml / fixtures/minimal / README） | 手工 | 按 spec §3 最小包 + 可选 shell.docx |

## 1. 路线①实证：reference.docx 作为样式/主题/页面设置来源

做法：以 HUT 学校 YAML 为蓝本，用 python-docx 从默认包出发编程注入学校样式与页面设置，
正文留空（仅 body 级 `sectPr`），再以 `Document('reference.docx')` 为底新建文档验证继承。

### 1.1 可行的部分（已实证）

- **样式继承**：TF Body / TF Heading 1-4 / TF Abstract / TF Bibliography / TF Figure Caption /
  TF Table Caption / TF Equation / TF Code Char 共 12 个样式全部随包携带，
  新文档可直接 `add_paragraph(..., style='TF Body')` 使用，openxml 校验通过。
- **页面设置继承**：A4、左 30mm / 右 25mm / 上下 25mm、页眉 15mm、页脚 17.5mm、
  docGrid `lines` linePitch 400（20pt）全部落在 sectPr 中随包继承。
- **页眉页脚继承**：默认页眉（校名 + 0.5pt 下边框）与页脚（PAGE 域）作为独立部件继承。
- **fontTable/theme 随包携带**：fontTable 登记了宋体/黑体；theme1.xml 沿用 python-docx
  默认主题。实证：theme 的 major/minor latin 字体仍是 Calibri/Cambria，但 styles.xml 中
  **没有任何样式再引用 theme 字体属性**（所有 rFonts 均为显式值），且 docDefaults 已改写为
  宋体/Times New Roman —— theme 字体对本模板是惰性的，不构成阻塞。
- **python-docx 默认包不含 TF 样式**（`default_template_has_tf_styles=false`），
  即 reference.docx 确实是样式的唯一来源，不是默认包碰巧提供。

### 1.2 限制与坑（已实证）

1. **`Document(path)` 是就地编辑**：`document.save()` 不带参数会覆盖 reference.docx 本体。
   作为模板使用必须先复制或另存（本 spike 均显式另存）。
2. **python-docx API 缺口**：
   - `fontTable.xml`、`theme1.xml` 被加载为普通 `Part`（无 `_element`），
     必须经 `part.blob` 反序列化/回写（本 spike 初版在此踩坑，`AttributeError`）；
   - `w:pgNumType`（页码格式/重启）无公开 API，需直接操作 sectPr XML，
     且必须按 schema 顺序插入（pgNumType 在 cols/docGrid 之前），否则 Word 可能修复提示；
   - 书签（bookmarkStart/End）无公开 API，需手工插元素，且 bookmarkStart 必须位于 pPr 之后。
3. **样式会被渲染器改写**：实证 `configure_styles()` 会把 YAML 值直接写进同名样式
   （Normal 的 firstLineIndent 从 None 被改写为 480 twips）。
   **reference.docx 与 YAML 并存时必须显式定义优先级**——这是 ADR-0002 必须回答的问题。
4. **docDefaults/latentStyles 属于包级单例**：多来源合并时只能保留一份，不能叠加。

结论：**路线①成立**。reference.docx 可以完整承担「styles/theme/fontTable/page setup/
header-footer/numbering base」来源职责；python-docx 的 API 缺口需要用少量
底层 XML 工具函数补齐，工作量可控。

## 2. 路线②实证：编译产物合并进带锚点的 shell.docx

### 2.1 合并策略（本 spike 的选择）

- shell.docx：两个 section（front：封面/声明/目录，lowerRoman 从 1；main：仅 tf_body
  锚点空段落，decimal 从 1 重启，独立页眉页脚），另含 tf_toc 锚点与一张占位 logo
  （rId11 → media/image1.png）。
- compiled.docx（examples/complete-thesis + HUT 模板，管线直出无 finalizer）正文 71 个
  子节点：[封面 13 个] + 封面分节符 + [前置内容 9 个（摘要/Abstract/目录域）] +
  前置分节符 + [正文 48 个] + final sectPr。
- **节点选取**：丢弃 compiled 封面区与其分节符（封面/声明由 shell 持有），
  导入其后的 57 个节点；**丢弃 compiled 的 final sectPr**（正文节属性由 shell 的
  main sectPr 接管）。插入位置：tf_body 锚点段落之前，随后移除锚点段落（书签对一并移除）。
- 合并结果 3 个 sectPr：`lowerRoman(1)`（shell 前置，证明 shell 节保留）→
  `upperRoman(1)`（compiled 前置，证明导入节保留）→ `decimal(1)`（shell 正文，证明
  shell 正文节接管导入正文）。

### 2.2 必须显式搬运的清单（实证台账）

| 对象 | 实证事实 | 本 spike 策略 |
| --- | --- | --- |
| **relationships（r:id/r:embed）** | 导入节点引用 5 个 rId（前置节页眉页脚 4 个 + 插图 1 个）；与 shell 既有 rId **必然冲突**（双方同出 python-docx 默认包的 rId 序列） | 全部重映射为新 rId（rId11→rId14 … rId21→rId18），目标部件复制进包 |
| **部件名冲突** | compiled 的 header2.xml/footer2.xml/media/image1.png 与 shell 既有部件**同名**，直接覆盖会损毁 shell 内容 | 按数字后缀递增重命名（header3.xml、footer3.xml、image2.png…），rels Target 同步改写 |
| **footnotes part** | shell（源自 python-docx 默认包）**无 footnotes.xml**；compiled 有（footnoteReference id=1，按 w:id 关联而非 r:id） | 整体搬运 footnotes.xml + 登记 relationship（rId19）+ Content Types Override；w:id 无需重映射（id 空间不冲突） |
| **styles** | 导入内容引用 14 个样式；闭包（含 basedOn/next/link）后 22 个；其中 **8 个与 shell 冲突**：Normal、Heading1-3 及各自 Char、DefaultParagraphFont | 闭包最小搬运；冲突 **compiled 胜出**（替换 shell 同名定义），9 个 TF* 样式纯新增；shell 的 docDefaults/latentStyles 不动 |
| **numbering.xml** | 导入内容引用 numId 10/11；shell 正文**无 numId 引用** | compiled numbering.xml 整体替换 shell 默认 numbering.xml（shell 未引用，零风险） |
| **[Content_Types].xml** | 新增 header/footer/footnotes 部件需要 Override（Default 不覆盖其 content type）；png 由 Default 覆盖 | 从 compiled CT 复制对应 Override 并改写为新部件名 |
| **settings/theme/fontTable/docProps** | compiled settings 含 evenAndOddHeaders 等 | **不合并，保留 shell 的**（记录为 ADR 决策点，见 §4） |

### 2.3 「shell 处理保留 relationships / styles / sections」是否成立

**成立**，证据：

- relationships：shell 既有 13 条 rel 全部原样保留（只增不改），logo 的 rId11 与
  目标 media/image1.png 未受影响；导入内容的 rId 全部走新号段。
- styles：shell 独有样式（TF Body 等 12 个）全部保留；冲突项按策略被 compiled 定义替换
  —— 属于**策略选择**而非丢失，且台账完整记录 8 个冲突。
- sections：shell 两个 sectPr 的页码格式/重启值/页眉页脚引用逐项断言保留
  （front lowerRoman、main decimal + 独立页眉「湖南工业大学硕士学位论文」）；
  tf_toc 锚点保留且唯一；openxml_validate 的书签配对/field 配对检查通过。
- 附带实证：合并产物经 soffice 无头转 PDF 成功（372,941 字节），LibreOffice 可无修复打开。

两个需要说明的副作用：

1. **冲突样式 compiled 胜出会回流影响 shell 前置页**：例如 compiled 的 Normal 带
   firstLineIndent=480，替换后 shell 封面占位段落也会出现首行缩进。样例可接受；
   正式版需要 token 映射或 shell-wins 白名单（见 §4）。
2. **settings 不合并意味着 compiled 的 evenAndOddHeaders 失效**：本例 compiled 前置节
   页眉本就为空（HUT YAML 前置节不启用页眉），无实际影响；但若学校规范要求奇偶页眉，
   settings 归谁持有必须决策。

## 3. 合并的坑（实证清单）

1. **rId 冲突是必然事件，不是边界情况**：两边都源自 python-docx 默认包，rId1-8 段完全
   重叠；任何合并实现都必须有 rId allocator + 属性重映射，不能只拷部件。
2. **部件名冲突同理**：header2.xml/image1.png 这类机器命名必然撞车，必须有
   part-name allocator（本 spike 用数字后缀递增）。
3. **final sectPr 必须显式丢弃**：compiled 的 body 级 sectPr 若一并导入，会用 compiled 的
   正文节属性（含 6 个页眉页脚引用）覆盖 shell 的 main section 设计。
4. **锚点消费要成对清理书签**：移除锚点段落时 bookmarkStart/bookmarkEnd 必须一起移除，
   否则 bookmark_pairing 校验失败。
5. **sectPr 子元素有 schema 顺序**：pgNumType 插入位置不对会导致 Word 修复提示
   （本 spike 在 build_shell.py 中用 successors 列表显式保证）。
6. **部件级 rels 递归是未覆盖边界**：若被搬运的 header/footer 内部再引用图片
   （word/_rels/headerN.xml.rels），需要递归搬运并重映射部件内部 r:id。
   本 spike 数据未触发（compiled 页眉页脚均无部件级 rels），代码显式
   `NotImplementedError` 拦截，不静默出错。
7. **双侧占用 id 空间是未覆盖边界**：shell 已有 footnotes 或已引用 numId 时，
   需要 w:id/numId 重映射合并，本 spike 同样显式拦截。

## 4. PackageEditor 设计建议要点

1. **以 OPC 包操作为核心，不要依赖 python-docx 文档模型做合并**。python-docx 没有跨包
   合并 API，且 fontTable/theme 等部件只暴露 blob；PackageEditor 应直接操作 ZIP 条目 +
   lxml，python-docx 仅用于「以 reference.docx 起建新文档」这类单包场景。
2. **显式 carry-list + 台账落盘**：每次合并输出本报告 §2.2 那样的搬运台账
   （rId 映射、部件重命名、样式冲突、未搬运项），供 lint 与排障使用。
3. **region → anchor 映射协议**：本 spike 用「首个分节符之后全部导入 tf_body」近似，
   导致 compiled 的摘要/目录域整体落在 shell 的 main 区之后（前置节重复 roman 重启）。
   正式版 Compiler 应输出 region 边界 manifest（cover/front_matter/main/back_matter），
   PackageEditor 按 `word.anchors` 分槽投递：front_matter → shell 前置区、
   main/back_matter → tf_body、目录域 → tf_toc。
4. **样式冲突策略归模板**：v2 §7 的 style token 应作为合并键——同名不同源的样式按
   token 对齐后二选一（建议 shell-wins 为默认，compiled-wins 仅用于 lint 诊断比对），
   并在 template lint 中报出 token 无映射的冲突。
5. **numbering/footnotes 重映射表**：实现 numId 与 footnote w:id 的双侧重映射
   （本次未触发的两条 `NotImplementedError` 路径），并纳入 L3 Word 资产 lint。
6. **settings/theme/fontTable 合并策略显式化**：建议 shell 持有 settings 与 theme，
   reference.docx 持有 fontTable 基线，compiled 的 settings 仅取白名单字段
   （如 evenAndOddHeaders 是否并入由 shell 的 section policies 决定）。
7. **校验闭环**：合并后必须跑 openxml_validate（本 spike 13/13）+ 目标应用冒烟
   （soffice 转 PDF）+ spec §19 L3 锚点/样式/relationship 检查；缺失 body anchor
   按 spec 为阻断错误（本 spike 已实现为 SystemExit）。
8. **确定性与幂等**：allocator 采用「最大编号 +1」的确定性规则，相同输入产出相同
   合并结果（zip 时间戳除外）。

## 5. 给 ADR-0002 的建议回答问题清单

1. reference.docx 与 YAML 重复定义同一属性（如正文首行缩进）时，优先级是什么？
   （实证：渲染器 configure_styles 会无条件改写同名样式。）
2. styles 冲突的默认策略：shell-wins、compiled-wins 还是按 style token 映射对齐？
   token 无映射时 lint 级别是 error 还是 warning？
3. settings.xml（evenAndOddHeaders、updateFields 等）由谁持有？compiled 的 settings
   字段是否有白名单并入机制？
4. numbering.xml 与 footnotes.xml 在双侧都被占用时的 id 重映射算法与验证规则？
5. Compiler 是否输出 region manifest 供 PackageEditor 做 anchor 分槽？tf_toc 锚点的
   投递物是 TOC 域还是静态目录？
6. 导入内容中的内部 sectPr（如 compiled 前置节）保留原样，还是应按 shell 的
   section policies 重写（页码格式、页眉页脚引用）？
7. 锚点被消费后是移除（本 spike 选择）还是保留以便二次合并/增量构建？
8. 部件级 rels 递归搬运的支持范围：header/footer 内图片是否属于 v2 必须项？
9. spec 的 external_relationships: forbid / macro_policy: forbid 在 PackageEditor 哪一层
   强制执行（合并前 lint 还是合并时拦截）？本 spike 在合并时拦截外部 rel。
10. 合并产物是否仍需 finalizer（LibreOffice 刷新域/页码缓存）？顺序是
    「编译 → 合并 → finalizer」还是「编译 → finalizer → 合并」？

## 6. 复现命令（仓库根目录）

```bash
.venv/bin/python spikes/phase0/docx-template/build_reference.py
.venv/bin/python spikes/phase0/docx-template/build_shell.py
.venv/bin/python spikes/phase0/docx-template/merge_into_shell.py
.venv/bin/python qa/tools/openxml_validate.py spikes/phase0/docx-template/output/merged.docx
```

## 7. 已知边界（本 spike 显式不覆盖）

- 部件级 rels 递归搬运（header/footer 内嵌图片）：`NotImplementedError` 显式拦截。
- shell 已引用 numId / 已有 footnotes 部件时的 id 重映射合并：同上。
- merged.docx 未过 finalizer（LibreOffice 域刷新）；TOC 域页码缓存为编译时态。
- shell 封面沿用 reference.docx 默认页眉（正式模板通常封面无页眉）——样例从简。
