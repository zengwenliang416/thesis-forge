from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from thesis_forge.core.math import (
    LatexMathConverter,
    MathAccent,
    MathConverter,
    MathFraction,
    MathFunction,
    MathLiteral,
    MathNary,
    MathNode,
    MathRadical,
    MathScript,
    MathSequence,
)
from thesis_forge.core.render_plan import EquationInstruction

from .bookmarks import end_bookmark, start_bookmark
from .fields import add_complex_field
from .styles import ALIGNMENTS


def _math_run(text: str):
    run = OxmlElement("m:r")
    value = OxmlElement("m:t")
    value.text = text
    run.append(value)
    return run


def _append_math(parent, node: MathNode) -> None:
    if isinstance(node, MathLiteral):
        parent.append(_math_run(node.value))
        return
    if isinstance(node, MathSequence):
        for item in node.items:
            _append_math(parent, item)
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
        character.set(qn("m:val"), "^" if node.kind == "hat" else "¯")
        properties.append(character)
        element = OxmlElement("m:e")
        _append_math(element, node.base)
        accent.extend((properties, element))
        parent.append(accent)
        return
    raise TypeError(f"Unsupported math node: {type(node).__name__}")


def render_equation(
    document: DocumentObject,
    instruction: EquationInstruction,
    converter: MathConverter | None = None,
) -> None:
    expression = (converter or LatexMathConverter()).convert(instruction.latex)
    paragraph = document.add_paragraph()
    paragraph.alignment = ALIGNMENTS[instruction.alignment]
    math = OxmlElement("m:oMath")
    _append_math(math, expression.root)
    paragraph._p.append(math)

    if instruction.sequence is not None or instruction.label:
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
