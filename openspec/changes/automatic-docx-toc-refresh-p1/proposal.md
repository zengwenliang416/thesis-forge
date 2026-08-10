## Why

ThesisForge 已生成真实 Word TOC field，但当前把 field 的缓存结果“目录”放在同一个
`TFTOCTitle` 段落。WPS macOS 不会在打开文档时自动计算该 field，因此用户只看到一个
空白目录页；更新 field 还可能替换标题。需要分离标题与 field，并在兼容本地 Office
布局引擎存在时自动刷新目录条目和页码。

## What Changes

- 把可见“目录”标题写入独立语义样式段落。
- 在下一段写入真实、dirty、可编辑的 TOC complex field，不再用标题充当 field result。
- application finalization 新增可注入 LibreOffice document refresher。
- 默认 refresher 跨平台发现 LibreOffice，使用隔离 profile 和 UNO 更新 indexes/fields。
- LibreOffice 缺失或失败时安全降级，保留有效 dirty TOC field 和现有离线构建能力。
- 在刷新后执行 DOCX package validation，再原子替换最终输出。
- 增加 OOXML、跨平台发现、失败保护、调用顺序和真实 HUT DOCX 端到端验证。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `render-plan-docx`: render a standalone TOC title and a following true editable TOC field.
- `offline-cli-pipeline`: optionally refresh DOCX indexes through a local compatible LibreOffice
  before validating and atomically publishing the output.

## Impact

- Affected code: DOCX Renderer, application finalization, new Office refresh service, focused tests
  and template documentation.
- Public contract: `build_service` success and output contracts remain unchanged; dependency
  injection gains an internal document refresher hook.
- Dependencies: no Python package or network dependency; LibreOffice is an optional local runtime.
- Architecture: preserves `Markdown -> ThesisDocument -> Validation -> Template -> RenderPlan ->
  DOCX`; pagination remains outside Parser, Domain, Compiler and Renderer-neutral plans.
