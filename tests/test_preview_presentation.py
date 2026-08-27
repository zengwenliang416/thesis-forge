from __future__ import annotations

import json
from pathlib import Path

import pytest

from docforge import application, presentation
from docforge.core.model import (
    Algorithm,
    BibliographyBlock,
    BlockQuote,
    CodeBlock,
    Equation,
    Figure,
    FootnoteDefinition,
    ForgeDocument,
    Heading,
    ListBlock,
    Listing,
    Paragraph,
    SourceLocation,
    Table,
    Text,
    ValidationIssue,
)
from docforge.core.render_plan import (
    AlgorithmInstruction,
    BibliographyEntryInstruction,
    BibliographyInstruction,
    BlockQuoteInstruction,
    CaptionRuns,
    CitationRun,
    CodeBlockInstruction,
    CoverInstruction,
    EquationInstruction,
    FigureInstruction,
    FootnoteDefinitionInstruction,
    FootnoteReferenceRun,
    HardBreakRun,
    HeadingInstruction,
    HyperlinkRun,
    ListingInstruction,
    ListInstruction,
    ListItemInstruction,
    MathRun,
    ParagraphInstruction,
    ReferenceRun,
    RenderPlan,
    SectionBreakInstruction,
    SoftBreakRun,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
    TocInstruction,
)
from docforge.core.validator import ValidationContext

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "preview-workbench-v1.json"


def _unknown_instruction(name: str) -> object:
    return type(name, (), {})()


_COMPLETE_V2_SOURCE = """\
# 绪论 {#chap:introduction}

系统总体架构如[图](#fig:architecture)所示。

![ThesisForge 确定性编译架构](assets/architecture.png){#fig:architecture}

# 系统设计 {#chap:design}

## 编译流水线 {#sec:pipeline}

系统采用单向编译链路，其抽象关系见[式](#eq:pipeline)。

$$
D_{docx} = R(C(V(P(D_{md}))))
$$
{#eq:pipeline}

## 能力模型 {#sec:capabilities}

V1 核心能力见[表](#tbl:capabilities)。

| 能力 | 输入 | DOCX 输出 |
| --- | --- | --- |
| 图 | 本地图片 | Drawing 与题注 |
| 表 | Markdown 表格 | 三线表 |
| 公式 | LaTeX 子集 | OMML |
| 引用 | BibTeX key | 顺序编码引用 |

: ThesisForge V1 核心能力 {#tbl:capabilities}

## 安全构建算法 {#sec:safe-build}

安全构建流程见[算法](#alg:build)。

```algorithm {#alg:build title="安全构建流程"}
1. 解析并验证本地输入；
2. 编译 renderer-neutral RenderPlan；
3. 渲染到目标目录临时文件；
4. 校验 DOCX ZIP 与核心 XML；
5. 原子替换最终输出。
```

## 应用服务接口 {#sec:application-service}

核心服务接口示意见[代码](#lst:service)。

```python {#lst:service title="安全构建服务调用"}
result = build_service(
    source="document.md",
    output="document.docx",
)
```
"""

_COMPLETE_V2_MANIFEST = """\
schema: docforge.project.v1
project:
  id: preview-order
  language: zh-CN
document:
  source: document.md
  type: academic
metadata:
  title:
    zh: Preview order
  authors:
    - name: Test Author
academic:
  student:
    name: Test Author
    id: "20260001"
  institution:
    name: Test University
    department: Computer Science
  degree:
    name: Bachelor
    major: Document Engineering
  advisor:
    name: Test Advisor
  completion:
    date: "2026-08"
resources:
  root: .
  assets: assets
render:
  template_id: example-university-2026
  citation_style: GB-T-7714-2025
"""


