from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.presentation.review import (
    ReviewAlgorithmContent,
    ReviewBibliographyContent,
    ReviewBibliographyEntry,
    ReviewBlock,
    ReviewBlockQuoteContent,
    ReviewCitationRun,
    ReviewCodeBlockContent,
    ReviewCoverContent,
    ReviewCoverField,
    ReviewDocument,
    ReviewEquationContent,
    ReviewFigureContent,
    ReviewFootnoteContent,
    ReviewFootnoteReferenceRun,
    ReviewHardBreakRun,
    ReviewHeadingContent,
    ReviewHyperlinkRun,
    ReviewListContent,
    ReviewListingContent,
    ReviewListItem,
    ReviewMathRun,
    ReviewPageBreakContent,
    ReviewParagraphContent,
    ReviewReferenceRun,
    ReviewSectionContent,
    ReviewSoftBreakRun,
    ReviewSource,
    ReviewTableCell,
    ReviewTableContent,
    ReviewTableRow,
    ReviewTextRun,
    ReviewTocContent,
    ReviewTocEntry,
)
from thesis_forge.presentation.review_markdown import (
    render_review_markdown,
    serialize_review_markdown,
)


def _block(
    kind: str,
    content: object,
    *,
    line: int | None = None,
    source: ReviewSource | None = None,
) -> ReviewBlock:
    if source is None and line is not None:
        source = ReviewSource("n1", line=line)
    return ReviewBlock(kind=kind, content=content, source=source)  # type: ignore[arg-type]


def test_serializes_all_review_content_and_keeps_source_map_out_of_markdown() -> None:
    review = ReviewDocument(
        blocks=(
            _block(
                "cover",
                ReviewCoverContent((ReviewCoverField("题目", "论文"),)),
            ),
            _block("section_break", ReviewSectionContent("main")),
            _block(
                "toc",
                ReviewTocContent((ReviewTocEntry("第一章", 1),), 1, 3),
            ),
            _block(
                "heading",
                ReviewHeadingContent(
                    "引言",
                    1,
                    (ReviewTextRun("引言", bold=True),),
                ),
                line=3,
            ),
            _block(
                "paragraph",
                ReviewParagraphContent(
                    "正文",
                    (
                        ReviewTextRun("加粗", bold=True),
                        ReviewTextRun("斜体", italic=True),
                        ReviewTextRun("粗斜体", bold=True, italic=True),
                        ReviewTextRun("代码 @fig:literal", code=True),
                        ReviewReferenceRun("图 1-1"),
                        ReviewCitationRun("[1]"),
                        ReviewFootnoteReferenceRun("脚注1", 1),
                        ReviewHyperlinkRun("项目主页", "https://example.test/project"),
                        ReviewMathRun("x^2", "x^2"),
                        ReviewSoftBreakRun(),
                        ReviewHardBreakRun(),
                    ),
                ),
                line=4,
            ),
            _block(
                "blockquote",
                ReviewBlockQuoteContent(
                    (
                        ReviewParagraphContent(
                            "引用内容",
                            (ReviewTextRun("引用内容", italic=True),),
                        ),
                        ReviewCodeBlockContent("text", "quoted literal"),
                    )
                ),
            ),
            _block(
                "code_block",
                ReviewCodeBlockContent("python", "print('plain')"),
            ),
            _block(
                "list",
                ReviewListContent(
                    True,
                    1,
                    (ReviewListItem("项目", 0, 1), ReviewListItem("子项", 1, 2)),
                ),
            ),
            _block(
                "figure",
                ReviewFigureContent("图 1-1", "架构图", "asset:fig", True, None),
            ),
            _block(
                "table",
                ReviewTableContent(
                    "表 1-1",
                    "数据",
                    (
                        ReviewTableRow(
                            True,
                            (ReviewTableCell("列 A"), ReviewTableCell("列 B")),
                        ),
                        ReviewTableRow(
                            False,
                            (ReviewTableCell("值 A"), ReviewTableCell("值 B")),
                        ),
                    ),
                ),
            ),
            _block("equation", ReviewEquationContent("式 1-1", "x^2 + y^2", "center")),
            _block("listing", ReviewListingContent("代码", "python", "print('@fig:literal')")),
            _block("algorithm", ReviewAlgorithmContent("算法", "1. 读取输入\n2. 输出结果")),
            _block("footnote", ReviewFootnoteContent(1, "脚注定义")),
            _block(
                "bibliography",
                ReviewBibliographyContent((ReviewBibliographyEntry(1, "作者. 标题."),)),
            ),
            _block("page_break", ReviewPageBreakContent()),
        ),
        status="ready",
    )

    result = render_review_markdown(
        review,
        source_name=Path("/private/project/thesis.md"),
        asset_links={"asset:fig": "assets/architecture.png"},
    )

    assert result.markdown == serialize_review_markdown(
        review,
        source_name=Path("/private/project/thesis.md"),
        asset_links={"asset:fig": "assets/architecture.png"},
    )
    assert "GENERATED FILE" in result.markdown
    assert "read-only" in result.markdown
    assert "Source: `thesis.md`" in result.markdown
    assert "![图 1-1 架构图](assets/architecture.png)" in result.markdown
    assert "**加粗**" in result.markdown
    assert "*斜体*" in result.markdown
    assert "***粗斜体***" in result.markdown
    assert "`代码 @fig:literal`" in result.markdown
    assert "> *引用内容*" in result.markdown
    assert "> ```text" in result.markdown
    assert "print('plain')" in result.markdown
    assert "\\(x^2\\)" in result.markdown
    assert "```python" in result.markdown
    assert "print('@fig:literal')" in result.markdown
    assert "**脚注 1**" in result.markdown
    assert "**分页**" in result.markdown
    assert "/private/project" not in result.markdown
    assert all(block.start_line <= block.end_line for block in result.blocks)
    assert result.blocks[3].source == ReviewSource("n1", line=3)
    assert result.blocks[3].generated is False


