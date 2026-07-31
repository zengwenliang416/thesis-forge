from decimal import Decimal
from pathlib import Path

import pytest

from thesis_forge.bibliography import Gbt7714Formatter, LocalBibTeXLoader
from thesis_forge.core.compiler import (
    BookmarkCollisionError,
    TableCompilationError,
    compile_document,
)
from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    Citation,
    CrossReference,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    Heading,
    ListBlock,
    Listing,
    ListItem,
    Paragraph,
    Table,
    Text,
    ThesisDocument,
)
from thesis_forge.core.render_plan import (
    AlgorithmInstruction,
    BibliographyInstruction,
    CitationRun,
    CoverInstruction,
    EquationInstruction,
    FigureInstruction,
    FigureWidthInstruction,
    FootnoteDefinitionInstruction,
    FootnoteReferenceRun,
    HeadingInstruction,
    ListingInstruction,
    ListInstruction,
    ParagraphInstruction,
    ReferenceRun,
    SectionBreakInstruction,
    SequenceInstruction,
    TableInstruction,
    TocInstruction,
)
from thesis_forge.templates import LengthSpec, SectionsSpec, load_template


def test_compile_document_resolves_typed_instructions_and_global_semantics():
    paragraph_inlines = [
        Text(value="参见"),
        CrossReference(target="fig:model"),
        Text(value="并引用"),
        Citation(keys=["smith2025", "doe2024"], raw="[@smith2025; @doe2024]"),
        Citation(keys=["smith2025"], raw="[@smith2025]"),
    ]
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(id="chap:intro", level=1, text="绪论", inlines=[Text(value="绪论")]),
            Paragraph(text="引用段落", inlines=paragraph_inlines),
            ListBlock(items=[ListItem(text="第一项", inlines=[Text(value="第一项")])]),
            Figure(id="fig:model", src="model.png", caption="系统模型"),
            Table(id="tbl:data", caption="数据表", markdown="| A |\n|---|\n| 1 |"),
            Equation(id="eq:loss", latex="E=mc^2"),
            Listing(id="lst:demo", caption="示例代码", language="python", code="print(1)"),
            Algorithm(id="alg:sort", caption="排序算法", body="1. 输入"),
            FootnoteDefinition(label="note", text="脚注正文", inlines=[Text(value="脚注正文")]),
            Heading(id="chap:method", level=1, text="方法"),
            Figure(id="fig:flow", src="flow.png", caption="流程"),
        ],
    )
    template = load_template("templates/base/bachelor.yaml")

    plan = compile_document(document, template=template, template_path=Path("template.yaml"))

    assert [type(node) for node in plan.nodes] == [
        HeadingInstruction,
        ParagraphInstruction,
        ListInstruction,
        FigureInstruction,
        TableInstruction,
        EquationInstruction,
        ListingInstruction,
        AlgorithmInstruction,
        FootnoteDefinitionInstruction,
        HeadingInstruction,
        FigureInstruction,
    ]
    figures = [node for node in plan.nodes if isinstance(node, FigureInstruction)]
    assert [(node.chapter, node.number, node.label) for node in figures] == [
        (1, "1-1", "图1-1"),
        (2, "2-1", "图2-1"),
    ]
    table = next(node for node in plan.nodes if isinstance(node, TableInstruction))
    equation = next(node for node in plan.nodes if isinstance(node, EquationInstruction))
    assert (table.chapter, table.number, table.label) == (1, "1-1", "表1-1")
    assert (equation.chapter, equation.number, equation.label) == (1, "1-1", "(1-1)")
    assert plan.bookmarks["fig:model"] == "tf_fig_model"
    paragraph = plan.nodes[1]
    assert isinstance(paragraph, ParagraphInstruction)
    assert isinstance(paragraph.inlines[1], ReferenceRun)
    assert paragraph.inlines[1].bookmark == "tf_fig_model"
    assert paragraph.inlines[1].display_text == "图1-1"
    citations = [run for run in paragraph.inlines if isinstance(run, CitationRun)]
    assert [run.ordinals for run in citations] == [(1, 2), (1,)]
    assert plan.citation_order == ("smith2025", "doe2024")
    assert plan.template is template
    assert plan.template_path == Path("template.yaml")
    assert plan.section_policy == template.sections


