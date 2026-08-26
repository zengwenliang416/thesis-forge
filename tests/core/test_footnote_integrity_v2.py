from pathlib import Path

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    Emphasis,
    FootnoteDefinition,
    FootnoteReference,
    ForgeDocument,
    Paragraph,
    SourceLocation,
    Strong,
    Text,
)
from thesis_forge.core.render_plan import FootnoteReferenceRun, ParagraphInstruction
from thesis_forge.core.validator import validate_document


def _document(*blocks: object) -> ForgeDocument:
    return ForgeDocument(source_path=Path("thesis.md"), blocks=list(blocks))


def _footnote_issues(document: ForgeDocument):
    return [
        issue
        for issue in validate_document(document)
        if issue.code in {"duplicate-footnote", "missing-footnote", "nested-footnote"}
    ]


def test_duplicate_definitions_report_both_definition_locations() -> None:
    first = FootnoteDefinition(
        label="scope",
        location=SourceLocation(line=3, column=1, source_file="thesis.md"),
        inlines=[Text(value="第一次定义")],
    )
    duplicate = FootnoteDefinition(
        label="scope",
        location=SourceLocation(line=11, column=1, source_file="thesis.md"),
        inlines=[Text(value="第二次定义")],
    )

    issues = _footnote_issues(_document(first, duplicate))

    assert len(issues) == 1
    assert issues[0].code == "duplicate-footnote"
    assert issues[0].line == 11
    assert issues[0].target == "scope"
    assert issues[0].details == {
        "label": "scope",
        "related_message": "首次定义：scope",
        "source_file": "thesis.md",
        "source_line": 11,
        "source_column": 1,
        "related_file": "thesis.md",
        "related_line": 3,
        "related_column": 1,
    }


def test_missing_definition_is_reported_at_reference_location() -> None:
    reference = FootnoteReference(
        label="missing",
        location=SourceLocation(line=7, column=9, source_file="thesis.md"),
    )

    issues = _footnote_issues(_document(Paragraph(inlines=[reference])))

    assert len(issues) == 1
    assert issues[0].code == "missing-footnote"
    assert issues[0].line == 7
    assert issues[0].target == "missing"
    assert issues[0].details == {
        "label": "missing",
        "source_file": "thesis.md",
        "source_line": 7,
        "source_column": 9,
    }


def test_nested_footnote_reference_is_rejected() -> None:
    nested = FootnoteReference(
        label="inner",
        location=SourceLocation(line=15, column=4, source_file="thesis.md"),
    )
    document = _document(
        FootnoteDefinition(
            label="outer",
            inlines=[Strong(children=(Emphasis(children=(nested,)),))],
        ),
        FootnoteDefinition(label="inner", inlines=[Text(value="内层")]),
    )

    issues = _footnote_issues(document)

    assert [issue.code for issue in issues] == ["nested-footnote"]
    assert issues[0].line == 15
    assert issues[0].target == "inner"
    assert issues[0].details == {
        "definition_label": "outer",
        "source_file": "thesis.md",
        "source_line": 15,
        "source_column": 4,
    }


def test_multiple_references_share_one_definition_and_one_render_id() -> None:
    first = FootnoteReference(label="scope")
    second = FootnoteReference(label="scope")
    document = _document(
        Paragraph(inlines=[first, Text(value="；"), second]),
        FootnoteDefinition(label="scope", inlines=[Text(value="说明")]),
    )

    assert _footnote_issues(document) == []
    plan = compile_document(document)
    paragraph = next(
        node for node in plan.nodes if isinstance(node, ParagraphInstruction)
    )
    references = [
        run for run in paragraph.inlines if isinstance(run, FootnoteReferenceRun)
    ]
    assert [run.footnote_id for run in references] == [1, 1]
