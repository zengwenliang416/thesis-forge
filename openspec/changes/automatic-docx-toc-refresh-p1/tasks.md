## 1. Correct TOC OOXML Structure

**用户结果：** “目录”标题不会再被目录更新吞掉；即使本机没有 Office 布局引擎，
DOCX 仍包含可手动更新的真实目录对象。

- [ ] 1.1 把 `toc.title` 普通文本段落与下一段 TOC complex field 分离。
- [ ] 1.2 保留 field instruction、dirty 标记、begin/separate/end 和 `w:updateFields=true`。
- [ ] 1.3 增加 OOXML 测试，证明标题与 field 的段落顺序、样式和独立生命周期。

## 2. Cross-Platform Office Refresh

**用户结果：** Web、macOS 和 Windows 在安装 LibreOffice 时可直接得到已计算的目录条目
和页码；未安装或刷新失败时不影响正常导出。

- [ ] 2.1 新增可注入 `DocumentRefresher` 和默认 `LibreOfficeDocumentRefresher`。
- [ ] 2.2 实现 macOS、Linux 和 Windows executable discovery。
- [ ] 2.3 使用隔离 user profile、私有 UNO endpoint、hidden load、index/field update、
  原文件保存、有界超时和进程/profile 清理。
- [ ] 2.4 在 render 之后、package validation 和 atomic replace 之前接入刷新器。
- [ ] 2.5 增加 missing、failure、timeout、corrupt-output、cancellation 和调用顺序测试。

## 3. Documentation And Complete Verification

**用户结果：** 完整 HUT 论文导出后目录可见、可编辑、页码已填充，并且失败降级和跨平台
安装边界有明确文档与证据。

- [ ] 3.1 更新 `docs/TEMPLATE_SPEC.md`，说明 TOC 模板样式与 Office 刷新职责边界。
- [ ] 3.2 使用本机真实 LibreOffice 构建完整 HUT 论文，检查 cached entries、field、
  title、styles 和 DOCX package。
- [ ] 3.3 执行聚焦测试、完整 pytest、Ruff、OpenSpec strict validation、CodeGraph、
  sensory review 和 SpecNav development handoff。
