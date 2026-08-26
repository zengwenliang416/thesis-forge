# DocForge

> 本地优先、确定性、模板驱动的 Markdown 文档编译器
> **用结构化 Markdown 生成可编辑、可验证的 Word 文档。**

DocForge 将 Markdown 项目编译为可编辑 DOCX。通用文档与学术文档共享同一条语义解析、校验、模板和渲染流水线：

```text
docforge.yaml + document.md
   ↓
Parser
   ↓
ForgeDocument
   ↓
Validator
   ↓
School Template Resolver
   ↓
Compiler
   ↓
DOCX Renderer
   ↓
   build/document.docx
```

## 1. 产品原则

1. **离线优先**：基础排版、结构解析、模板应用、校验、DOCX 生成必须完全离线可用。
2. **AI 可选**：AI 只做润色、摘要、结构建议、改写等辅助能力，不进入排版核心链路。
3. **结构与样式分离**：`document.md` 描述内容与语义；模板 YAML 描述 Word 版式。
4. **先语义模型，后渲染**：禁止直接将 Markdown 节点“边解析边写进 Word”。
5. **Word 对象是真对象**：目录、公式、题注、交叉引用、脚注、页码等尽量生成真实 OOXML/Word 对象，而不是视觉模拟。
6. **模板可替换**：同一份论文源文件可以套不同学校模板生成不同 DOCX。
7. **可检查**：生成 Word 前报告缺图、断链引用、未引用文献、标题层级异常等问题。

## 2. V1 范围

### 必做

- YAML Front Matter 元数据
- Markdown 标题 / 段落 / 列表
- 图片 + 题注 + 编号
- 表格 + 三线表样式
- LaTeX 公式 → Word OMML
- 公式编号
- 图 / 表 / 公式交叉引用
- BibTeX 文献库
- GB/T 7714-2025 引用与参考文献输出接口
- 自动目录
- 多 Section 与页码
- 页眉页脚
- 学校 YAML 模板
- 论文结构与引用校验
- DOCX 导出

### 暂不作为 V1 核心

- AI 写整篇论文
- 多人实时协作
- 云端账号体系
- 在线模板市场
- WPS / Word 插件

## 3. 项目结构

```text
thesis-forge/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── src/docforge/
│   ├── core/            # Parser / AST / Validator / Compiler
│   ├── renderers/docx/  # DOCX + OOXML 渲染
│   ├── bibliography/    # BibTeX / CSL / 引文
│   ├── templates/       # 模板加载与解析
│   ├── ai/              # 可选 AI 层
│   ├── ui/              # 桌面 UI（后置）
│   └── cli.py
├── templates/
│   ├── base/
│   └── schools/
├── examples/
├── docs/
├── tests/
└── scripts/
```

## 4. 核心数据流

```text
                    ┌───────────────┐
                    │  document.md  │
                    └───────┬───────┘
                            ↓
                    Markdown Parser
                            ↓
                     ForgeDocument
                            ↓
              ┌─────────────┼─────────────┐
              ↓             ↓             ↓
          Validator     Bibliography    Template
              └─────────────┼─────────────┘
                            ↓
                         Compiler
                            ↓
                       RenderPlan
                            ↓
                      DOCX Renderer
                            ↓
                    build/document.docx
```

`RenderPlan` 再把论文语义和 Word 实现细节隔开，避免 AST 直接依赖 OOXML。

## 5. 快速开始

当前仓库已完成 DocForge 核心编译链。`inspect`、`validate`、`review` 和 `build`
均可在无网络、无 AI API Key 的环境中运行；完整示例覆盖本地图、三线表、可编辑
OMML 公式、Word 字段、交叉引用、脚注、多 Section、页眉页脚、BibTeX 引用和参考文献。

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
make install

make inspect
make validate
make build-example
```

也可以直接使用安装后的命令：

```bash
.venv/bin/docforge inspect tests/fixtures/docforge-academic
.venv/bin/docforge validate tests/fixtures/docforge-academic
.venv/bin/docforge review tests/fixtures/docforge-academic --output-dir review
.venv/bin/docforge build tests/fixtures/docforge-academic
```

模板由项目入口 `docforge.yaml` 的 `render.template_id` 选择。

## 6. 项目示例

`docforge.yaml`：

```yaml
schema: docforge.project.v1
project:
  id: example-document
  language: zh-CN
document:
  source: document.md
  type: academic
metadata:
  title:
    zh: 我的文档
  authors:
    - name: 张三
academic:
  student:
    name: 张三
    id: "20260001"
render:
  template_id: example-university-2026
```

`document.md`：

```markdown
# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

已有研究表明…… [@ref-example-1]。

