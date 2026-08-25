from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu

from thesis_forge.core.math import (
    LatexMathConverter,
    MathAccent,
    MathBinomial,
    MathConverter,
    MathDelimiter,
    MathEquationArray,
    MathFraction,
    MathFunction,
    MathLimitFunction,
    MathLiteral,
    MathMatrix,
    MathNary,
    MathNode,
    MathRadical,
    MathScript,
    MathSequence,
    MathTextRun,
)
from thesis_forge.core.render_plan import EquationInstruction

from .bookmarks import end_bookmark, start_bookmark
from .fields import add_complex_field
from .styles import ALIGNMENTS

XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

ACCENT_CHARACTERS = {
    "hat": "^",
    "bar": "¯",
    "vec": "→",
    "dot": "˙",
    "ddot": "¨",
    "tilde": "~",
}


def _content_width_twips(document: DocumentObject) -> int:
    section = document.sections[-1]
    content_width = (
        int(section.page_width)
        - int(section.left_margin)
        - int(section.right_margin)
    )
    if content_width <= 0:
        raise ValueError("equation tabs require positive content width")
    return Emu(content_width).twips


def _configure_numbered_equation_tabs(
    document: DocumentObject,
    paragraph,
) -> None:
    content_width = _content_width_twips(document)
    paragraph.alignment = ALIGNMENTS["left"]
    paragraph_properties = paragraph._p.get_or_add_pPr()
    tabs = paragraph_properties.find(qn("w:tabs"))
    if tabs is None:
        tabs = OxmlElement("w:tabs")
        paragraph_properties.insert_element_before(
            tabs,
            "w:spacing",
            "w:ind",
            "w:jc",
            "w:outlineLvl",
            "w:rPr",
        )

    for alignment, position in (
        ("center", content_width // 2),
        ("right", content_width),
    ):
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), alignment)
        tab.set(qn("w:pos"), str(position))
        tabs.append(tab)


def _math_run(text: str, *, upright: bool = False, normal: bool = False):
    run = OxmlElement("m:r")
    if upright or normal:
        properties = OxmlElement("m:rPr")
        if normal:
            properties.append(OxmlElement("m:nor"))
        style = OxmlElement("m:sty")
        style.set(qn("m:val"), "p")
        properties.append(style)
        run.append(properties)
    value = OxmlElement("m:t")
    if text != text.strip():
        value.set(XML_SPACE, "preserve")
    value.text = text
    run.append(value)
    return run


def _wrap_delimiter(left: str | None, right: str | None, element):
    """Wrap the prepared m:e ``element`` in a growing m:d pair (``None`` hides a side)."""
    delimiter = OxmlElement("m:d")
    properties = OxmlElement("m:dPr")
    begin = OxmlElement("m:begChr")
    begin.set(qn("m:val"), left or "")
    properties.append(begin)
    separator = OxmlElement("m:sepChr")
    separator.set(qn("m:val"), "")
    properties.append(separator)
    end = OxmlElement("m:endChr")
    end.set(qn("m:val"), right or "")
    properties.append(end)
    properties.append(OxmlElement("m:grow"))
    delimiter.append(properties)
    delimiter.append(element)
    return delimiter


def _build_matrix(node: MathMatrix):
    matrix = OxmlElement("m:m")
    properties = OxmlElement("m:mPr")
    base_alignment = OxmlElement("m:baseJc")
    base_alignment.set(qn("m:val"), "center")
    properties.append(base_alignment)
    placeholder_hidden = OxmlElement("m:plcHide")
    placeholder_hidden.set(qn("m:val"), "on")
    properties.append(placeholder_hidden)
    columns = OxmlElement("m:mcs")
    column_count = max(len(row) for row in node.rows)
    for _ in range(column_count):
        column = OxmlElement("m:mc")
        column_properties = OxmlElement("m:mcPr")
        column_alignment = OxmlElement("m:mcJc")
        column_alignment.set(qn("m:val"), node.column_alignment)
        column_properties.append(column_alignment)
        count = OxmlElement("m:count")
        count.set(qn("m:val"), "1")
        column_properties.append(count)
        column.append(column_properties)
        columns.append(column)
    properties.append(columns)
    matrix.append(properties)
    for row in node.rows:
        matrix_row = OxmlElement("m:mr")
        for cell in row:
            element = OxmlElement("m:e")
            _append_math(element, cell)
            matrix_row.append(element)
        matrix.append(matrix_row)
    return matrix


