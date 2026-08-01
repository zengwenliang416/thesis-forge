# Third-Party Notes

当前 ThesisForge V1 实现未从 `docs/REFERENCES.md` 所列参考仓库复制具体实现代码。
这些仓库仅用于架构、OOXML 方法和测试策略研究，也不会进入 wheel 或 sdist。

运行时直接依赖由 `pyproject.toml` 声明：

- Pydantic：领域和模板数据校验。
- PyYAML：Front Matter、模板和配置解析。
- python-docx：DOCX 高层对象。
- lxml：focused OOXML 与 package 结构处理。
- Typer / Rich：CLI 参数和终端输出。

`citeproc-py` 是可选依赖，不是离线核心命令的运行前提。React、TypeScript、Vite
和 Tauri 2 属于后续跨平台工作台的独立前端与桌面发行工具链，不进入 Python 核心
运行时依赖。公开发布前仍需完成 Python、npm、Cargo 及 sidecar 分发依赖的许可证
清单、项目许可证选择和分发策略审查。

后续如引入或改写第三方实现，按以下格式登记：

```text
Source:
Repository:
Commit:
Original file:
License:
Local file:
Usage:
Changes:
```

如未来复制、改写或生成自第三方具体实现，必须在合入前新增真实记录，不得保留空白
模板作为合规证据。
