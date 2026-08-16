# ThesisForge V1 Risk Register

> 状态：Living Document  
> 更新日期：2026-08-15（Phase 0 回写，见 §6）

## 1. 使用方式

每个风险应包含：

- ID；
- 分类；
- 概率；
- 影响；
- 触发信号；
- 预防措施；
- 应急/退路；
- owner；
- 目标决策阶段；
- 当前状态。

概率/影响建议使用 `Low / Medium / High / Critical`。任何 High/Critical 风险没有 owner 和缓解措施时，不允许进入 Beta。

---

## 2. 风险总览

| ID | 风险 | 概率 | 影响 | 当前等级 | 首要处理阶段 |
|---|---|---:|---:|---:|---|
| R-001 | 正则 Parser 无法支撑完整学术 Markdown | High | Critical | Critical | Phase 0–2 |
| R-002 | Pandoc 二进制分发和多平台兼容复杂 | Medium | High | High | Phase 0 |
| R-003 | SourceMap 不完整导致诊断无法定位 | Medium | High | High | Phase 0–2 |
| R-004 | 纯 YAML 无法表达真实学校 Word 模板 | High | Critical | Critical | Phase 0–3 |
| R-005 | shell/reference DOCX 合并破坏 relationships/sections | Medium | Critical | Critical | Phase 0–5 |
| R-006 | Word 字段首次打开为空或未刷新 | High | High | High | Phase 0、7 |
| R-007 | 分页依赖 Word 布局引擎，跨软件结果不同 | High | High | High | Phase 0、9 |
| R-008 | LaTeX → OMML 覆盖不足 | Medium | Critical | Critical | Phase 0、6 |
| R-009 | 复杂表格模型与 Word 行为不一致 | High | High | High | Phase 2、6 |
| R-010 | GB/T 7714-2025 输出不符合真实学校要求 | Medium | Critical | Critical | Phase 0、8 |
| R-011 | citeproc Provider 特性不足或行为差异 | Medium | High | High | Phase 0、8 |
| R-012 | 模板数量增加后 Renderer 出现学校特例分支 | High | Critical | Critical | Phase 3–9 |
| R-013 | 字体缺失造成分页和版式漂移 | High | High | High | Phase 0、3、9 |
| R-014 | WPS/LibreOffice 对 OOXML 字段支持差异 | High | Medium | High | Phase 0、7、9 |
| R-015 | DOCX 包合法但 Word 仍提示修复 | Medium | Critical | Critical | Phase 5–9 |
| R-016 | 测试只检查文件存在，不能发现语义错误 | High | Critical | Critical | Phase 0–9 |
| R-017 | Golden/视觉基线过脆，维护成本过高 | Medium | Medium | Medium | Phase 9 |
| R-018 | 多文件 include 和 ID 顺序不确定 | Medium | High | High | Phase 1–4 |
| R-019 | 构建不确定，难以复现和比较 | Medium | High | High | Phase 4–10 |
| R-020 | 模板包引入路径穿越、宏或外部关系 | Medium | Critical | Critical | Phase 3、9、10 |
| R-021 | 大图片/大论文导致内存和速度失控 | Medium | High | High | Phase 0、6、9 |
| R-022 | UI 过早开发导致 Core API 被界面绑死 | High | High | High | Release planning |
| R-023 | AI 进入编译链路破坏确定性和隐私 | Medium | Critical | Critical | V1.2 |
| R-024 | 第三方代码或 CSL 样式许可证不清 | Medium | High | High | Phase 0、8、10 |
| R-025 | 学校规范本身模糊或不同学院冲突 | High | High | High | Phase 0、3 |
| R-026 | 模板 schema 演进造成旧模板静默失真 | Medium | High | High | Phase 3、10 |
| R-027 | 自动 finalizer 依赖 Office 安装/授权 | Medium | High | High | Phase 0、7、10 |
| R-028 | LibreOffice 视觉回归与 Word 权威结果不一致 | High | Medium | High | Phase 9 |
| R-029 | 诊断码和 JSON contract 在 V1 前频繁破坏 | Medium | Medium | Medium | Phase 4、10 |
| R-030 | 需求扩张为“支持所有论文类型” | High | Critical | Critical | Product governance |

---

## 3. 详细风险

## R-001 — Parser 架构不足

**描述**：当前正则 Parser 在加入脚注、嵌套容器、复杂行内、表格和多文件后迅速失控。

**触发信号**：

