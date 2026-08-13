# Prototype Question: libreoffice-preview-fidelity-p1

## Question

是否批准 `macos-temporary-font-alias-v1`：只在送入 LibreOffice 的一次性 DOCX 副本中，
把精确 OOXML 字体属性 `宋体` 映射为 `Source Han Serif SC`、`黑体` 映射为
`PingFang SC`，正式 DOCX 和非 macOS 转换保持原字体名称？

## Branch

`logic-state`

## Review Target

- Entry: `logic/harness.js`
- Variant: `macos-temporary-font-alias-v1`
- Required reviewer decision: 是否接受该平台隔离、失败降级和输入不变边界作为生产实现依据。

## Out of Scope

- Production implementation.
- Database writes.
- Deployment behavior.
- 捆绑字体、修改用户全局 Office 配置或承诺 WPS/Word 逐像素一致。
