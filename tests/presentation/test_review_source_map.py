from __future__ import annotations

import json

import pytest

from thesis_forge.presentation.review import (
    ReviewBlock,
    ReviewDocument,
    ReviewHeadingContent,
    ReviewParagraphContent,
    ReviewSource,
)
from thesis_forge.presentation.review_markdown import (
    ReviewMarkdownBlock,
    ReviewMarkdownResult,
    render_review_markdown,
    render_review_source_map,
    serialize_review_source_map,
)


def _result() -> ReviewMarkdownResult:
    return render_review_markdown(
        ReviewDocument(
            blocks=(
                ReviewBlock(
                    "heading",
                    ReviewHeadingContent("标题", 1),
                    ReviewSource(
                        "node:heading",
                        line=4,
                        column=1,
                        end_line=4,
                        end_column=3,
                    ),
                ),
                ReviewBlock(
                    "paragraph",
                    ReviewParagraphContent("生成内容"),
                ),
            )
        )
    )


def test_source_map_preserves_node_id_and_source_span() -> None:
    result = _result()

    source_map = render_review_source_map(result)

    assert source_map["schemaVersion"] == 1
    assert source_map["blocks"][0] == {
        "kind": "heading",
        "startLine": 6,
        "endLine": 6,
        "generated": False,
        "source": {
            "nodeId": "node:heading",
            "sourceSpan": {
                "line": 4,
                "column": 1,
                "endLine": 4,
                "endColumn": 3,
            },
        },
    }


def test_generated_block_is_explicitly_unmapped() -> None:
    source_map = render_review_source_map(_result())

    assert source_map["blocks"][1]["generated"] is True
    assert source_map["blocks"][1]["source"] is None


def test_source_map_ranges_are_one_based_and_within_markdown() -> None:
    result = _result()
    line_count = len(result.markdown.splitlines())

    for block in render_review_source_map(result)["blocks"]:
        assert 1 <= block["startLine"] <= block["endLine"] <= line_count


def test_serialized_source_map_is_stable_and_contains_no_markdown_content() -> None:
    result = _result()

    first = serialize_review_source_map(result)
    second = serialize_review_source_map(result)

    assert first == second
    assert json.loads(first) == render_review_source_map(result)
    assert '"markdown"' not in first
    assert "生成内容" not in first
    assert "/Users/" not in first


def test_source_map_rejects_duck_typed_result_and_block() -> None:
    class DuckResult:
        markdown = "内容\n"
        blocks = ()

    class DuckBlock:
        kind = "paragraph"
        start_line = 1
        end_line = 1
        source = None
        generated = True

    with pytest.raises(TypeError, match="ReviewMarkdownResult"):
        render_review_source_map(DuckResult())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="ReviewMarkdownBlock"):
        render_review_source_map(
            ReviewMarkdownResult("内容\n", (DuckBlock(),))  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("start_line", "end_line"),
    ((0, 1), (2, 1), (1, 3)),
)
def test_source_map_rejects_invalid_line_ranges(
    start_line: int,
    end_line: int,
) -> None:
    result = ReviewMarkdownResult(
        "一行\n",
        (
            ReviewMarkdownBlock(
                "paragraph",
                start_line,
                end_line,
                None,
                True,
            ),
        ),
    )

    with pytest.raises(ValueError, match="line"):
        render_review_source_map(result)


@pytest.mark.parametrize(
    "node_id",
    (
        "/Users/example/thesis.md",
        "C:\\Users\\example\\thesis.md",
        "\\\\server\\share\\thesis.md",
        "node:/private/thesis.md",
        "file:///Users/example/thesis.md",
        "node://server/share/thesis.md",
        "node:%2Fprivate%2Fthesis.md",
        "node:%252Fprivate%252Fthesis.md",
        "node:file:///Users/example/thesis.md",
        "node:file:%2F%2F%2FUsers/example/thesis.md",
        "node:file:%252F%252F%252FUsers/example/thesis.md",
    ),
)
def test_source_map_rejects_absolute_machine_paths_in_node_ids(
    node_id: str,
) -> None:
    result = ReviewMarkdownResult(
        "一行\n",
        (
            ReviewMarkdownBlock(
                "paragraph",
                1,
                1,
                ReviewSource(node_id),
                False,
            ),
        ),
    )

    with pytest.raises(ValueError, match="absolute path"):
        render_review_source_map(result)


@pytest.mark.parametrize(
    ("source", "generated"),
    (
        (None, False),
        (ReviewSource("node:paragraph"), True),
    ),
)
def test_source_map_rejects_inconsistent_generated_marker(
    source: ReviewSource | None,
    generated: bool,
) -> None:
    result = ReviewMarkdownResult(
        "一行\n",
        (
            ReviewMarkdownBlock(
                "paragraph",
                1,
                1,
                source,
                generated,
            ),
        ),
    )

    with pytest.raises(ValueError, match="generated"):
        render_review_source_map(result)


@pytest.mark.parametrize(
    "source",
    (
        ReviewSource("node:paragraph", line=0),
        ReviewSource("node:paragraph", line=4, end_line=3),
        ReviewSource(
            "node:paragraph",
            line=4,
            column=5,
            end_line=4,
            end_column=4,
        ),
        ReviewSource("node:paragraph", column=0),
        ReviewSource("node:paragraph", column=5, end_column=4),
    ),
)
def test_source_map_rejects_invalid_source_spans(source: ReviewSource) -> None:
    result = ReviewMarkdownResult(
        "一行\n",
        (
            ReviewMarkdownBlock(
                "paragraph",
                1,
                1,
                source,
                False,
            ),
        ),
    )

    with pytest.raises(ValueError, match="source span|1-based"):
        render_review_source_map(result)


def test_serialized_source_map_keeps_documented_key_order() -> None:
    serialized = serialize_review_source_map(_result())

    assert serialized.index('"schemaVersion"') < serialized.index('"blocks"')
    assert serialized.index('"kind"') < serialized.index('"startLine"')
    assert serialized.index('"startLine"') < serialized.index('"endLine"')
    assert serialized.index('"endLine"') < serialized.index('"generated"')
    assert serialized.index('"generated"') < serialized.index('"source"')
    assert serialized.index('"nodeId"') < serialized.index('"sourceSpan"')