- Renderer 开始重新解析 `Paragraph.text`；
- 同一语法需要多个正则补丁；
- source line 经常不准确；
- 未知语法静默退化；
- Parser bug 数量随功能呈指数增长。

**预防**：

- Phase 0 完成 Parser backend spike；
- 使用成熟 AST 后端；
- 建立 ParserBackend 协议；
- 规范、fixture、AST snapshot 一一对应。

**退路**：

- 受限模式只支持明确子集并对其他语法报错；
- 不允许继续以正则补丁掩盖架构问题。

**Gate**：Engineering Preview 前关闭选型。

## R-002 — Pandoc 分发复杂

**描述**：若选择 Pandoc，需处理多平台二进制、体积、更新、签名和离线安装。

**触发信号**：

- 安装失败率高；
- 用户系统 Pandoc 版本行为不一致；
- 二进制体积超出产品接受范围；
- 打包许可或供应链审核未完成。

**预防**：

- 固定并验证版本；
- `doctor` 检测；
- 可选择 bundled/system 两种模式；
- 记录哈希和来源；
- 在 Phase 0 评估 markdown-it-py fallback。

**退路**：

- 只支持已验证的 system Pandoc；
- 或使用纯 Python 后端，但需重新评估功能范围。

## R-003 — SourceMap 不完整

**描述**：第三方 AST 或 include 处理后，诊断无法回到正确源文件和行列。

**预防**：

- 技术试验必须把 SourceMap 作为 P0 验收，而不是附加能力；
- source span 贯穿 Normalized/Resolved IR；
- 变换时保留 origin chain；
- 对 generated nodes 标记 generated origin。

**退路**：

- 降级到块级位置，但必须明确显示“位置近似”；
- 不允许返回错误文件或误导性行号。

## R-004 — 纯 YAML 模板表达力不足

**描述**：复杂学校封面、声明页、页眉页脚和 Word 样式无法稳定用 YAML 重建。

**预防**：

- Template Package v2；
- `reference.docx`；
- 可选 `shell.docx`；
- YAML 仅表达规则和映射。

**退路**：

- 对复杂前置页采用受控 shell anchors；
- 不将 YAML 扩展成任意 OOXML DSL。

## R-005 — DOCX 壳体合并破坏包结构

**描述**：插入正文、清理 placeholder、复制节点时可能遗漏 relationships、styles、numbering、headers、media。

**预防**：

- 设计统一 PackageEditor；
- 对每种 part 建立 relationship-aware API；
- 使用 OpenXML validator；
- shell fixture 覆盖页眉、图片、表格、section 和 content controls。

**退路**：

- Alpha 只使用 reference.docx；
- shell.docx 暂作为 Beta 能力；
- 对不支持的 shell 特性报错，不做部分合并。

## R-006 — 字段未刷新

**描述**：纯生成字段代码不等于有正确显示结果，TOC/REF/PAGE 可能为空或旧值。

**预防**：

- 写 cached result；
- 写 update-on-open/dirty；
- build report 记录字段状态；
- finalizer profiles；
- Word 人工/自动验证。

**退路**：

- draft 明确提示打开后更新；
- final-word 作为权威最终件路径；
- 不以普通文本替代字段。

## R-007 — 分页差异

**描述**：分页由字体、渲染引擎、Office 版本和打印机设置共同影响。

**预防**：

- 定义 Word 主基准；
- 字体探测和固定；
- 关键模板在权威环境 finalization；
- 视觉自动化只做回归预警；
- 兼容矩阵说明允许差异。

**退路**：

- 对最终提交要求使用 `final-word`；
- LibreOffice 仅作为 preview；
- 发布说明不承诺跨引擎像素一致。

## R-008 — OMML 覆盖不足

**描述**：复杂 LaTeX 命令可能不能转换或转换后在 Word 中不正确。

**预防**：

- 代表性公式 corpus；
- 选择成熟转换后端；
- inline/block 分开测试；
- Word 可编辑性人工检查；
- 明确 supported subset。

**退路**：

- 对不支持公式阻断 build 或允许显式 image fallback；
- image fallback 不得静默开启。

## R-009 — 复杂表格

**描述**：Markdown 表格模型通常不能表达合并、重复表头、跨页、横向页面等论文要求。

**预防**：

- StructuredTable 独立模型；
- 定义 simple/extended table syntax；
- 结构化诊断超宽、合并冲突；
- Phase 0/2 明确复杂表格范围。

**退路**：

