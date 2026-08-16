---
# 来源：spikes/phase0/parser/fixtures/full-syntax.md（Phase 0 parser spike 全语法样例），
# 适配为 qa 正式 parser fixture；覆盖 docs/MARKDOWN_SPEC.md v0.1 的全部语法面。
document:
  type: master_thesis
  language: zh-CN
thesis:
  title: "Parser 全语法 qa 夹具"
author:
  name: "张三"
render:
  template_id: "spike-template"
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
---

# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

传统排版依赖手工调整 [@smith2025]，确定性编译可降低成本 [@smith2025; @wang2024]，已有综述给出页码级证据 [@smith2025, p. 12]。[^note]

### 现有方法的分类

#### 手工排版的局限 {#sec:manual-limits}

如 @fig:model 所示，并参见 @tbl:results、@eq:loss、@alg:train、@lst:predict、@sec:background 与 @chap:introduction。

行内数学 $E = m c^2$ 与普通文本混排，用于验证 `$...$` 不破坏段落与 inline 解析。[^long]

::: figure {#fig:model}
src: "./images/model.png"
caption: "模型总体结构"
width: "85%"
:::

::: table {#tbl:results}
caption: "实验结果"

| 模型 | AUROC |
| --- | ---: |
| A | 0.91 |
| B | 0.94 |

:::

::: equation {#eq:loss}
$$
L=-\sum_i y_i \log \hat y_i
$$
:::

::: algorithm {#alg:train}
caption: "训练流程"

1. 初始化参数；
2. 读取数据；
3. 前向计算；
4. 反向传播。
:::

::: listing {#lst:predict}
caption: "预测函数"
language: "python"

```python
def predict(x):
    return model(x)
```
:::

## 列表示例 {#sec:lists}

- 第一项
  - 第二级项目
- 第三项

3. 从 3 开始
4. 下一项

# 参考文献 {#chap:references}

::: bibliography
:::

[^note]: 这是普通脚注。
[^long]: 第一行。
    第二行（续行）。
