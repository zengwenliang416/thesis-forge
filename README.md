# ThesisForge

> 结构化学术论文编写、校验与排版系统  
> **Markdown 写论文，一键生成学校标准 Word。**

ThesisForge 的核心目标不是做一个“Markdown 转 Word 小工具”，而是建立一个可长期演进的**学术论文编译器**：

```text
thesis.md
   ↓
Parser
   ↓
Thesis AST / Document Model
   ↓
Validator
   ↓
School Template Resolver
   ↓
Compiler
   ↓
DOCX Renderer
   ↓
thesis.docx
```

## 1. 产品原则

1. **离线优先**：基础排版、结构解析、模板应用、校验、DOCX 生成必须完全离线可用。
2. **AI 可选**：AI 只做润色、摘要、结构建议、改写等辅助能力，不进入排版核心链路。
3. **结构与样式分离**：`thesis.md` 描述论文内容与语义；学校 YAML 模板描述 Word 版式。
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
├── src/thesis_forge/
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
                    │   thesis.md   │
                    └───────┬───────┘
                            ↓
                    Markdown Parser
                            ↓
                    ThesisDocument
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
                     output/thesis.docx
```

`RenderPlan` 再把论文语义和 Word 实现细节隔开，避免 AST 直接依赖 OOXML。

## 5. 快速开始

当前仓库是**可开发骨架**：已经放入 Parser / Validator / AST / Template Model / DOCX smoke renderer 的最小实现，高级 Word 对象后续按里程碑补齐。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

thesisforge inspect examples/bachelor-thesis/thesis.md
thesisforge validate examples/bachelor-thesis/thesis.md
```

## 6. Markdown 示例

```markdown
---
thesis:
  title: "我的本科毕业论文"
author:
  name: "张三"
render:
  template_id: "example-university-2026"
  bibliography: "./references.bib"
---

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

完整模板见 `examples/bachelor-thesis/thesis.md`。

## 7. 学校模板

论文正文中**不要写字体、字号、页边距、固定行距**。这些配置放在：

```text
templates/schools/<school>/<year>.yaml
```

同一份 `thesis.md` 可以切换不同学校模板重新编译。

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
- PySide6：桌面 UI（V1 后半段）

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

## 11. 许可证

本骨架暂未替项目选择开源许可证。发布前请根据商业/开源计划明确许可证，并对第三方依赖与参考代码做许可证审查。
## 12. 初始化为你的 Git 仓库

```bash
cd thesis-forge
git init
git add .
git commit -m "chore: initialize ThesisForge scaffold"
```

如需把参考仓库拉到本地研究：

```bash
./scripts/clone_references.sh
```

这些仓库会进入 `references/external/`，默认不会被提交。