- V1 限制到明确子集；
- 提供 raw OOXML/embedded docx 不是首选，若提供必须受控和隔离。

## R-010 — GB/T 7714-2025 正确性

**描述**：标准实施时间新，学校可能仍有 2015 或自定义要求，CSL 样式也可能持续修订。

**预防**：

- 固定标准版本；
- 保留 2015 compatibility profile（是否进入 V1 由需求决定）；
- 20–30 文献类型 golden corpus；
- 人工审校；
- template override；
- citation style hash/provenance。

**退路**：

- 不宣称“完全符合”未经审校的边界类型；
- 已知差异进入模板文档；
- Provider 可替换。

## R-011 — citeproc Provider 局限

**描述**：候选 Provider 可能缺少 disambiguation、collapse 等特性或格式行为差异。

**预防**：

- Provider interface；
- Phase 0 对比 Pandoc citeproc 与 citeproc-py；
- 以项目 golden corpus 为准；
- 不直接暴露 provider-specific 对象。

**退路**：

- 切换 provider；
- 对不支持的 citation feature 给出诊断；
- 将范围限制写入 V1 spec。

## R-012 — 学校特例污染 Renderer

**描述**：为了快速支持模板，在 Renderer 中出现 `if school == ...`。

**触发信号**：

- core 代码出现学校名称或模板 ID；
- 新学校需要修改 compiler/renderer；
- 模板字段无法表达差异而直接加分支。

**预防**：

- CI 静态检查敏感模板 ID；
- style token/section policy/numbering policy；
- 每个特例先判断是否为通用语义；
- Template Package review。

**退路**：

- 将真正通用能力升级为 schema；
- 不可通用能力以受控 extension provider 实现，不能散落条件分支。

## R-013 — 字体缺失

**描述**：缺少宋体、黑体、Times New Roman 等会引起字宽和分页变化。

**预防**：

- `doctor`；
- primary/fallback policy；
- template package 声明字体；
- CI 使用固定字体镜像；
- build manifest 记录实际字体。

**退路**：

- final profile 对关键字体缺失直接报错；
- draft profile 可警告并使用声明 fallback。

## R-014 — WPS/LibreOffice OOXML 差异

**描述**：字段、OMML、样式继承或页眉页脚行为可能不同。

**预防**：

- 支持等级分级；
- 三应用矩阵；
- 尽量使用标准 OOXML；
- 避免依赖 Word 私有扩展，若使用则记录。

**退路**：

- Word 为主基准；
- WPS/LibreOffice 的差异列为已知限制；
- 关键 finalization 不由 LibreOffice 替代 Word。

## R-015 — Word 修复提示

**描述**：OpenXML schema 通过仍可能存在 Word 特有一致性问题。

**预防**：

- OpenXML validation + Word open test；
- 增量构建 corpus；
- field/bookmark/relationship pairing；
- 从已验证 template shell 开始；
- 保存 Word repair log 作为 S1 缺陷证据。

**退路**：

- 阻断 release；
- 二分定位 DOCX parts；
- 不允许以“能修复后打开”作为通过。

## R-016 — 测试层次过浅

**描述**：只检查文件存在或文本出现，无法识别字段、关系和版式错误。

**预防**：

- 六域质量体系；
- XPath/relationship tests；
- visual/compatibility evidence；
- release gate。

**退路**：

- 暂停功能扩张，补齐 fixture 和门禁。

## R-017 — 基线过脆

**描述**：整份 XML/PDF 像素比较产生大量无意义差异。

**预防**：

- semantic XPath；
- XML normalization；
- 视觉区域、mask 和容差；
- 区分 Word authority 与 LibreOffice regression。

**退路**：

- 将不稳定部分降级为人工 check；
- 不通过扩大 ignore 区域掩盖真实回归。

## R-018 — 多文件顺序/ID

**描述**：include glob、文件系统顺序和跨文件引用可能不确定。

**预防**：

- manifest 显式顺序；
- 禁止隐式无序 glob 或对 glob 稳定排序；
- 全局 symbol table；
- source origin chain。

**退路**：

- Alpha 仅单文件；
- 多文件在 Beta 前完成，不做半支持。

## R-019 — 构建不确定

**描述**：时间戳、关系 ID、ZIP 顺序、随机 ID 导致每次输出不同。

**预防**：

- stable IDs；
- deterministic traversal；
- package normalization；
- reproducible profile；
- manifest hashes。

**退路**：

- 先保证 semantic manifest 一致；
- 对 Office 自动写入的不可控元数据明确 allowlist。

