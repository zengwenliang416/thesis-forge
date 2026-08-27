# 交叉引用目标缺失负例（TF-D2-REF-004） {#chap:missing-ref-case}

正文引用[图](#fig:ghost)，但全文没有 ID 为 `fig:ghost` 的图，validator
必须给出 `missing-reference` 结构化诊断（AGENTS.md §4：引用 target 是否存在）。

![真实存在的示例图](images/model.png){#fig:real}