def _complete_v2_project(tmp_path: Path) -> Path:
    project = tmp_path / "complete-v2"
    assets = project / "assets"
    assets.mkdir(parents=True)
    (assets / "architecture.png").write_bytes(
        (
            ROOT
            / "examples"
            / "bachelor-thesis"
            / "images"
            / "acceptance-architecture.png"
        ).read_bytes()
    )
    (project / "document.md").write_text(_COMPLETE_V2_SOURCE, encoding="utf-8")
    (project / "docforge.yaml").write_text(
        _COMPLETE_V2_MANIFEST,
        encoding="utf-8",
    )
    return project


def _text_inlines(value: str) -> list[Text]:
    return [Text(value=value)]


def _preview_api():
    assert hasattr(application, "PreviewResult")
    assert hasattr(presentation, "map_preview_result")
    return application.PreviewResult, presentation.map_preview_result


def test_preview_mapper_matches_versioned_golden_contract(tmp_path: Path):
    PreviewResult, map_preview_result = _preview_api()
    source = tmp_path / "thesis.md"
    image = tmp_path / "images" / "arch.png"
    image.parent.mkdir()
    image.write_bytes(b"preview-fixture")
    document = ForgeDocument(
        source_path=source,
        blocks=[
            Heading(
                id="chap:intro",
                level=1,
                inlines=_text_inlines("绪论"),
                location=SourceLocation(line=8),
            ),
            Paragraph(
                inlines=[Text(value="系统结构见图 1-1，相关工作见[1]。脚注1")],
                location=SourceLocation(line=10),
            ),
            Figure(
                id="fig:arch",
                src="./images/arch.png",
                caption_inlines=_text_inlines("系统架构"),
                width="80%",
                location=SourceLocation(line=12),
            ),
        ],
    )
    plan = RenderPlan(
        nodes=[
            HeadingInstruction(
                source_id="chap:intro",
                level=1,
                text="绪论",
                inlines=(TextRun("绪论"),),
            ),
            ParagraphInstruction(
                text="系统结构见图 1-1，相关工作见[1]。脚注1",
                inlines=(
                    TextRun("系统结构见"),
                    ReferenceRun("fig:arch", "fig_arch", "图 1-1"),
                    TextRun("，相关工作见"),
                    CitationRun(("ref-1",), (1,), text="[1]"),
                    TextRun("。"),
                    FootnoteReferenceRun("note", 1),
                ),
            ),
            FigureInstruction(
                source_id="fig:arch",
                src="./images/arch.png",
                asset_path=image,
                caption=CaptionRuns((TextRun("系统架构"),)),
                width="80%",
                resolved_width=None,
                chapter=1,
                number="1-1",
                label="图 1-1",
                bookmark="fig_arch",
            ),
            _unknown_instruction("custom-widget"),
        ]
    )
    issues = (
        ValidationIssue(
            code="heading-level-jump",
            severity="warning",
            message="jump",
            line=8,
        ),
        ValidationIssue(
            code="figure-note",
            severity="info",
            message="note",
            target="fig:arch",
        ),
    )

    result = map_preview_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=issues,
            plan=plan,
        )
    )

    assert result == json.loads(FIXTURE.read_text(encoding="utf-8"))
    json.dumps(result, ensure_ascii=False)
    assert str(tmp_path) not in json.dumps(result, ensure_ascii=False)


def test_complete_example_preview_preserves_compiler_order_and_numbering(
    tmp_path: Path,
):
    _, map_preview_result = _preview_api()
    project = _complete_v2_project(tmp_path)
    result = map_preview_result(
        application.preview_service(
            project / "document.md",
        )
    )

    assert result["preview"]["status"] == "ready"
    semantic_blocks = {
        block["selectionId"]: (index, block["content"])
        for index, block in enumerate(result["preview"]["blocks"])
        if block["selectionId"]
        in {
            "fig:architecture",
            "eq:pipeline",
            "tbl:capabilities",
            "alg:build",
            "lst:service",
        }
    }
    assert list(semantic_blocks) == [
        "fig:architecture",
        "eq:pipeline",
        "tbl:capabilities",
        "alg:build",
        "lst:service",
    ]
    assert semantic_blocks["fig:architecture"][1]["label"] == "图1-1"
    assert semantic_blocks["eq:pipeline"][1]["label"] == "(2-1)"
    assert semantic_blocks["tbl:capabilities"][1]["label"] == "表2-1"