## R-020 — 模板包安全

**描述**：DOCX/ZIP 可携带宏、外部关系、嵌入对象和路径攻击。

**预防**：

- 宏禁止；
- external relationship allowlist；
- ZIP safety；
- package size limits；
- signature/hash；
- provenance；
- sandbox extraction。

**退路**：

- 拒绝不安全模板；
- 不提供“忽略安全警告继续”默认选项。

## R-021 — 大文档性能

**描述**：图片、XML 拼接、反复遍历和 finalizer 导致高内存/慢构建。

**预防**：

- phase timing；
- streaming/one-pass where safe；
- image dedup；
- caching；
- stress corpus；
- 性能 profile。

**退路**：

- 清晰的资源限制和诊断；
- 对预览降采样，但最终 DOCX 不静默降质。

## R-022 — UI 过早

**描述**：UI 直接调用内部对象，迫使 Core API 为界面妥协。

**预防**：

- UI 后置；
- service facade；
- CLI/JSON contract 先稳定；
- UI 与 CLI E2E 一致性测试。

**退路**：

- 暂停 UI 功能，将逻辑迁回 Core service。

## R-023 — AI 破坏确定性/隐私

**描述**：AI 自动改稿、生成引用或上传全文，造成不可追踪和隐私风险。

**预防**：

- AI Proposal/Diff/Approval；
- provider permission；
- data minimization；
- no compiler dependency；
- citation verification；
- offline mode。

**退路**：

- 完全禁用 AI；
- Core build 不受影响。

## R-024 — 许可证

**描述**：参考代码、CSL 样式、学校 Logo/模板和字体可能有不同授权。

**预防**：

- THIRD_PARTY_NOTES；
- SPDX/SBOM；
- style attribution；
- template provenance；
- 发布前法律/合规审查。

**退路**：

- 移除不清晰资产；
- 只发布工具，不分发受限学校素材；
- 提供本地导入工具。

## R-025 — 学校规范冲突

**描述**：同校不同学院、年份和指导老师可能有冲突要求。

**预防**：

- 模板 ID 包含 document type/year/variant；
- provenance 记录依据；
- override 层；
- 不宣称“学校唯一标准”。

**退路**：

- 维护多个 variant；
- 用户显式选择；
- 将冲突记录到 README。

## R-026 — Schema 演进

**描述**：旧模板被新代码读取后产生无提示版式变化。

**预防**：

- schema_version；
- strict validation；
- explicit migration；
- compatibility range；
- resolved template snapshot。

**退路**：

- 拒绝不兼容 schema；
- 提供 migrate 和 rollback。

## R-027 — Finalizer 依赖

**描述**：Word COM/AppleScript 或 LibreOffice 依赖本地安装、授权、用户会话和平台。

**预防**：

- finalizer provider；
- draft 不依赖 finalizer；
- `doctor`；
- timeouts/isolated profiles；
- CI 使用明确环境。

**退路**：

- 生成字段 + cache + update-on-open；
- 用户手工 Word refresh；
- 不把 finalizer 失败伪装成成功 final build。

## R-028 — LibreOffice 视觉基线偏差

**描述**：自动视觉回归可能稳定，但与 Word 最终版式不同。

**预防**：

- 标注 rendering engine；
- 只用于相对回归；
- 关键 release 使用 Word 人工/自动 finalization；
- 分应用维护基线。

**退路**：

- 对高风险页面改为 Word screenshot evidence；
- 不使用 LO page count 作为唯一权威。

## R-029 — Contract 频繁破坏

**描述**：CLI、diagnostics、IR JSON 在开发期变化，影响 UI/CI 集成。

**预防**：

- `api_version`；
- Alpha 前标记 experimental；
- Beta 冻结；
- schema tests；
- deprecation policy。

**退路**：

- 提供版本协商或 adapter；
- breaking change 提升 major API version。

## R-030 — 范围失控

**描述**：项目被要求同时支持本科、硕士、博士、期刊、LaTeX、云协作、AI 和模板市场。

**预防**：

- Product Scope；
- P0/P1/P2；
- release gate；
- 新需求必须说明替换哪个现有优先级；
- 一个真实模板先闭环。

**退路**：

- 拆分 V1.1/V2；
- 保持核心扩展点，但不提前实现所有场景。

---

## 4. 风险评审节奏