::: figure {#fig:model}
src: "./images/model.png"
caption: "模型总体结构"
width: "85%"
:::

如 @fig:model 所示。

::: equation {#eq:loss}
$$
L=-\sum_{i=1}^{N} y_i \log \hat y_i
$$
:::
```

可执行项目见 `tests/fixtures/docforge-academic/`。

## 7. 学校模板

论文正文中**不要写字体、字号、页边距、固定行距**。这些配置放在：

```text
templates/schools/<school>/<year>.yaml
```

同一份 `document.md` 可以切换不同模板重新编译。

## 8. GitHub 参考仓库

详细用途、clone 命令、许可检查要求见：

- `docs/REFERENCES.md`
- `scripts/clone_references.sh`

重点参考：

- `AfishInLake/WordFormat`
- `Drenches/gov-doc-formatter`
- `wzbwan/gongwen-format-skill`
- `xkonglong/gw`
- `python-openxml/python-docx`
- `jgm/pandoc`
- `citeproc-py/citeproc-py`
- `citation-style-language/styles`
- `zhiyiYo/PyQt-Fluent-Widgets`

> 在吸收任何源码前，必须检查上游仓库 LICENSE。不要因为仓库公开就默认可以复制源码。

## 9. 推荐技术栈

- Python 3.11+
- Pydantic：领域模型 / 模板 Schema
- PyYAML：模板与 Front Matter
- python-docx：DOCX 高层 API
- lxml：OOXML 低层控制
- Pandoc：Markdown AST/转换语义参考，可作为可选 parser backend
- citeproc-py：CSL 引用处理候选
- React + TypeScript + Vite：Web、macOS、Windows 共用前端
- Tauri 2：macOS / Windows 桌面壳与托管 Python sidecar

Web 通过版本化 HTTP adapter 调用 Python application services；macOS 和 Windows
通过 Tauri command bridge 调用相同 services。Python CLI 不依赖 Node.js、Rust、
Tauri 或 HTTP server，仍可独立离线运行。

## 10. 开发里程碑

```text
M0  仓库骨架 + 规范
M1  Parser + ThesisDocument
M2  Template + Validator
M3  基础 DOCX（段落/标题/页面）
M4  Figure/Table
M5  Equation/OMML
M6  Bookmark/REF/SEQ/TOC
M7  Bibliography/GB-T 7714
M8  完整端到端编译
M9  桌面 UI
M10 AI 扩展
```

详细计划见 `docs/V1_PLAN.md`。

## 11. 测试、打包与维护

日常源码、Web 与 sidecar 维护门禁：

```bash
make verify
```

该命令执行完整 pytest、Ruff、依赖一致性、wheel/sdist 构建、隔离 wheel
安装与离线 CLI 回归、前端与 sidecar 验证、严格 OpenSpec 校验和 Git
whitespace 检查。它不构建或替代 macOS `.app/.dmg` 与 Windows `.msi/.exe`
原生安装包门禁；原生打包和 verifier 命令见下文。

只构建并验证安装包：

```bash
make verify-dist
```

wheel 内置基础模板和示例学校模板。安装验证会从仓库外运行完整示例，确保不依赖
checkout 中的 `src/`、`templates/` 或父开发环境 `site-packages`。详细维护流程见
`docs/MAINTENANCE.md`。

### Web 与桌面分发

三个产品入口共用同一套 React + TypeScript + Vite 工作台，但运行能力不同：

- Web：`dist/web/` 是静态资源，必须显式配置并连接 DocForge HTTP 服务。
  浏览器没有本地路径权限，使用 workspace 上传、显式保存和下载语义。
- macOS：Tauri `.app` / `.dmg` 内置目标平台的冻结 Python sidecar，正常运行不
  需要另外安装 Python、Node.js、Rust、API Key、账号或网络服务。
- Windows：Tauri `.msi` / NSIS `.exe` 使用同一前端和协议，并内置 Windows
  原生 sidecar；必须由 Windows runner 原生构建和验收，不能重命名 macOS 产物。

构建独立 Web 与当前平台 sidecar：

```bash
make package-web
make verify-desktop-dist
```

macOS 原生打包：

```bash
cargo tauri build \
  --config src-tauri/tauri.release.conf.json \
  --bundles app,dmg
dot_clean -m src-tauri/target/release/bundle
.venv/bin/python scripts/verify_desktop_distribution.py \
  --platform macos \
  --bundle-root src-tauri/target/release/bundle
```

产物位于：

```text
dist/web/
dist/python/
src-tauri/binaries/
src-tauri/target/<target>/release/bundle/
```

桌面工作台支持 `Cmd/Ctrl+K` 聚焦编辑器、`Cmd/Ctrl+S` 显式保存、
`Cmd/Ctrl+B` 构建 DOCX。打开源文件仅接受 `.md` 或 `.markdown`；构建结果默认
写入项目的 `build/document.docx`，并保留临时包校验与原子替换行为。

当前本地产物未做 Apple Developer ID / Microsoft Authenticode 生产签名，也未做
Apple notarization。它们用于本地验收和 CI 产物验证，不应直接作为公开发行包。
签名、公证、Windows runner 和校验和流程见 `docs/MAINTENANCE.md`。

## 12. 许可证

项目尚未选择开源许可证。当前 wheel/sdist 仅用于本地安装与验收；公开发布前必须
明确项目许可证，并完成第三方依赖与参考实现审查。

## 13. 参考仓库

如需把参考仓库拉到本地研究：

```bash
./scripts/clone_references.sh
```

这些仓库会进入 `references/external/`，默认不会被提交。