def test_preview_serializes_all_inline_run_variants(tmp_path: Path):
    PreviewResult, map_preview_result = _preview_api()
    runs = (
        TextRun("前", bold=True, italic=True),
        ReferenceRun("fig:arch", "fig_arch", "图 1-1"),
        HyperlinkRun("项目主页", "https://example.test"),
        MathRun(r"x^2 + y^2"),
        SoftBreakRun(),
        HardBreakRun(),
        CitationRun(("ref-1",), (1,), raw="[@ref-1]"),
        FootnoteReferenceRun("note", 1),
        TextRun("后"),
    )

    result = map_preview_result(
        PreviewResult(
            document=ForgeDocument(source_path=tmp_path / "thesis.md", blocks=[]),
            context=ValidationContext(),
            issues=(),
            plan=RenderPlan(nodes=(ParagraphInstruction("正文", runs),)),
        )
    )

    assert result["preview"]["blocks"][0]["content"]["runs"] == [
        {
            "type": "text",
            "text": "前",
            "bold": True,
            "italic": True,
        },
        {"type": "reference", "targetId": "fig:arch", "text": "图 1-1"},
        {
            "type": "hyperlink",
            "text": "项目主页",
            "destination": "https://example.test",
        },
        {"type": "math", "latex": r"x^2 + y^2", "text": r"x^2 + y^2"},
        {"type": "soft-break", "text": " "},
        {"type": "hard-break", "text": "\n"},
        {
            "type": "citation",
            "keys": ["ref-1"],
            "ordinals": [1],
            "locator": None,
            "text": "[1]",
        },
        {
            "type": "footnote-reference",
            "label": "note",
            "footnoteId": 1,
            "text": "脚注1",
        },
        {"type": "text", "text": "后"},
    ]

    class ForeignInline:
        pass

    with pytest.raises(TypeError, match=r"unsupported InlineRun: ForeignInline"):
        map_preview_result(
            PreviewResult(
                document=ForgeDocument(
                    source_path=tmp_path / "unknown.md",
                    blocks=[],
                ),
                context=ValidationContext(),
                issues=(),
                plan=RenderPlan(
                    nodes=(ParagraphInstruction("正文", (ForeignInline(),)),),
                ),
            )
        )