- 每个 Phase Exit Gate 前评审一次；
- 新增 Critical 风险立即评审；
- RC 阶段每次候选构建评审；
- 已关闭风险保留历史；
- 缓解措施失败时升级等级；
- 风险豁免必须有 owner、理由、影响范围和到期日。

## 5. 风险关闭标准

风险不能因为“代码已经实现”而自动关闭。至少需要：

- 技术决策已落实；
- 自动测试覆盖；
- 代表性 fixture 通过；
- 失败路径和 fallback 验证；
- 文档与已知限制更新；
- 必要的兼容/视觉证据；
- 无阻断缺陷。

---

## 6. Phase 0 回写（2026-08-15）

Phase 0 完成（见 `PHASE0_GATE.md`）。各风险状态变化：

| ID | Phase 0 结果 | 新状态 |
|---|---|---|
| R-001 | 选型关闭：ADR-0001 决定迁往 markdown-it-py + 自研插件，现有 parser 冻结维护，ParserBackend 协议隔离 | 缓解中（迁移待 Phase 1–2） |
| R-002 | 决策关闭：pandoc 不进编译依赖（ADR-0001/0003/0004 一致），仅作可选外部工具；253MB 二进制问题规避 | 已关闭（决策层面） |
| R-003 | spike 实证各后端位置粒度；SourceMap/origin chain 设计落入 `IR_MODEL_DESIGN.md` §4 | 缓解中（实现待 Phase 1–2） |
| R-004 | ADR-0002 采用 Template Package v2；schema 设计完成（`TEMPLATE_PACKAGE_SCHEMA_V2.md`） | 缓解中（实现待 Phase 3） |
| R-005 | spike 实证合并可行 + 搬运清单（`spikes/phase0/docx-template/`）；Alpha 仅用 reference.docx，shell 留 Beta | 缓解中 |
| R-006 | 字段生命周期实证（Word 首开弹窗由 updateFields/dirty 各自独立触发）；ADR-0005 三 profile + TOC cached 条目决策 | 缓解中（TOC cached 待实现） |
| R-008 | 50 条 corpus 量化现状 48%；ADR-0003 决定扩手写子集至 ≥95% | 缓解中（实施待 Phase 6） |
| R-010 | 28 条 GB/T 7714-2025 golden corpus 建立（19 机器通过 / 9 pending-human-review）；ADR-0004 决策 | 缓解中（人工定稿待 GA 前） |
| R-011 | 实证 citeproc-py 仅 5/28 一致（引擎级缺陷）→ 拒绝；pandoc citeproc 为可选外部 provider | 已关闭（选型层面） |
| R-012 | 样式 precedence 与继承合并规则成文（SCHEMA D-1/D-2，ADR-0002） | 缓解中 |
| R-014 | 首轮三软件实证完成；WPS 无脚本接口登记 pending-human-review | 持续（门禁已就绪） |
| R-015 | `openxml_validate`（13 项）+ `no_repair_open` 门禁工具就绪并实测（Word pass） | 缓解中（纳入 PR 门禁待 CI 接线） |
| R-016 | 六域证据制采纳（ADR-0006）；qa/ 目录、用例目录、首个 XPath E2E 落地 | 缓解中 |
| R-018 | Project 层与显式顺序设计落入 `IR_MODEL_DESIGN.md` | 缓解中（实现待 Phase） |
| R-019 | shell 合并双跑字节一致实证；DOCX 规范化十步策略采纳（ADR-0006） | 缓解中 |
| R-020 | 模板包安全策略成文（SCHEMA §5.5/§7.4：宏/外部关系禁止、Zip Slip 防护） | 缓解中（实现待 Phase 3/10） |
| R-024 | MML2OMML.XSL 无开源许可 → 拒绝引入（ADR-0003）；GB/T CSL 许可证与哈希已记录（ADR-0004） | 缓解中 |
| R-027 | finalizer 三 profile 策略（ADR-0005）；新登记缺陷 D-09：darwin 硬编码 `/tmp` 无回退（office_refresh.py:592、pdf_preview.py:567），本机 /private/tmp 缺失已致 4 项测试失败 | 缓解中（D-09 列入 Phase 1 修复） |
| R-029 | contract 版本化策略（ADR-0006） | 缓解中 |
| R-030 | `PRODUCT_SCOPE.md` 成文，范围纪律写入 ADR-0006 | 缓解中 |

未触及风险（R-007/R-009/R-013/R-017/R-021/R-022/R-023/R-025/R-026/R-028）维持原等级，按台账计划阶段处理。
