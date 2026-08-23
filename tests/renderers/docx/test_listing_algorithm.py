from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree

from thesis_forge.application.contracts import PreviewResult
from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import Algorithm, Listing
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend
from thesis_forge.core.render_plan import (
    AlgorithmInstruction,
    ListingInstruction,
    RenderNode,
    RenderPlan,
    SequenceInstruction,
)
from thesis_forge.core.validator import ValidationContext
from thesis_forge.presentation.review import (
    ReviewAlgorithmContent,
    ReviewListingContent,
    map_review_result,
)
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.renderers.docx.errors import DocxRenderError
from thesis_forge.templates import load_template
from thesis_forge.templates.model import (
    AlgorithmSpec,
    CaptionSpec,
    FontSpec,
    LengthSpec,
    ListingSpec,
    NumberingSpec,
)

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


@dataclass(frozen=True, slots=True)
class UnknownInstruction:
    kind: str = "unknown"


def _xml_part(path: Path, name: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(name))


def _bookmark_text(paragraph, bookmark_name: str) -> str:
    bookmark_start = paragraph.xpath(
        f"./w:bookmarkStart[@w:name='{bookmark_name}']",
        namespaces=NS,
    )[0]
    bookmark_end = paragraph.xpath(
        "./w:bookmarkEnd[@w:id=$bookmark_id]",
        namespaces=NS,
        bookmark_id=bookmark_start.get(f"{{{NS['w']}}}id"),
    )[0]
    children = list(paragraph)
    start_index = children.index(bookmark_start)
    end_index = children.index(bookmark_end)
    return "".join(
        text
        for child in children[start_index + 1 : end_index]
        for text in child.xpath(".//w:t/text()", namespaces=NS)
    )


def _paragraph_text(paragraph) -> str:
    chunks: list[str] = []
    for node in paragraph.xpath(".//w:t | .//w:br | .//w:cr", namespaces=NS):
        if etree.QName(node).localname in {"br", "cr"}:
            chunks.append("\n")
        else:
            chunks.append(node.text or "")
    return "".join(chunks)


def _template():
    base = load_template("templates/base/bachelor.yaml")
    return base.model_copy(
        update={
            "listing": ListingSpec(
                numbering=NumberingSpec(mode="chapter", separator="-"),
                caption=CaptionSpec(
                    position="top",
                    prefix="代码",
                    alignment="left",
                    font=FontSpec(east_asia="黑体", latin="Arial"),
                    size=LengthSpec.model_validate("10pt"),
                ),
            ),
            "algorithm": AlgorithmSpec(
                numbering=NumberingSpec(mode="continuous"),
                caption=CaptionSpec(
                    position="top",
                    prefix="算法",
                    alignment="right",
                    font=FontSpec(east_asia="楷体", latin="Georgia"),
                    size=LengthSpec.model_validate("11pt"),
                ),
            ),
        }
    )


