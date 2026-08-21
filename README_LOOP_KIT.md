# ThesisForge v2 Loop Kit

本目录是一套可以直接复制到 ThesisForge 仓库根目录的 Loop Engineering 执行包。

它把此前分散的需求统一为一个破坏性 v2 目标：

- 强制以 `thesisforge.yaml` 打开论文项目；
- `thesis.md` 只保存可读正文与最小稳定语义；
- 删除旧 Front Matter、旧 `:::` 论文对象、旧交叉引用和多 Parser 兼容；
- 使用唯一强类型、无静默丢失的 Markdown → IR → RenderPlan → DOCX 流水线；
- 提供内容审阅、结构检查、最终版式三种视图；
- 每次构建都产生可见、可跳转源码的 BuildReport；
- 构建失败保留上一次成功预览并标记为过期；
- 所有已声明格式都必须有 Review、DOCX 和测试证据；
- 每个实现子任务最多修改三个仓库文件。

## 需要复制到仓库的文件

```text
LOOP.md
lint-loop.sh
stop-check.sh
CODEX_RUNBOOK.md
docs/THESISFORGE_V2_PRODUCT_SPEC.md
docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md
protocol/build-report.v2.schema.json
protocol/examples/build-success.json
protocol/examples/build-failed-validation.json
protocol/examples/build-failed-render.json
spec/format-capabilities.yaml
scripts/verify_thesisforge_v2_goal.py
tests/fixtures/v2-project/thesisforge.yaml
tests/fixtures/v2-project/thesis.md
tests/fixtures/v2-project/references.bib
tests/fixtures/v2-project/assets/model.png
tests/fixtures/legacy-project/thesis.md
```

这些文件是一个整体。不要再同时保留此前生成的：

```text
THESISFORGE_CODEX_IMPLEMENTATION_PLAN.md
THESISFORGE_CODEX_BREAKING_IMPLEMENTATION_PLAN.md
THESISFORGE_BUILD_ERROR_VISIBILITY_PLAN.md
LOOP_WITH_BUILD_ERRORS.md
```

它们的有效需求已经合并进本包。

## 安装

在仓库根目录执行：

```bash
unzip thesisforge-v2-loop-kit.zip -d /tmp/thesisforge-v2-loop-kit
cp -R /tmp/thesisforge-v2-loop-kit/. .
chmod +x lint-loop.sh stop-check.sh
./lint-loop.sh
```

第一次执行 `./stop-check.sh` 预期会失败，因为目标功能尚未实现，而且 `LOOP.md` 仍包含 Open 项。这不是日常测试命令；它只用于判断整个 Goal 是否完成。

日常每个子任务只运行其在 `LOOP.md` 或实施计划中声明的定向 Verify 命令，并保持现有仓库基线绿色。

## Codex 使用入口

打开 `CODEX_RUNBOOK.md`，将其中的 `/goal` 指令交给 Codex。Codex 每个 Cycle 只处理一个 Open Item，独立 Checker 验证通过后才允许进入 Done。

## 文件角色

| 文件 | 作用 |
|---|---|
| `LOOP.md` | 唯一活跃 Goal、规则、Open/Done/Blocked 和 Cycle Log |
| `lint-loop.sh` | 检查 Loop 状态结构、三文件限制和任务完整性 |
| `stop-check.sh` | Goal 终止条件；只有全目标完成时退出 0 |
| `CODEX_RUNBOOK.md` | 可直接粘贴给 Codex 的启动和续跑指令 |
| `docs/THESISFORGE_V2_PRODUCT_SPEC.md` | 唯一产品与架构需求基线 |
| `docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md` | 按最多三个文件拆分的完整任务目录 |
| `protocol/**` | BuildReport v2 的机器可读协议与黄金样例 |
| `spec/format-capabilities.yaml` | 已承诺格式的端到端能力清单 |
| `scripts/verify_thesisforge_v2_goal.py` | 最终行为级 Goal 验证器 |
| `tests/fixtures/**` | v2 成功项目与旧格式拒绝输入 |

## 人工边界

Loop 可以在本地分支修改代码、运行测试和创建本地提交，但不得自行：

- 推送远程分支；
- 创建或更新远程 PR；
- 合并；
- 发布；
- 部署；
- 删除用户数据；
- 修改外部服务；
- 产生费用。

这些操作必须由人确认。