@pytest.mark.parametrize(
    "link",
    (
        "https://example.test/model.png",
        "/srv/model.png",
        "C:\\models\\model.png",
        "assets/../secret/model.png",
        "assets/%2e%2e%2fsecret/model.png",
        "assets/%252e%252e%252fsecret/model.png",
        "assets/%25252e%25252e%25252fsecret/model.png",
        "assets/%252e%252e%255csecret/model.png",
    ),
)
def test_asset_links_are_project_relative_after_repeated_decoding(link: str) -> None:
    review = ReviewDocument(
        blocks=(
            _block(
                "figure",
                ReviewFigureContent("资源", "模型", "asset:model", True, None),
            ),
        )
    )

    markdown = serialize_review_markdown(
        review,
        asset_links={"asset:model": link},
    )

    assert "![" not in markdown
    assert link not in markdown


def test_visible_text_clears_generic_paths_and_markers_but_not_literal_code() -> None:
    review = ReviewDocument(
        blocks=(
            _block(
                "paragraph",
                ReviewParagraphContent(
                    (
                        "prefix /srv suffix /srv/ "
                        "prefix /srv/private/thesis.md: "
                        "network //server/share/thesis.md "
                        "::: {#fig:model} [@secret] @fig:model"
                    ),
                ),
            ),
            _block(
                "equation",
                ReviewEquationContent("式", "x + /srv/private/thesis.md ::: @eq:loss", "center"),
            ),
            _block(
                "listing",
                ReviewListingContent(
                    "代码",
                    None,
                    "literal /srv {#literal} [@literal] @fig:literal :::",
                ),
            ),
        )
    )

    markdown = serialize_review_markdown(review)

    assert "prefix" in markdown
    assert "/srv" not in markdown.split("```", 1)[0]
    assert "//server/share/thesis.md" not in markdown
    assert "{#fig:model}" not in markdown
    assert "[@secret]" not in markdown
    assert "@fig:model" not in markdown
    assert "literal /srv" in markdown
    assert "{#literal} [@literal] @fig:literal :::" in markdown
    assert "x + " in markdown


def test_partial_is_explicit_and_blocked_does_not_render_supplied_blocks() -> None:
    paragraph = _block("paragraph", ReviewParagraphContent("不要出现"))
    partial = serialize_review_markdown(ReviewDocument((paragraph,), status="partial"))
    blocked = render_review_markdown(
        ReviewDocument((paragraph,), status="blocked"),
        source_name="source.md",
    )

    assert "Review status: partial" in partial
    assert "不要出现" in partial
    assert "Review status: blocked" in blocked.markdown
    assert "不要出现" not in blocked.markdown
    assert blocked.blocks == ()


def test_public_api_rejects_duck_typed_review_values_and_unknown_variants() -> None:
    class DuckReview:
        blocks = ()
        status = "ready"

    class DuckSource:
        node_id = "n1"

    with pytest.raises(TypeError, match="ReviewDocument"):
        serialize_review_markdown(DuckReview())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="ReviewSource"):
        serialize_review_markdown(
            ReviewDocument(
                (
                    ReviewBlock(
                        "paragraph",
                        ReviewParagraphContent("text"),
                        DuckSource(),  # type: ignore[arg-type]
                    ),
                )
            )
        )

    with pytest.raises(TypeError, match="ReviewContent"):
        serialize_review_markdown(
            ReviewDocument((ReviewBlock("paragraph", object()),))  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="ReviewInline"):
        serialize_review_markdown(
            ReviewDocument(
                (
                    ReviewBlock(
                        "paragraph",
                        ReviewParagraphContent("text", (object(),)),  # type: ignore[arg-type]
                    ),
                )
            )
        )


def test_source_metadata_is_present_only_in_returned_map() -> None:
    source = ReviewSource("node:secret", line=12, column=3, end_line=13, end_column=4)
    result = render_review_markdown(
        ReviewDocument(
            (
                ReviewBlock(
                    "paragraph",
                    ReviewParagraphContent("可读内容"),
                    source,
                ),
            )
        )
    )

    assert "node:secret" not in result.markdown
    assert result.blocks == (
        result.blocks[0],
    )
    assert result.blocks[0].source == source
    assert result.blocks[0].start_line == result.blocks[0].end_line
