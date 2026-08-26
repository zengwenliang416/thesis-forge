from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def _next_bookmark_id(paragraph: Paragraph) -> int:
    ids = []
    for element in paragraph.part.element.iter(qn("w:bookmarkStart")):
        value = element.get(qn("w:id"))
        if value is not None and value.isdigit():
            ids.append(int(value))
    return max(ids, default=-1) + 1


def start_bookmark(paragraph: Paragraph, name: str | None) -> str | None:
    if not name:
        return None

    bookmark_id = str(_next_bookmark_id(paragraph))
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), bookmark_id)
    start.set(qn("w:name"), name)
    paragraph._p.append(start)
    return bookmark_id


def end_bookmark(paragraph: Paragraph, bookmark_id: str | None) -> None:
    if bookmark_id is None:
        return
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), bookmark_id)
    paragraph._p.append(end)


def wrap_paragraph_in_bookmark(paragraph: Paragraph, name: str | None) -> None:
    if not name:
        return

    bookmark_id = str(_next_bookmark_id(paragraph))
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), bookmark_id)
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), bookmark_id)

    paragraph_element = paragraph._p
    insert_at = 1 if paragraph_element.pPr is not None else 0
    paragraph_element.insert(insert_at, start)
    paragraph_element.append(end)
