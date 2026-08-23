from decimal import Decimal
from pathlib import Path

import pytest

from thesis_forge.bibliography import (
    Gbt7714Formatter,
    LocalBibTeXLoader,
    UnsupportedCitationStyleError,
)
from thesis_forge.core.compiler import (
    BookmarkCollisionError,
    TableCompilationError,
    compile_document,
)
from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    BibliographyConfig,
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
    TableCell,
    TableRow,
    Text,
    ThesisDocument,
)
from thesis_forge.core.parser_backend import create_parser_backend
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
    PageBreakInstruction,
    ParagraphInstruction,
    ReferenceRun,
    SectionBreakInstruction,
    SequenceInstruction,
    TableInstruction,
    TextRun,
    TocEntryInstruction,
    TocInstruction,
)
from thesis_forge.templates import LengthSpec, SectionsSpec, load_template

PARSER = create_parser_backend()


def _text_inlines(value: str) -> list[Text]:
    return [Text(value=value)]


def _structured_table(
    table_id: str | None,
    caption: str,
    header: tuple[tuple[str, str | None], ...],
    body: tuple[tuple[tuple[str, str | None], ...], ...] = (),
) -> Table:
    def row(values: tuple[tuple[str, str | None], ...], *, is_header: bool) -> TableRow:
        return TableRow(
            header=is_header,
            cells=tuple(
                TableCell(inlines=_text_inlines(value), alignment=alignment)
                for value, alignment in values
            ),
        )

    return Table(
        id=table_id,
        caption_inlines=_text_inlines(caption),
        rows=(row(header, is_header=True),)
        + tuple(row(values, is_header=False) for values in body),
    )


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
            Heading(id="chap:intro", level=1, inlines=[Text(value="绪论")]),
            Paragraph(inlines=paragraph_inlines),
            ListBlock(items=[ListItem(inlines=[Text(value="第一项")])]),
            Figure(
                id="fig:model",
                src="model.png",
                caption_inlines=_text_inlines("系统模型"),
            ),
            _structured_table("tbl:data", "数据表", (("A", None),), ((("1", None),),)),
            Equation(id="eq:loss", latex="E=mc^2"),
            Listing(
                id="lst:demo",
                caption_inlines=_text_inlines("示例代码"),
                language="python",
                code="print(1)",
            ),
            Algorithm(
                id="alg:sort",
                caption_inlines=_text_inlines("排序算法"),
                body="1. 输入",
            ),
            FootnoteDefinition(label="note", inlines=[Text(value="脚注正文")]),
            Heading(
                id="chap:method",
                level=1,
                inlines=_text_inlines("方法"),
            ),
            Figure(
                id="fig:flow",
                src="flow.png",
                caption_inlines=_text_inlines("流程"),
            ),
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


def test_compile_document_includes_parsed_container_citations_in_global_order():
    document = PARSER.parse_text(
        '![模型 [@container2026]](./model.png){#fig:model}\n',
        source_path=Path("/tmp/thesis.md"),
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
                inlines=[Text(value="引用"), grouped, Text(value="。")],
            ),
            BibliographyBlock(),
            Paragraph(inlines=[repeated]),
        ],
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
        blocks=[Paragraph(inlines=[citation])],
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
                inlines=[
                    Text(value="先见脚注"),
                    FootnoteReference(label="note"),
                    Text(value="，后见正文引用"),
                    body_citation,
                ],
            ),
            FootnoteDefinition(
                label="note",
                inlines=[Text(value="脚注引用"), footnote_citation],
            ),
        ],
        # Parser registers the body citation before the later footnote definition.
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
            Figure(
                id="fig:a-b",
                src="a.png",
                caption_inlines=_text_inlines("A"),
            ),
            Figure(
                id="fig:a_b",
                src="b.png",
                caption_inlines=_text_inlines("B"),
            ),
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
                caption_inlines=_text_inlines("显式宽度"),
                width="80%",
            ),
            Figure(
                id="fig:default",
                src="./images/default.png",
                caption_inlines=_text_inlines("模板宽度"),
            ),
            _structured_table(
                "tbl:results",
                "实验结果",
                (("模型", "left"), ("AUROC", "right"), ("说明", "center")),
                (
                    (("A", "left"), ("0.91", "right"), ("基线", "center")),
                    (("B", "left"), ("0.94", "right"), ("最优", "center")),
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
    assert table.payload["rows"][0]["cells"][0]["text"] == "模型"


def test_compile_document_rejects_malformed_markdown_table():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Table(
                id="tbl:broken",
                caption_inlines=_text_inlines("坏表格"),
                rows=(
                    TableRow(
                        header=True,
                        cells=(TableCell(inlines=_text_inlines("A")),),
                    ),
                    TableRow(
                        header=False,
                        cells=(
                            TableCell(inlines=_text_inlines("1")),
                            TableCell(inlines=_text_inlines("2")),
                        ),
                    ),
                ),
            )
        ],
    )

    with pytest.raises(TableCompilationError, match="column count"):
        compile_document(document, template=load_template("templates/base/bachelor.yaml"))