def test_compile_document_includes_registered_container_citations_in_global_order():
    citation = Citation(keys=["container2026"], raw="[@container2026]")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[Paragraph(text="正文", inlines=[Text(value="正文")])],
        citations=[citation],
    )

    plan = compile_document(document, template=load_template("templates/base/bachelor.yaml"))

    assert plan.citation_order == ("container2026",)


def test_compile_document_formats_citations_and_marker_bibliography_from_database():
    fixture = Path(__file__).parent / "fixtures" / "bibliography" / "gbt7714-v1.bib"
    database = LocalBibTeXLoader().load(fixture)
    grouped = Citation(
        keys=["doe2024", "smith2025"],
        locator="p. 12",
        raw="[@doe2024; @smith2025, p. 12]",
    )
    repeated = Citation(keys=["smith2025"], raw="[@smith2025]")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Paragraph(
                text="引用",
                inlines=[Text(value="引用"), grouped, Text(value="。")],
            ),
            BibliographyBlock(),
            Paragraph(text="再次引用", inlines=[repeated]),
        ],
        citations=[grouped, repeated],
    )

    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
        bibliography_database=database,
        citation_formatter=Gbt7714Formatter(),
    )

    first_paragraph = plan.nodes[0]
    assert isinstance(first_paragraph, ParagraphInstruction)
    citation_run = next(
        run for run in first_paragraph.inlines if isinstance(run, CitationRun)
    )
    assert citation_run.ordinals == (1, 2)
    assert citation_run.text == "[1,2, p. 12]"
    bibliography = plan.nodes[1]
    assert isinstance(bibliography, BibliographyInstruction)
    assert [(entry.key, entry.ordinal) for entry in bibliography.entries] == [
        ("doe2024", 1),
        ("smith2025", 2),
    ]
    assert bibliography.entries[0].text.startswith(
        "[1] DOE J. Structured Academic Documents[M]."
    )
    assert all(entry.key != "uncited2020" for entry in bibliography.entries)


def test_compile_document_appends_bibliography_when_marker_is_absent():
    fixture = Path(__file__).parent / "fixtures" / "bibliography" / "gbt7714-v1.bib"
    database = LocalBibTeXLoader().load(fixture)
    citation = Citation(keys=["smith2025"], raw="[@smith2025]")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[Paragraph(text="引用", inlines=[citation])],
        citations=[citation],
    )

    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
        bibliography_database=database,
    )

    assert isinstance(plan.nodes[-1], BibliographyInstruction)
    assert [entry.key for entry in plan.nodes[-1].entries] == ["smith2025"]


def test_compile_document_orders_footnote_citation_at_reference_position():
    fixture = Path(__file__).parent / "fixtures" / "bibliography" / "gbt7714-v1.bib"
    database = LocalBibTeXLoader().load(fixture)
    body_citation = Citation(keys=["doe2024"], raw="[@doe2024]")
    footnote_citation = Citation(keys=["smith2025"], raw="[@smith2025]")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Paragraph(
                text="先见脚注，后见正文引用",
                inlines=[
                    Text(value="先见脚注"),
                    FootnoteReference(label="note"),
                    Text(value="，后见正文引用"),
                    body_citation,
                ],
            ),
            FootnoteDefinition(
                label="note",
                text="脚注引用",
                inlines=[Text(value="脚注引用"), footnote_citation],
            ),
        ],
        # Parser registers the body citation before the later footnote definition.
        citations=[body_citation, footnote_citation],
    )

    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
        bibliography_database=database,
    )

    assert plan.citation_order == ("smith2025", "doe2024")
    paragraph = next(
        node for node in plan.nodes if isinstance(node, ParagraphInstruction)
    )
    body_run = next(run for run in paragraph.inlines if isinstance(run, CitationRun))
    footnote = next(
        node for node in plan.nodes if isinstance(node, FootnoteDefinitionInstruction)
    )
    footnote_run = next(
        run for run in footnote.inlines if isinstance(run, CitationRun)
    )
    assert body_run.ordinals == (2,)
    assert footnote_run.ordinals == (1,)