def test_docx_renders_listing_algorithm_capability_end_to_end(tmp_path: Path) -> None:
    source_path = tmp_path / "thesis.md"
    document = MarkdownItParserBackend().parse_text(
        """# 第一章 {#chap:intro}

```python {#lst:service title="构建服务"}
print("@fig:inside")
# [@literal] {#code-id} /tmp/keep
```

```algorithm {#alg:build title="安全构建"}
1. 读取输入
2. 执行渲染
```
""",
        source_path=source_path,
    )
    template = _template()
    plan = compile_document(document, template=template)

    source_listing = next(
        block for block in document.blocks if isinstance(block, Listing)
    )
    source_algorithm = next(
        block for block in document.blocks if isinstance(block, Algorithm)
    )
    expected_listing_code = (
        'print("@fig:inside")\n# [@literal] {#code-id} /tmp/keep'
    )
    expected_algorithm_body = "1. 读取输入\n2. 执行渲染"
    assert source_listing.code == expected_listing_code
    assert source_algorithm.body == expected_algorithm_body

    listing = next(
        node for node in plan.nodes if isinstance(node, ListingInstruction)
    )
    algorithm = next(
        node for node in plan.nodes if isinstance(node, AlgorithmInstruction)
    )
    review = map_review_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(),
            plan=plan,
        )
    )
    review_listing = next(
        block.content
        for block in review.blocks
        if block.kind == "listing"
    )
    review_algorithm = next(
        block.content
        for block in review.blocks
        if block.kind == "algorithm"
    )
    assert isinstance(review_listing, ReviewListingContent)
    assert isinstance(review_algorithm, ReviewAlgorithmContent)
    assert review_listing.caption == "构建服务"
    assert review_listing.code == source_listing.code == listing.code
    assert review_algorithm.caption == "安全构建"
    assert review_algorithm.body == source_algorithm.body == algorithm.body

    output = tmp_path / "listing-algorithm.docx"
    DocxRenderer().render(plan, output)

    document_xml = _xml_part(output, "word/document.xml")
    listing_caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_lst_service']]",
        namespaces=NS,
    )[0]
    algorithm_caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_alg_build']]",
        namespaces=NS,
    )[0]

    assert listing_caption.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["left"]
    assert algorithm_caption.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["right"]
    assert listing_caption.xpath(
        ".//w:instrText/text()",
        namespaces=NS,
    ) == ["SEQ TF_Listing_1 \\r 1 \\* ARABIC"]
    assert algorithm_caption.xpath(
        ".//w:instrText/text()",
        namespaces=NS,
    ) == ["SEQ TF_Algorithm \\r 1 \\* ARABIC"]
    assert "".join(listing_caption.xpath(".//w:t/text()", namespaces=NS)) == (
        "代码1-1 构建服务"
    )
    assert "".join(algorithm_caption.xpath(".//w:t/text()", namespaces=NS)) == (
        "算法1 安全构建"
    )
    assert set(
        listing_caption.xpath(".//w:rFonts/@w:eastAsia", namespaces=NS)
    ) == {"黑体"}
    assert set(
        algorithm_caption.xpath(".//w:rFonts/@w:eastAsia", namespaces=NS)
    ) == {"楷体"}
    assert set(listing_caption.xpath(".//w:sz/@w:val", namespaces=NS)) == {"20"}
    assert set(algorithm_caption.xpath(".//w:sz/@w:val", namespaces=NS)) == {"22"}

    for caption, bookmark_name, expected_label in (
        (listing_caption, "tf_lst_service", "代码1-1"),
        (algorithm_caption, "tf_alg_build", "算法1"),
    ):
        bookmark_start = caption.xpath("./w:bookmarkStart", namespaces=NS)[0]
        bookmark_end = caption.xpath(
            "./w:bookmarkEnd[@w:id=$bookmark_id]",
            namespaces=NS,
            bookmark_id=bookmark_start.get(f"{{{NS['w']}}}id"),
        )[0]
        field_chars = caption.xpath(".//w:fldChar", namespaces=NS)
        assert [
            field.get(f"{{{NS['w']}}}fldCharType") for field in field_chars
        ] == ["begin", "separate", "end"]
        assert field_chars[0].get(f"{{{NS['w']}}}dirty") == "true"
        children = list(caption)
        start_index = children.index(bookmark_start)
        end_index = children.index(bookmark_end)
        assert any(
            child.xpath(".//w:instrText", namespaces=NS)
            for child in children[start_index + 1 : end_index]
        )
        assert _bookmark_text(caption, bookmark_name) == expected_label

    listing_code = document_xml.xpath(
        ".//w:p[.//w:t[contains(., 'print(\"@fig:inside\")')]]",
        namespaces=NS,
    )[0]
    algorithm_body = document_xml.xpath(
        ".//w:p[.//w:t[contains(., '1. 读取输入')]]",
        namespaces=NS,
    )[0]
    assert listing_code.xpath(".//w:rFonts/@w:ascii", namespaces=NS) == [
        "Courier New"
    ]
    assert algorithm_body.xpath(".//w:rFonts/@w:ascii", namespaces=NS) == [
        "Courier New"
    ]
    assert _paragraph_text(listing_code) == expected_listing_code
    assert _paragraph_text(algorithm_body) == expected_algorithm_body
    caption_text = "".join(
        listing_caption.xpath(".//w:t/text()", namespaces=NS)
        + algorithm_caption.xpath(".//w:t/text()", namespaces=NS)
    )
    assert "lst:service" not in caption_text
    assert "alg:build" not in caption_text
    assert "tf_lst_service" not in caption_text
    assert "tf_alg_build" not in caption_text
    assert "[@citation-key]" not in caption_text
    assert "{#caption-id}" not in caption_text
    assert str(source_path) not in caption_text


@pytest.mark.parametrize(
    "instruction",
    [
        UnknownInstruction(),
        RenderNode(kind="unknown", payload={"x": 1}),
    ],
)
def test_docx_rejects_unknown_instruction_instead_of_debug_fallback(
    tmp_path: Path,
    instruction,
) -> None:
    with pytest.raises(DocxRenderError, match="unsupported instruction"):
        DocxRenderer().render(
            RenderPlan(nodes=[instruction]),
            tmp_path / "unsupported.docx",
        )


def test_docx_honors_bottom_caption_positions(tmp_path: Path) -> None:
    template = _template()
    template.listing.caption.position = "bottom"
    template.algorithm.caption.position = "bottom"
    plan = RenderPlan(
        template=template,
        nodes=[
            ListingInstruction(
                source_id="lst:bottom",
                caption="标题",
                language="python",
                code="print(1)",
                bookmark="tf_lst_bottom",
                label="代码1",
                sequence=SequenceInstruction(
                    name="TF_Listing_1",
                    value=1,
                    prefix="代码",
                    suffix="",
                    result="1",
                ),
            ),
            AlgorithmInstruction(
                source_id="alg:bottom",
                caption="流程",
                body="一步",
                bookmark="tf_alg_bottom",
                label="算法1",
                sequence=SequenceInstruction(
                    name="TF_Algorithm",
                    value=1,
                    prefix="算法",
                    suffix="",
                    result="1",
                ),
            ),
        ],
    )

    output = tmp_path / "bottom-captions.docx"
    DocxRenderer().render(plan, output)

    document_xml = _xml_part(output, "word/document.xml")
    paragraphs = document_xml.xpath(".//w:body/w:p", namespaces=NS)
    texts = [_paragraph_text(paragraph) for paragraph in paragraphs]
    assert texts == ["print(1)", "代码1 标题", "一步", "算法1 流程"]
