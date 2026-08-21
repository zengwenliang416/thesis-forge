# ThesisForge Codex Loop Runbook

## 首次启动

把以下内容直接交给 Codex：

```text
/goal Read LOOP.md first and execute the ThesisForge engineering loop one cycle at a time.

Make the Goal in LOOP.md true.

A cycle handles exactly one Open item. Before editing, list the exact repository files you expect to touch. One implementation item may modify at most three repository files, counting source, test, fixture, documentation, configuration, workflow, lockfile, creation, deletion, rename, move, and generated changes.

When a fourth file is required, do not edit product code. Split the item into ordered child items, each naming at most three files and its own executable Verify command; update LOOP.md and end the cycle.

Use docs/THESISFORGE_V2_PRODUCT_SPEC.md as the normative requirement and docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md as the discovery catalogue. Do not mechanically execute the catalogue when the current code requires a smaller green slice.

The Maker may implement but may not mark its own item Done. An independent Checker must audit the diff, reject scope creep, run the exact Verify command, restore failed work, and only then move the item to Done and create one local commit containing the task ID. Never push.

Do not add legacy compatibility, automatic migration, fallback parsers, dual source-of-truth fields, hidden flags, message-only build failures, silent degradation, return-None handling for unknown semantic nodes, or [kind] {payload} output.

Keep the current repository baseline green after every completed cycle. Do not add intentionally failing tests to the normal test suite. Goal-only failures belong in scripts/verify_thesisforge_v2_goal.py and are evaluated by stop-check.sh only after Open is empty.

Done only when LOOP.md has no Open or Blocked items and ./stop-check.sh exits 0. Do not infer completion from code inspection. Run the stop condition.

Stop and record Blocked after three failed verification attempts, three consecutive no-progress cycles, an unresolved security/data-loss boundary, or any action requiring the Human gate.
```

## 继续下一轮

```text
Continue the active /goal loop from LOOP.md. Execute exactly one Open item and obey the three-file limit, Maker/Checker separation, exact Verify command, local-commit-only rule, and Human gate.
```

## 指定一个任务

仅在人工需要改变优先级时使用：

```text
Continue the active /goal loop, but select item <ITEM-ID> for this cycle. Do not execute another item. Keep every rule in LOOP.md unchanged.
```

## 查看状态但不改代码

```text
Read LOOP.md and report the current Goal status, first three executable Open items, blockers, last five Cycle log entries, and whether the three-file boundaries remain valid. Do not edit files.
```

## 最终验证

Codex 只有在 Open 和 Blocked 均为空时才运行：

```bash
./stop-check.sh
```

通过后，Codex应将 `**Status:**` 改成 `done`，追加最终 Cycle Log，再次运行 `./lint-loop.sh`。远程推送和 PR 仍由人执行。