def _append_math(parent, node: MathNode) -> None:
    if isinstance(node, MathLiteral):
        parent.append(_math_run(node.value))
        return
    if isinstance(node, MathSequence):
        for item in node.items:
            _append_math(parent, item)
        return
    if isinstance(node, MathTextRun):
        parent.append(
            _math_run(
                node.text,
                normal=node.style == "text",
                upright=node.style == "mathrm",
            )
        )
        return
    if isinstance(node, MathFraction):
        fraction = OxmlElement("m:f")
        numerator = OxmlElement("m:num")
        denominator = OxmlElement("m:den")
        _append_math(numerator, node.numerator)
        _append_math(denominator, node.denominator)
        fraction.extend((numerator, denominator))
        parent.append(fraction)
        return
    if isinstance(node, MathBinomial):
        fraction = OxmlElement("m:f")
        properties = OxmlElement("m:fPr")
        fraction_type = OxmlElement("m:type")
        fraction_type.set(qn("m:val"), "noBar")
        properties.append(fraction_type)
        fraction.append(properties)
        numerator = OxmlElement("m:num")
        denominator = OxmlElement("m:den")
        _append_math(numerator, node.top)
        _append_math(denominator, node.bottom)
        fraction.extend((numerator, denominator))
        element = OxmlElement("m:e")
        element.append(fraction)
        parent.append(_wrap_delimiter("(", ")", element))
        return
    if isinstance(node, MathRadical):
        radical = OxmlElement("m:rad")
        properties = OxmlElement("m:radPr")
        degree_hidden = OxmlElement("m:degHide")
        degree_hidden.set(qn("m:val"), "1")
        properties.append(degree_hidden)
        element = OxmlElement("m:e")
        _append_math(element, node.radicand)
        radical.extend((properties, element))
        parent.append(radical)
        return
    if isinstance(node, MathScript):
        if node.subscript is not None and node.superscript is not None:
            script = OxmlElement("m:sSubSup")
        elif node.subscript is not None:
            script = OxmlElement("m:sSub")
        else:
            script = OxmlElement("m:sSup")
        element = OxmlElement("m:e")
        _append_math(element, node.base)
        script.append(element)
        if node.subscript is not None:
            subscript = OxmlElement("m:sub")
            _append_math(subscript, node.subscript)
            script.append(subscript)
        if node.superscript is not None:
            superscript = OxmlElement("m:sup")
            _append_math(superscript, node.superscript)
            script.append(superscript)
        parent.append(script)
        return
    if isinstance(node, MathNary):
        nary = OxmlElement("m:nary")
        properties = OxmlElement("m:naryPr")
        character = OxmlElement("m:chr")
        character.set(qn("m:val"), node.operator)
        properties.append(character)
        limit_location = OxmlElement("m:limLoc")
        limit_location.set(qn("m:val"), "subSup")
        properties.append(limit_location)
        if node.lower is None:
            hidden = OxmlElement("m:subHide")
            hidden.set(qn("m:val"), "1")
            properties.append(hidden)
        if node.upper is None:
            hidden = OxmlElement("m:supHide")
            hidden.set(qn("m:val"), "1")
            properties.append(hidden)
        nary.append(properties)
        if node.lower is not None:
            lower = OxmlElement("m:sub")
            _append_math(lower, node.lower)
            nary.append(lower)
        if node.upper is not None:
            upper = OxmlElement("m:sup")
            _append_math(upper, node.upper)
            nary.append(upper)
        nary.append(OxmlElement("m:e"))
        parent.append(nary)
        return
    if isinstance(node, MathLimitFunction):
        current = _math_run(node.name, upright=True)
        if node.upper is not None:
            limit_upper = OxmlElement("m:limUpp")
            element = OxmlElement("m:e")
            element.append(current)
            limit_upper.append(element)
            limit = OxmlElement("m:lim")
            _append_math(limit, node.upper)
            limit_upper.append(limit)
            current = limit_upper
        if node.lower is not None:
            limit_lower = OxmlElement("m:limLow")
            element = OxmlElement("m:e")
            element.append(current)
            limit_lower.append(element)
            limit = OxmlElement("m:lim")
            _append_math(limit, node.lower)
            limit_lower.append(limit)
            current = limit_lower
        parent.append(current)
        return
    if isinstance(node, MathFunction):
        function = OxmlElement("m:func")
        name = OxmlElement("m:fName")
        name.append(_math_run(node.name))
        argument = OxmlElement("m:e")
        _append_math(argument, node.argument)
        function.extend((name, argument))
        parent.append(function)
        return
    if isinstance(node, MathAccent):
        accent = OxmlElement("m:acc")
        properties = OxmlElement("m:accPr")
        character = OxmlElement("m:chr")
        character.set(qn("m:val"), ACCENT_CHARACTERS[node.kind])
        properties.append(character)
        element = OxmlElement("m:e")
        _append_math(element, node.base)
        accent.extend((properties, element))
        parent.append(accent)
        return
    if isinstance(node, MathDelimiter):
        element = OxmlElement("m:e")
        _append_math(element, node.body)
        parent.append(_wrap_delimiter(node.left, node.right, element))
        return
    if isinstance(node, MathMatrix):
        matrix = _build_matrix(node)
        if node.left is None and node.right is None:
            parent.append(matrix)
            return
        element = OxmlElement("m:e")
        element.append(matrix)
        parent.append(_wrap_delimiter(node.left, node.right, element))
        return
    if isinstance(node, MathEquationArray):
        array = OxmlElement("m:eqArr")
        for row in node.rows:
            element = OxmlElement("m:e")
            for index, cell in enumerate(row):
                if index:
                    # OMML alignment marker inside an equation array row,
                    # same convention as pandoc/texmath output.
                    element.append(_math_run("&"))
                _append_math(element, cell)
            array.append(element)
        parent.append(array)
        return
    raise TypeError(f"Unsupported math node: {type(node).__name__}")


