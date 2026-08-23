from __future__ import annotations

import json
from pathlib import Path

import pytest

from thesis_forge import application, presentation
from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    Equation,
    Figure,
    FootnoteDefinition,
    Heading,
    ListBlock,
    Listing,
    Paragraph,
    SourceLocation,
    Table,
    Text,
    ThesisDocument,
    ValidationIssue,
)
from thesis_forge.core.render_plan import (
    AlgorithmInstruction,
    BibliographyEntryInstruction,
    BibliographyInstruction,
    CaptionRuns,
    CitationRun,
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
    RenderNode,
    RenderPlan,
    SectionBreakInstruction,
    SoftBreakRun,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
    TocInstruction,
)
from thesis_forge.core.validator import ValidationContext

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "preview-workbench-v1.json"


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
    document = ThesisDocument(
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
            RenderNode(kind="custom-widget", payload={"private": object()}),
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


def test_complete_example_preview_preserves_compiler_order_and_numbering():
    _, map_preview_result = _preview_api()
    result = map_preview_result(
        application.preview_service(
            ROOT / "examples" / "bachelor-thesis" / "thesis.md",
            template_path=(
                ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
            ),
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
        TextRun("前"),
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
            document=ThesisDocument(source_path=tmp_path / "thesis.md", blocks=[]),
            context=ValidationContext(),
            issues=(),
            plan=RenderPlan(nodes=(ParagraphInstruction("正文", runs),)),
        )
    )

    assert result["preview"]["blocks"][0]["content"]["runs"] == [
        {"type": "text", "text": "前"},
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
                document=ThesisDocument(
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
        ListBlock(location=SourceLocation(line=12)),
        Figure(
            id="fig:a",
            caption_inlines=_text_inlines("图题"),
            location=SourceLocation(line=13),
        ),
        Table(id="tbl:a", location=SourceLocation(line=14)),
        Equation(id="eq:a", display=True, location=SourceLocation(line=15)),
        Listing(id="lst:a", location=SourceLocation(line=16)),
        Algorithm(id="alg:a", location=SourceLocation(line=17)),
        FootnoteDefinition(label="note", location=SourceLocation(line=18)),
        BibliographyBlock(location=SourceLocation(line=19)),
    ]
    plan = RenderPlan(
        nodes=[
            CoverInstruction(title="论文标题", author="作者"),
            SectionBreakInstruction(role="front_matter"),
            TocInstruction(min_level=1, max_level=3),
            HeadingInstruction("chap:intro", 1, "绪论"),
            ParagraphInstruction("正文", (TextRun("正文"),)),
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
            TableInstruction(
                "tbl:a",
                "表题",
                "| A |",
                (
                    TableRowInstruction(
                        True,
                        (TableCellInstruction("A", "center"),),
                    ),
                ),
                1,
                "1-1",
                "表 1-1",
                "tbl_a",
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
            RenderNode(kind="future-node", payload={}),
        ]
    )
    result = map_preview_result(
        PreviewResult(
            document=ThesisDocument(source_path=tmp_path / "thesis.md", blocks=blocks),
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
            document=ThesisDocument(
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
            document=ThesisDocument(
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
