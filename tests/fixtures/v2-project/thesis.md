# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

已有研究表明，**结构化编译**与*可验证反馈*能够提升论文工程的一致性 [@smith2025]。
本项目使用 `thesisforge.yaml` 作为入口，普通源码换行
不应在 Word 中产生手动换行。这里使用一个[普通链接](https://example.com)，模型流程见[图](#fig:model)。

![模型总体结构](assets/model.png){#fig:model}

损失函数定义如下：

$$
L=-\sum_{i=1}^{N} y_i \log \hat y_i
$$
{#eq:loss}

其计算方式见[式](#eq:loss)。

| 指标 | 实验组 | 对照组 |
|---|---:|---:|
| **准确率** | 96.2% | 91.8% |
| 召回率 | 94.1% | 89.6% |

: 模型实验结果 {#tbl:experiment}

结果汇总见[表](#tbl:experiment)。

> 内容审阅应隐藏技术标记，但保留这一引用块。

```python {#lst:training title="训练代码"}
# 代码中的 {#literal}、[@literal] 与 @fig:literal 必须保持字面量
for epoch in range(epochs):
    train_one_epoch()
```

```algorithm {#alg:training title="训练流程"}
输入：训练集 D
输出：模型 M
1. 初始化参数
2. 迭代优化
```

这里包含一个说明性脚注[^scope]。  
这一行使用显式 HardBreak。

[^scope]: Review 中显示脚注号和正文，DOCX 中生成原生脚注。

# 参考文献 {#region:bibliography}