def test_compile_document_reports_bookmark_name_collisions():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Figure(id="fig:a-b", src="a.png", caption="A"),
            Figure(id="fig:a_b", src="b.png", caption="B"),
        ],
    )

    with pytest.raises(BookmarkCollisionError) as exc_info:
        compile_document(document, template=load_template("templates/base/bachelor.yaml"))

    assert exc_info.value.bookmark == "tf_fig_a_b"
    assert exc_info.value.source_ids == ("fig:a-b", "fig:a_b")


def test_compile_document_resolves_figure_assets_widths_and_structured_table_rows(
    tmp_path: Path,
):
    source_path = tmp_path / "chapter" / "thesis.md"
    template = load_template("templates/base/bachelor.yaml")
    template.figure.default_width = LengthSpec.model_validate("120mm")
    document = ThesisDocument(
        source_path=source_path,
        blocks=[
            Figure(
                id="fig:explicit",
                src="./images/model.png",
                caption="显式宽度",
                width="80%",
            ),
            Figure(
                id="fig:default",
                src="./images/default.png",
                caption="模板宽度",
            ),
            Table(
                id="tbl:results",
                caption="实验结果",
                markdown=(
                    "| 模型 | AUROC | 说明 |\n"
                    "| :--- | ---: | :---: |\n"
                    "| A | 0.91 | 基线 |\n"
                    "| B | 0.94 | 最优 |"
                ),
            ),
        ],
    )

    plan = compile_document(document, template=template)

    explicit, default = [
        node for node in plan.nodes if isinstance(node, FigureInstruction)
    ]
    assert explicit.asset_path == tmp_path / "chapter" / "images" / "model.png"
    assert explicit.resolved_width == FigureWidthInstruction(
        value=Decimal(80),
        unit="percent",
        origin="source",
    )
    assert default.asset_path == tmp_path / "chapter" / "images" / "default.png"
    assert default.resolved_width == FigureWidthInstruction(
        value=Decimal(120),
        unit="mm",
        origin="template",
    )

    table = next(node for node in plan.nodes if isinstance(node, TableInstruction))
    assert [row.header for row in table.rows] == [True, False, False]
    assert [[cell.text for cell in row.cells] for row in table.rows] == [
        ["模型", "AUROC", "说明"],
        ["A", "0.91", "基线"],
        ["B", "0.94", "最优"],
    ]
    assert [cell.alignment for cell in table.rows[0].cells] == [
        "left",
        "right",
        "center",
    ]
    assert table.markdown.startswith("| 模型 |")


def test_compile_document_rejects_malformed_markdown_table():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Table(
                id="tbl:broken",
                caption="坏表格",
                markdown="| A | B |\n| --- |\n| 1 | 2 |",
            )
        ],
    )

    with pytest.raises(TableCompilationError, match="column count"):
        compile_document(document, template=load_template("templates/base/bachelor.yaml"))


def test_compile_document_resolves_sequence_fields_and_footnote_ids():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(id="chap:intro", level=1, text="绪论"),
            Figure(id="fig:model", src="model.png", caption="模型"),
            Table(id="tbl:data", caption="数据", markdown="| A |\n| --- |\n| 1 |"),
            Equation(id="eq:loss", latex=r"L=\frac{a}{b}"),
            Paragraph(
                text="说明",
                inlines=[
                    CrossReference(target="fig:model"),
                    FootnoteReference(label="note"),
                ],
            ),
            FootnoteDefinition(label="note", text="脚注正文"),
        ],
    )

    plan = compile_document(document, template=load_template("templates/base/bachelor.yaml"))

    figure = next(node for node in plan.nodes if isinstance(node, FigureInstruction))
    table = next(node for node in plan.nodes if isinstance(node, TableInstruction))
    equation = next(node for node in plan.nodes if isinstance(node, EquationInstruction))
    paragraph = next(node for node in plan.nodes if isinstance(node, ParagraphInstruction))
    footnote = next(
        node for node in plan.nodes if isinstance(node, FootnoteDefinitionInstruction)
    )
    assert figure.sequence == SequenceInstruction(
        name="TF_Figure_1",
        value=1,
        prefix="图1-",
        suffix="",
        result="图1-1",
    )
    assert table.sequence == SequenceInstruction(
        name="TF_Table_1",
        value=1,
        prefix="表1-",
        suffix="",
        result="表1-1",
    )
    assert equation.sequence == SequenceInstruction(
        name="TF_Equation_1",
        value=1,
        prefix="(1-",
        suffix=")",
        result="(1-1)",
    )
    footnote_run = next(
        run for run in paragraph.inlines if isinstance(run, FootnoteReferenceRun)
    )
    assert footnote_run.footnote_id == 1
    assert footnote.footnote_id == 1