def test_compile_document_preserves_equation_display_state():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[Equation(id="eq:inline", latex="x", display=False)],
    )

    plan = compile_document(document)
    equation = next(node for node in plan.nodes if isinstance(node, EquationInstruction))

    assert equation.display is False


def test_compile_document_resolves_sequence_fields_and_footnote_ids():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(
                id="chap:intro",
                level=1,
                inlines=_text_inlines("绪论"),
            ),
            Figure(
                id="fig:model",
                src="model.png",
                caption_inlines=_text_inlines("模型"),
            ),
            _structured_table("tbl:data", "数据", (("A", None),), ((("1", None),),)),
            Equation(id="eq:loss", latex=r"L=\frac{a}{b}"),
            Paragraph(
                inlines=[
                    CrossReference(target="fig:model"),
                    FootnoteReference(label="note"),
                ],
            ),
            FootnoteDefinition(
                label="note",
                inlines=_text_inlines("脚注正文"),
            ),
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
            Heading(
                id="chap:abstract-zh",
                level=1,
                inlines=_text_inlines("摘要"),
            ),
            Paragraph(inlines=_text_inlines("摘要正文")),
            Heading(
                id="chap:introduction",
                level=1,
                inlines=_text_inlines("绪论"),
            ),
        ],
    )

    plan = compile_document(document, template=template)

    assert plan.initial_section_role == "cover"
    assert [type(node) for node in plan.nodes] == [
        SectionBreakInstruction,
        HeadingInstruction,
        ParagraphInstruction,
        PageBreakInstruction,
        TocInstruction,
        SectionBreakInstruction,
        HeadingInstruction,
    ]
    assert plan.nodes[0] == SectionBreakInstruction(role="front_matter")
    assert plan.nodes[3] == PageBreakInstruction()
    assert plan.nodes[4] == TocInstruction(
        min_level=1,
        max_level=3,
        entries=(
            TocEntryInstruction(
                text="摘要",
                level=1,
                bookmark="tf_chap_abstract_zh",
            ),
            TocEntryInstruction(
                text="绪论",
                level=1,
                bookmark="tf_chap_introduction",
            ),
        ),
    )
    assert plan.nodes[5] == SectionBreakInstruction(role="main")


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
        blocks=[
            Heading(
                id="chap:intro",
                level=1,
                inlines=_text_inlines("绪论"),
            )
        ],
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
        blocks=[
            Heading(
                id="chap:abstract-zh",
                level=1,
                inlines=_text_inlines("摘要"),
            )
        ],
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


