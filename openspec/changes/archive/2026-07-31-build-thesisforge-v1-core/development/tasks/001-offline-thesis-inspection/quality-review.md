# Quality Review: 001-offline-thesis-inspection

## Verdict

approved

## Separation Of Concerns

- Parser 仍保持 renderer-neutral：`src/thesis_forge/core/parser.py:7-28` 只依赖标准库、`yaml` 和 domain model，没有把 DOCX、Template、UI、AI 或 Renderer 逻辑带进解析层。
- CLI 序列化边界仍在 `src/thesis_forge/cli.py:22-40`，`inspect` 负责把 `ThesisDocument` 投影成 JSON，Parser 本身只返回领域对象。
- 架构边界有直接测试兜底：`tests/test_architecture.py:30-38` 会拒绝 `docx`、`lxml`、`thesis_forge.renderers`、`thesis_forge.templates`、`thesis_forge.ui`、`thesis_forge.ai` 导入。

## Component Cohesion / Coupling

- 这次修复把“精确 inline 定位”留在 parser 内部完成，而没有污染 model 或 CLI：`_parse_container_inlines()` 负责容器内 caption/body 的逐行定位，见 `src/thesis_forge/core/parser.py:155-175`；脚注续行分段定位见 `src/thesis_forge/core/parser.py:261-288`。
- `ThesisDocument.register_inlines()` 继续作为单一聚合点维护 `inline_content`、`cross_references`、`citations`、`footnote_references`，耦合关系清晰，未出现解析层和展示层互相反向依赖的情况。
- 当前 parser 仍是单文件实现，但体量控制在 380 行内，且新增逻辑集中在辅助函数和局部循环，没有把跨层职责耦合到一起。

## Test Quality

- 正向覆盖已经足够强：`tests/test_parser.py:57-176` 覆盖了 Front Matter、段落、列表、figure、table、equation、algorithm、listing、citation、cross-reference、footnote 与 inline 顺序。
- 回归覆盖到位：`tests/test_parser.py:215-241` 直接锁定了本轮修复的两个高风险点，验证容器 caption/body 与脚注续行 citation 的精确行列坐标。
- 边界覆盖也有证据：`tests/test_parser.py:188-201` 覆盖 malformed parser 输入；`tests/test_cli.py:13-72` 同时覆盖 `inspect` 成功路径、malformed Front Matter 和缺失文件两条失败路径，并断言无 traceback；`tests/test_architecture.py:30-38` 覆盖导入边界。
- 验证日志可信：`openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl:1-8` 记录了 Python 3.14 下 `15 passed`、`ruff check .`、`pip check`、离线 `inspect`、SpecNav contract，以及额外 Python 3.12 临时环境下的 `15 passed` 和 CLI 失败路径复现。

## Error Handling

- Parser 本身的错误语义是好的：YAML Front Matter 失败会抛带源码行号的 `ParseError`，见 `src/thesis_forge/core/parser.py:50-65`；未闭合容器会抛具体到行号与容器类型的 `ParseError`，见 `src/thesis_forge/core/parser.py:299-300`。
- `thesisforge inspect` 现在把 parser/read failures 转成简洁 CLI 结果：`src/thesis_forge/cli.py:24-32` 捕获 `ParseError` 与 `OSError`，输出用户态文案并以 `exit 2` 结束。
- 失败路径已被测试锁定：`tests/test_cli.py:52-72` 断言 malformed Front Matter 与 missing file 都返回 `exit 2`，同时输出包含原因的简洁报错且不含 `Traceback`。

## Reuse / Duplication

- 可复用部分做得对：位置计算统一走 `_location_for_offset()`，inline tokenization 统一走 `_parse_inline_content()`，没有把 citation/cross-reference 解析复制到多个分支，见 `src/thesis_forge/core/parser.py:68-130`。
- 仍有一处小范围重复：`_parse_container()` 与 `_parse_container_inlines()` 都各自扫描了一次 container metadata/body 切换，分别位于 `src/thesis_forge/core/parser.py:155-175` 和 `src/thesis_forge/core/parser.py:178-226`。这会增加后续修改时的同步成本，但当前重复范围小、职责清楚，还不到必须抽象的程度。

## Complexity Delta

- 复杂度增量主要集中在 parser：`src/thesis_forge/core/parser.py` 现为 380 行，`tests/test_parser.py` 现为 241 行。对一个 V1 语法切片来说，这个规模仍可控。
- 这次增量没有引入深层嵌套或跨层泄漏。新增逻辑主要表现为两段低耦合 helper / segmentation 逻辑，且已经被针对性测试锁住。
- CLI 额外增加的错误边界很薄，仅在命令入口做异常转换，没有把解析职责反推回 parser，因此复杂度增量可接受。

## Required Fixes

- None. 前一轮 Required Fixes 已由 `src/thesis_forge/cli.py:24-32` 和 `tests/test_cli.py:52-72` 直接满足，并有 `openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl:1-8` 的执行证据支撑。