def test_compile_document_emits_toc_and_explicit_section_transitions():
    template = load_template("templates/base/bachelor.yaml")
    template.sections = SectionsSpec.model_validate(
        {
            "cover": {
                "start": "new_page",
                "page_number": {"format": "none"},
            },
            "front_matter": {
                "start": "new_page",
                "footer": {"enabled": True},
                "page_number": {"format": "roman-lower"},
            },
            "main": {
                "start": "odd_page",
                "header": {"enabled": True, "text": "论文标题"},
                "footer": {"enabled": True},
                "page_number": {"format": "decimal", "restart": 1},
            },
        }
    )
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(id="chap:abstract-zh", level=1, text="摘要"),
            Paragraph(text="摘要正文"),
            Heading(id="chap:introduction", level=1, text="绪论"),
        ],
    )

    plan = compile_document(document, template=template)

    assert plan.initial_section_role == "cover"
    assert [type(node) for node in plan.nodes] == [
        SectionBreakInstruction,
        HeadingInstruction,
        ParagraphInstruction,
        TocInstruction,
        SectionBreakInstruction,
        HeadingInstruction,
    ]
    assert plan.nodes[0] == SectionBreakInstruction(role="front_matter")
    assert plan.nodes[3] == TocInstruction(min_level=1, max_level=3)
    assert plan.nodes[4] == SectionBreakInstruction(role="main")


def test_compile_document_transitions_directly_from_cover_to_main():
    template = load_template("templates/base/bachelor.yaml")
    template.sections = SectionsSpec.model_validate(
        {
            "cover": {
                "start": "new_page",
                "page_number": {"format": "none"},
            },
            "main": {
                "start": "new_page",
                "page_number": {"format": "decimal", "restart": 1},
            },
        }
    )
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[Heading(id="chap:intro", level=1, text="绪论")],
    )

    plan = compile_document(document, template=template)

    assert plan.initial_section_role == "cover"
    assert plan.nodes[0] == SectionBreakInstruction(role="main")
    assert isinstance(plan.nodes[1], HeadingInstruction)
    assert not any(isinstance(node, TocInstruction) for node in plan.nodes)


def test_compile_document_emits_renderer_neutral_cover_from_front_matter():
    template = load_template("templates/schools/example-university/2026.yaml")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        metadata={
            "university": {"name": "XX大学", "college": "计算机学院"},
            "thesis": {
                "title": "结构化论文编译",
                "title_en": "Structured Thesis Compilation",
                "major": "计算机科学与技术",
                "degree": "工学学士",
            },
            "author": {"name": "张三", "student_id": "2022000001"},
            "advisor": {"name": "李老师", "title": "副教授"},
            "dates": {"completed": "2026-06"},
        },
        blocks=[Heading(id="chap:abstract-zh", level=1, text="摘要")],
    )

    plan = compile_document(document, template=template)

    assert plan.nodes[0] == CoverInstruction(
        university="XX大学",
        college="计算机学院",
        title="结构化论文编译",
        title_en="Structured Thesis Compilation",
        major="计算机科学与技术",
        degree="工学学士",
        author="张三",
        student_id="2022000001",
        advisor="李老师",
        advisor_title="副教授",
        completed="2026-06",
    )
    assert plan.nodes[0].payload["student_id"] == "2022000001"
    assert plan.nodes[1] == SectionBreakInstruction(role="front_matter")
