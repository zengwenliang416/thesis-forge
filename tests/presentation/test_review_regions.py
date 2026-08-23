from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import get_args

import pytest

from thesis_forge.application.contracts import PreviewResult
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
    PageBreakInstruction,
    ParagraphInstruction,
    ReferenceRun,
    RenderInstruction,
    RenderNode,
    RenderPlan,
    SectionBreakInstruction,
    SoftBreakRun,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
    TocEntryInstruction,
    TocInstruction,
)
from thesis_forge.core.validator import ValidationContext
from thesis_forge.presentation.review import (
    REVIEW_PROJECTION_REGISTRY,
    ReviewAlgorithmContent,
    ReviewBibliographyContent,
    ReviewCoverContent,
    ReviewDocument,
    ReviewFigureContent,
    ReviewHardBreakRun,
    ReviewHyperlinkRun,
    ReviewListingContent,
    ReviewMathRun,
    ReviewPageBreakContent,
    ReviewParagraphContent,
    ReviewSoftBreakRun,
    ReviewTableContent,
    ReviewTocContent,
    map_review_result,
    project_instruction,
)


def _source_document(source_path: Path) -> ThesisDocument:
    return ThesisDocument(
        source_path=source_path,
        blocks=[
            Heading(
                id="chap:intro",
                inlines=[Text(value="绪论")],
                location=SourceLocation(line=1),
            ),
            Paragraph(
                inlines=[Text(value="正文")],
                location=SourceLocation(line=2),
            ),
            ListBlock(location=SourceLocation(line=3)),
            Figure(id="fig:arch", location=SourceLocation(line=4)),
            Table(id="tbl:data", location=SourceLocation(line=5)),
            Equation(id="eq:loss", location=SourceLocation(line=6)),
            Listing(id="lst:code", location=SourceLocation(line=7)),
            Algorithm(id="alg:flow", location=SourceLocation(line=8)),
            FootnoteDefinition(
                label="scope",
                inlines=[Text(value="脚注正文")],
                location=SourceLocation(line=9),
            ),
            BibliographyBlock(location=SourceLocation(line=10)),
        ],
    )