def test_preview_mapper_covers_every_typed_instruction_and_unknown_fallback(
    tmp_path: Path,
):
    PreviewResult, map_preview_result = _preview_api()
    blocks = [
        Heading(id="chap:intro", location=SourceLocation(line=10)),
        Paragraph(location=SourceLocation(line=11)),
        CodeBlock(location=SourceLocation(line=12)),
        BlockQuote(location=SourceLocation(line=13)),
        ListBlock(location=SourceLocation(line=14)),
        Figure(
            id="fig:a",
            caption_inlines=_text_inlines("图题"),
            location=SourceLocation(line=15),
        ),
        Table(id="tbl:a", location=SourceLocation(line=16)),
        Equation(id="eq:a", display=True, location=SourceLocation(line=17)),
        Listing(id="lst:a", location=SourceLocation(line=18)),
        Algorithm(id="alg:a", location=SourceLocation(line=19)),
        FootnoteDefinition(label="note", location=SourceLocation(line=20)),
        BibliographyBlock(location=SourceLocation(line=21)),
    ]
    plan = RenderPlan(
        nodes=[
            CoverInstruction(
                bindings=(
                    ("metadata.title.zh", "文档标题"),
                    ("metadata.authors", "作者"),
                )
            ),
            SectionBreakInstruction(role="front_matter"),
            TocInstruction(min_level=1, max_level=3),
            HeadingInstruction("chap:intro", 1, "绪论"),
            ParagraphInstruction("正文", (TextRun("正文"),)),
            CodeBlockInstruction("python", "print(1)\n"),
            BlockQuoteInstruction(
                (ParagraphInstruction("引用正文", (TextRun("引用正文"),)),)
            ),
            ListInstruction(
                ordered=True,
                start=3,
                items=(ListItemInstruction("第三项", 0, 3),),
            ),
            FigureInstruction(
                "fig:a",
                "./missing.png",
                tmp_path / "missing.png",
                CaptionRuns((TextRun("图题"),)),
                None,
                None,
                1,
                "1-1",
                "图 1-1",
                "fig_a",
            ),
            TableInstruction.from_typed_rows(
                source_id="tbl:a",
                caption="表题",
                rows=(
                    TableRowInstruction(
                        True,
                        (
                            TableCellInstruction.from_inlines(
                                (TextRun("A"),),
                                alignment="center",
                            ),
                        ),
                    ),
                ),
                chapter=1,
                number="1-1",
                label="表 1-1",
                bookmark="tbl_a",
            ),
            EquationInstruction(
                "eq:a",
                "x = 1",
                "center",
                1,
                "1-1",
                "式（1-1）",
                "eq_a",
            ),
            ListingInstruction("lst:a", "代码", "python", "print(1)", "lst_a"),
            AlgorithmInstruction("alg:a", "算法", "1. 执行", "alg_a"),
            FootnoteDefinitionInstruction("note", 1, "脚注"),
            BibliographyInstruction(
                (BibliographyEntryInstruction("ref-1", 1, "[1] 文献"),)
            ),
            _unknown_instruction("future-node"),
        ]
    )
    result = map_preview_result(
        PreviewResult(
            document=ForgeDocument(source_path=tmp_path / "thesis.md", blocks=blocks),
            context=ValidationContext(),
            issues=(),
            plan=plan,
        )
    )

    assert [block["content"]["type"] for block in result["preview"]["blocks"]] == [
        "cover",
        "section",
        "toc",
        "text",
        "text",
        "code-block",
        "blockquote",
        "list",
        "figure",
        "table",
        "equation",
        "listing",
        "algorithm",
        "footnote",
        "bibliography",
        "unsupported",
    ]
    figure = next(
        block
        for block in result["preview"]["blocks"]
        if block["content"]["type"] == "figure"
    )
    assert figure["content"]["available"] is False
    assert figure["content"]["label"] == "图 1-1"


def test_preview_mapper_preserves_outline_when_validation_blocks_compile(
    tmp_path: Path,
):
    PreviewResult, map_preview_result = _preview_api()
    result = map_preview_result(
        PreviewResult(
            document=ForgeDocument(
                source_path=tmp_path / "invalid.md",
                blocks=[
                    Heading(
                        id="chap:intro",
                        level=1,
                        inlines=_text_inlines("绪论"),
                        location=SourceLocation(line=4),
                    )
                ],
            ),
            context=ValidationContext(),
            issues=(
                ValidationIssue(
                    code="missing-template",
                    severity="error",
                    message="missing",
                    target="template",
                ),
            ),
            plan=None,
        )
    )

    assert result["outline"][0]["selectionId"] == "chap:intro"
    assert result["preview"] == {
        "status": "blocked",
        "message": "存在 1 个错误诊断，无法生成结构预览。",
        "disclaimer": "结构预览不代表 Word 最终分页。",
        "blocks": [],
    }


def test_preview_outline_uses_inline_text_as_authority(tmp_path: Path):
    _, map_preview_result = _preview_api()
    result = map_preview_result(
        application.PreviewResult(
            document=ForgeDocument(
                source_path=tmp_path / "thesis.md",
                blocks=[
                    Heading(
                        id="chap:intro",
                        level=1,
                        inlines=_text_inlines("真实标题"),
                        location=SourceLocation(line=4),
                    )
                ],
            ),
            context=ValidationContext(),
            issues=(),
            plan=None,
        )
    )

    assert result["outline"][0]["text"] == "真实标题"