def test_compile_document_resolves_semantic_heading_and_paragraph_roles():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(
                id="chap:abstract-zh",
                level=1,
                inlines=_text_inlines("摘要"),
            ),
            Paragraph(inlines=_text_inlines("中文摘要正文")),
            Paragraph(
                inlines=_text_inlines("关键词：编译；模板"),
            ),
            Paragraph(
                inlines=_text_inlines("本文讨论关键词：不会误判"),
            ),
            Heading(
                id="chap:abstract-en",
                level=1,
                inlines=_text_inlines("Abstract"),
            ),
            Paragraph(
                inlines=_text_inlines("English abstract body."),
            ),
            Paragraph(
                inlines=_text_inlines("**Keywords:** compiler; template"),
            ),
            Heading(
                id="references",
                level=1,
                inlines=_text_inlines("参考文献"),
            ),
            Paragraph(
                inlines=_text_inlines("[1] Reference entry."),
            ),
            Heading(
                id="acknowledgements",
                level=1,
                inlines=_text_inlines("致谢"),
            ),
            Paragraph(inlines=_text_inlines("感谢所有帮助。")),
            Heading(
                id="achievements",
                level=1,
                inlines=_text_inlines("攻读学位期间的成果"),
            ),
            Paragraph(inlines=_text_inlines("成果说明。")),
            Heading(
                id="chap:introduction",
                level=1,
                inlines=_text_inlines("摘要"),
            ),
            Paragraph(
                inlines=_text_inlines("关键词：普通正文"),
            ),
        ],
    )

    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
    )
    semantic_nodes = [
        node
        for node in plan.nodes
        if isinstance(node, (HeadingInstruction, ParagraphInstruction))
    ]

    assert [node.role for node in semantic_nodes] == [
        "abstract.zh.title",
        "abstract.zh.body",
        "keywords.zh",
        "abstract.zh.body",
        "abstract.en.title",
        "abstract.en.body",
        "keywords.en",
        "bibliography.title",
        "bibliography.entry",
        "special.acknowledgements",
        "body",
        "special.achievements",
        "body",
        None,
        "body",
    ]
    assert semantic_nodes[2].text == "关键词：编译；模板"
    assert semantic_nodes[6].text == "**Keywords:** compiler; template"
    assert semantic_nodes[2].inlines == (TextRun("关键词：编译；模板"),)
    assert semantic_nodes[6].inlines == (
        TextRun("**Keywords:** compiler; template"),
    )
    assert all(isinstance(node.role, str) or node.role is None for node in semantic_nodes)


def test_compile_document_uses_inlines_as_the_authoritative_block_text():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(
                id="chap:abstract-zh",
                level=1,
                inlines=_text_inlines("摘要"),
            ),
            Paragraph(
                inlines=_text_inlines("中文摘要正文"),
            ),
            Paragraph(
                inlines=_text_inlines("关键词：编译；模板"),
            ),
            ListBlock(
                items=[
                    ListItem(
                        inlines=_text_inlines("真实列表项"),
                    )
                ]
            ),
            Paragraph(
                inlines=[CrossReference(target="chap:abstract-zh")],
            ),
            FootnoteDefinition(
                label="note",
                inlines=_text_inlines("真实脚注"),
            ),
        ],
    )

    plan = compile_document(document)

    heading = next(node for node in plan.nodes if isinstance(node, HeadingInstruction))
    paragraphs = [
        node for node in plan.nodes if isinstance(node, ParagraphInstruction)
    ]
    list_instruction = next(
        node for node in plan.nodes if isinstance(node, ListInstruction)
    )
    footnote = next(
        node
        for node in plan.nodes
        if isinstance(node, FootnoteDefinitionInstruction)
    )

    assert heading.text == "摘要"
    assert paragraphs[0].text == "中文摘要正文"
    assert paragraphs[0].role == "abstract.zh.body"
    assert paragraphs[1].text == "关键词：编译；模板"
    assert paragraphs[1].role == "keywords.zh"
    assert list_instruction.items[0].text == "真实列表项"
    assert footnote.text == "真实脚注"
    reference = next(
        run
        for run in paragraphs[2].inlines
        if isinstance(run, ReferenceRun)
    )
    assert reference.display_text == "摘要"