def _all_region_instructions(tmp_path: Path) -> list[object]:
    asset = tmp_path / "images" / "arch.png"
    asset.parent.mkdir()
    asset.write_bytes(b"png")
    return [
        CoverInstruction(title="论文标题", author="作者"),
        SectionBreakInstruction(role="front_matter"),
        TocInstruction(entries=(TocEntryInstruction("绪论", 1, "chap_intro"),)),
        HeadingInstruction(
            source_id="chap:intro",
            level=1,
            text="绪论",
            inlines=(TextRun("绪论"),),
        ),
        ParagraphInstruction(
            text="文献[@secret-key] [fig:arch]",
            inlines=(
                TextRun("普通 /tmp/leak {#fig:leak} [@secret-key]"),
                CitationRun(
                    keys=("secret-key",),
                    ordinals=(1,),
                    raw="[@secret-key]",
                    text="[@secret-key]",
                ),
                ReferenceRun("fig:arch", "fig_arch", "图 1-1"),
                FootnoteReferenceRun("scope", 1),
            ),
        ),
        ListInstruction(
            ordered=True,
            start=1,
            items=(
                ListItemInstruction(
                    "第一项",
                    level=0,
                    ordinal=1,
                    inlines=(TextRun("第一项"),),
                ),
            ),
        ),
        FigureInstruction(
            source_id="fig:arch",
            src="../images/arch.png",
            asset_path=asset,
            caption=CaptionRuns((TextRun("系统架构"),)),
            width="80%",
            resolved_width=None,
            chapter=1,
            number="1-1",
            label="图 1-1",
            bookmark="fig_arch",
        ),
        TableInstruction.from_typed_rows(
            source_id="tbl:data",
            caption="实验数据",
            rows=(
                TableRowInstruction(
                    header=True,
                    cells=(
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
            bookmark="tbl_data",
        ),
        EquationInstruction(
            source_id="eq:loss",
            latex="x^2",
            alignment="center",
            chapter=1,
            number="1-1",
            label="式（1-1）",
            bookmark="eq_loss",
        ),
        ListingInstruction(
            source_id="lst:code",
            caption="代码示例",
            language="python",
            code="print('literal @fig:inside')",
            bookmark="lst_code",
        ),
        AlgorithmInstruction(
            source_id="alg:flow",
            caption="训练流程",
            body="1. 初始化\n2. 迭代",
            bookmark="alg_flow",
        ),
        FootnoteDefinitionInstruction(
            label="scope",
            footnote_id=1,
            text="脚注正文",
            inlines=(TextRun("脚注正文"),),
        ),
        BibliographyInstruction(
            entries=(
                BibliographyEntryInstruction(
                    key="secret-key",
                    ordinal=1,
                    text="[1] 作者. 标题.",
                ),
            )
        ),
        PageBreakInstruction(),
    ]


def test_registry_covers_every_typed_render_instruction() -> None:
    assert set(REVIEW_PROJECTION_REGISTRY) == set(get_args(RenderInstruction))


def test_review_projects_all_regions_without_visible_technical_markers(
    tmp_path: Path,
) -> None:
    document = _source_document(tmp_path / "thesis.md")
    plan = RenderPlan(nodes=_all_region_instructions(tmp_path))

    review = map_review_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(),
            plan=plan,
        )
    )

    assert isinstance(review, ReviewDocument)
    assert review.status == "ready"
    assert [block.kind for block in review.blocks] == [
        "cover",
        "section_break",
        "toc",
        "heading",
        "paragraph",
        "list",
        "figure",
        "table",
        "equation",
        "listing",
        "algorithm",
        "footnote",
        "bibliography",
        "page_break",
    ]
    assert isinstance(review.blocks[0].content, ReviewCoverContent)
    assert isinstance(review.blocks[2].content, ReviewTocContent)
    assert isinstance(review.blocks[6].content, ReviewFigureContent)
    assert isinstance(review.blocks[7].content, ReviewTableContent)
    assert isinstance(review.blocks[9].content, ReviewListingContent)
    assert isinstance(review.blocks[10].content, ReviewAlgorithmContent)
    assert isinstance(review.blocks[12].content, ReviewBibliographyContent)
    assert isinstance(review.blocks[13].content, ReviewPageBreakContent)

    paragraph = review.blocks[4].content
    assert paragraph.text.startswith("普通")
    assert paragraph.text.endswith("[1]图 1-1脚注1")
    assert "secret-key" not in paragraph.text
    assert "fig:arch" not in paragraph.text
    assert "/tmp" not in paragraph.text

    figure = review.blocks[6].content
    assert figure.available is True
    assert figure.asset_handle.startswith("asset:")
    assert "fig:arch" not in figure.asset_handle

    listing = review.blocks[9].content
    assert "@fig:inside" in listing.code

    assert review.blocks[3].source is not None
    assert review.blocks[3].source.line == 1
    assert review.blocks[3].source.node_id != "chap:intro"

    serialized = json.dumps(asdict(review), ensure_ascii=False)
    for marker in (
        "secret-key",
        "fig:arch",
        "tbl:data",
        "eq:loss",
        "lst:code",
        "alg:flow",
        "fig_arch",
        str(tmp_path),
    ):
        assert marker not in serialized


def test_review_projects_all_inline_run_variants(tmp_path: Path) -> None:
    document = _source_document(tmp_path / "thesis.md")
    plan = RenderPlan(
        nodes=[
            ParagraphInstruction(
                text="",
                inlines=(
                    TextRun("前"),
                    ReferenceRun("fig:arch", "fig_arch", "图 1-1"),
                    HyperlinkRun("项目主页", "https://example.test/project"),
                    MathRun(r"x^2 + y^2"),
                    SoftBreakRun(),
                    HardBreakRun(),
                    CitationRun(
                        keys=("secret-key",),
                        ordinals=(1,),
                        raw="[@secret-key]",
                        text="[@secret-key]",
                    ),
                    FootnoteReferenceRun("scope", 1),
                ),
            )
        ]
    )

    review = map_review_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(),
            plan=plan,
        )
    )

    paragraph = review.blocks[0].content
    assert isinstance(paragraph, ReviewParagraphContent)
    assert paragraph.text == "前图 1-1项目主页x^2 + y^2 \n[1]脚注1"
    assert "https://example.test/project" not in paragraph.text
    assert "secret-key" not in paragraph.text
    assert "fig:arch" not in paragraph.text

    assert isinstance(paragraph.runs[2], ReviewHyperlinkRun)
    assert paragraph.runs[2].text == "项目主页"
    assert paragraph.runs[2].destination == "https://example.test/project"
    assert isinstance(paragraph.runs[3], ReviewMathRun)
    assert paragraph.runs[3].text == "x^2 + y^2"
    assert paragraph.runs[3].latex == r"x^2 + y^2"
    assert isinstance(paragraph.runs[4], ReviewSoftBreakRun)
    assert paragraph.runs[4].text == " "
    assert isinstance(paragraph.runs[5], ReviewHardBreakRun)
    assert paragraph.runs[5].text == "\n"


def test_unknown_inline_run_fails_explicitly() -> None:
    with pytest.raises(TypeError, match="unsupported InlineRun"):
        project_instruction(
            ParagraphInstruction(text="", inlines=(object(),))  # type: ignore[arg-type]
        )


def test_review_blocks_when_plan_is_unavailable(tmp_path: Path) -> None:
    result = PreviewResult(
        document=_source_document(tmp_path / "thesis.md"),
        context=ValidationContext(),
        issues=(),
        plan=None,
    )

    review = map_review_result(result)

    assert review == ReviewDocument(blocks=(), status="blocked", issues=())


def test_unknown_instruction_fails_explicitly() -> None:
    with pytest.raises(TypeError, match="unsupported RenderInstruction"):
        project_instruction(RenderNode(kind="future-node"))  # type: ignore[arg-type]
