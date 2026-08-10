# Prototype Question: automatic-docx-toc-refresh-p1

## Question

是否批准 `toc-field-office-refresh-seam-v1` 组件边界：DOCX Renderer 只把“目录”标题
和真实 TOC field 分成独立段落；application finalization 通过可注入
`DocumentRefresher` 在 package validation 前尝试 LibreOffice 更新；Office 缺失或失败
时保留有效 dirty field 并继续离线构建？

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Variant: `toc-field-office-refresh-seam-v1`
- Required reviewer decision: 是否批准该依赖方向、刷新时机、失败降级、进程隔离和测试边界
  作为自动目录纵向切片的生产开发依据。

## Out of Scope

- Production implementation.
- UI、模板编辑器、主题和国际化变更。
- Parser、Domain、Compiler 或 RenderPlan 计算页码。
- 静态伪目录、Word/WPS 私有自动化和强制安装 LibreOffice。