def render_equation(
    document: DocumentObject,
    instruction: EquationInstruction,
    converter: MathConverter | None = None,
    *,
    omml_provider=None,
) -> None:
    """渲染公式段落（OMML + 编号/书签/SEQ 字段包装，包装点不迁移）。

    ``omml_provider`` 显式传入可选外部 provider（ADR-0003 §2.4，如
    ``PandocMathProvider``）时，``m:oMath`` 片段改由 provider 产出，
    AST 转换路径（``converter``/``LatexMathConverter``）跳过；其余包装
    （对齐、书签、SEQ ``\\r`` 钉值、题注）两条链路完全一致。默认 None
    走离线确定性内建引擎，编译路径不依赖任何外部可执行文件。
    """

    paragraph = document.add_paragraph()
    numbered = instruction.sequence is not None or bool(instruction.label)
    centered_numbered = numbered and instruction.alignment == "center"
    if centered_numbered:
        _configure_numbered_equation_tabs(document, paragraph)
        paragraph.add_run("\t")
    else:
        paragraph.alignment = ALIGNMENTS[instruction.alignment]

    if omml_provider is not None:
        math = omml_provider.convert_to_omml(instruction.latex, display=True)
    else:
        expression = (converter or LatexMathConverter()).convert(instruction.latex)
        math = OxmlElement("m:oMath")
        _append_math(math, expression.root)
    paragraph._p.append(math)

    if numbered:
        paragraph.add_run("\t")
    bookmark_id = start_bookmark(paragraph, instruction.bookmark)
    if instruction.sequence is not None:
        add_complex_field(
            paragraph,
            instruction.sequence.field_code,
            result=str(instruction.sequence.value),
            prefix=instruction.sequence.prefix,
            suffix=instruction.sequence.suffix,
        )
    elif instruction.label:
        paragraph.add_run(instruction.label)
    end_bookmark(paragraph, bookmark_id)