def test_compile_document_preserves_abstract_context_across_nested_headings():
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(
                id="chap:abstract-zh",
                level=1,
                inlines=_text_inlines("摘要"),
            ),
            Heading(
                id="sec:zh-method",
                level=2,
                inlines=_text_inlines("方法"),
            ),
            Paragraph(
                inlines=_text_inlines("中文摘要的分节正文"),
            ),
            Paragraph(
                inlines=_text_inlines("关键词：编译；模板"),
            ),
            Heading(
                id="chap:abstract-en",
                level=1,
                inlines=_text_inlines("Abstract"),
            ),
            Heading(
                id="sec:en-method",
                level=3,
                inlines=_text_inlines("Method"),
            ),
            Paragraph(
                inlines=_text_inlines("English abstract subsection body."),
            ),
            Paragraph(
                inlines=_text_inlines("Keywords: compiler; template"),
            ),
            Heading(
                id="chap:introduction",
                level=1,
                inlines=_text_inlines("绪论"),
            ),
            Paragraph(
                inlines=_text_inlines("关键词：普通正文"),
            ),
        ],
    )

    plan = compile_document(document)
    semantic_nodes = [
        node
        for node in plan.nodes
        if isinstance(node, (HeadingInstruction, ParagraphInstruction))
    ]

    assert [node.role for node in semantic_nodes] == [
        "abstract.zh.title",
        None,
        "abstract.zh.body",
        "keywords.zh",
        "abstract.en.title",
        None,
        "abstract.en.body",
        "keywords.en",
        None,
        "body",
    ]


@pytest.mark.parametrize(
    ("heading_id", "paragraph_text"),
    [
        ("chap:abstract-zh", "正文提到关键词：但标签不在段首"),
        ("chap:abstract-zh", "关键字：不是约定标签"),
        ("chap:abstract-en", "This sentence mentions Keywords: later."),
        ("chap:abstract-en", "Keyword: singular is not the label."),
        ("chap:introduction", "关键词：普通章节不得识别"),
        (None, "Keywords: an unmarked heading is not semantic"),
    ],
)
def test_compile_document_avoids_keyword_false_positives(
    heading_id: str | None,
    paragraph_text: str,
):
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(
                id=heading_id,
                level=1,
                inlines=_text_inlines("摘要"),
            ),
            Paragraph(inlines=_text_inlines(paragraph_text)),
        ],
    )

    first = compile_document(document)
    second = compile_document(document)
    paragraph = next(
        node for node in first.nodes if isinstance(node, ParagraphInstruction)
    )

    assert paragraph.role in {"abstract.zh.body", "abstract.en.body", "body"}
    assert paragraph.role not in {"keywords.zh", "keywords.en"}
    assert first == second


def test_compile_document_selects_provider_from_citation_style():
    fixture = Path(__file__).parent / "fixtures" / "bibliography" / "gbt7714-v1.bib"
    database = LocalBibTeXLoader().load(fixture)
    citation = Citation(keys=["smith2025"], raw="[@smith2025]")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[Paragraph(inlines=[citation])],
        bibliography=BibliographyConfig(
            path="references.bib",
            citation_style="gbt7714-2025-numeric",
        ),
    )

    plan = compile_document(document, bibliography_database=database)

    bibliography = plan.nodes[-1]
    assert isinstance(bibliography, BibliographyInstruction)
    assert bibliography.entries[0].text.startswith(
        "[1] SMITH J, WANG L. Deterministic Thesis Compilation[J]."
    )


def test_compile_document_rejects_unsupported_citation_style():
    fixture = Path(__file__).parent / "fixtures" / "bibliography" / "gbt7714-v1.bib"
    database = LocalBibTeXLoader().load(fixture)
    citation = Citation(keys=["smith2025"], raw="[@smith2025]")
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[Paragraph(inlines=[citation])],
        bibliography=BibliographyConfig(
            path="references.bib",
            citation_style="not-a-style",
        ),
    )

    with pytest.raises(UnsupportedCitationStyleError, match="not-a-style"):
        compile_document(document, bibliography_database=database)
