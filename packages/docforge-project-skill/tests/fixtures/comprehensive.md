---
language: zh-CN
title: DocForge 全格式导入验证
author: 测试作者
organization: DocForge
keywords: [Markdown, 项目格式]
---
# 全格式验证 {#chap:overview}

这是包含 **粗体**、*斜体*、`inline_code` 和[本地语义链接](#chap:overview)的段落，并引用文献 [@smith2025]。

- 无序列表
  - 嵌套项目

1. 有序列表
2. 第二项

> 这是引用块。

![模型图](images/model.png)

| 指标 | 数值 |
|---|---:|
| 准确率 | 96.2% |

: 指标表 {#tbl:metrics}

行内数学 $x+y$ 保持在正文中。

$$
E=mc^2
$$
{#eq:energy}

```python {#lst:sample title="代码示例"}
print("DocForge")
```

这里有脚注。[^note]

[^note]: 脚注正文。

# 参考文献 {#chap:bibliography}
