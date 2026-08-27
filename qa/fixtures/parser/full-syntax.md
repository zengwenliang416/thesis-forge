# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

传统排版依赖手工调整 [@smith2025]，确定性编译可降低成本
[@smith2025; @wang2024]，已有综述给出页码级证据 [@smith2025, p. 12]。[^note]

### 现有方法的分类

#### 手工排版的局限 {#sec:manual-limits}

如[图](#fig:model)所示，并参见[表](#tbl:results)、[式](#eq:loss)、
[算法](#alg:train)、[清单](#lst:predict)、[小节](#sec:background)与
[绪论](#chap:introduction)。

行内数学 $E = m c^2$ 与普通文本混排，用于验证 `$...$` 不破坏段落与 inline 解析。[^long]

![模型总体结构](images/model.png){#fig:model}

| 模型 | AUROC |
| --- | ---: |
| A | 0.91 |
| B | 0.94 |

: 实验结果 {#tbl:results}

$$
L=-\sum_i y_i \log \hat y_i
$$
{#eq:loss}

```algorithm {#alg:train title="训练流程"}
输入：训练集 D
1. 初始化参数
2. 读取数据
```

```python {#lst:predict title="预测函数"}
def predict(x):
    return model(x)
```

## 列表示例 {#sec:lists}

- 第一项
  - 第二级项目
- 第三项

3. 从 3 开始
4. 下一项

# 参考文献 {#chap:references}

[^note]: 这是普通脚注。
[^long]: 第一行。
    第二行（续行）。
