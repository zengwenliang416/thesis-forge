from pathlib import Path

import pytest
from pydantic import ValidationError

from thesis_forge.core.model import Algorithm, Heading, Listing, Text, ThesisDocument
from thesis_forge.core.symbols import NumberingInputs, SymbolTable
from thesis_forge.templates import load_template
from thesis_forge.templates.model import (
    AlgorithmSpec,
    CaptionSpec,
    ListingSpec,
    NumberingSpec,
    ThesisTemplate,
)


def _text(value: str) -> list[Text]:
    return [Text(value=value)]


def _template(
    *,
    listing_mode: str = "chapter",
    algorithm_mode: str = "continuous",
) -> ThesisTemplate:
    base = load_template("templates/base/bachelor.yaml")
    return base.model_copy(
        update={
            "listing": ListingSpec(
                numbering=NumberingSpec(mode=listing_mode, separator="-"),
                caption=CaptionSpec(position="top", prefix="代码"),
            ),
            "algorithm": AlgorithmSpec(
                numbering=NumberingSpec(mode=algorithm_mode, separator="-"),
                caption=CaptionSpec(position="top", prefix="算法"),
            ),
        }
    )


def _document() -> ThesisDocument:
    return ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(id="chap:first", level=1, inlines=_text("第一章")),
            Listing(
                id="lst:first",
                caption_inlines=_text("第一段代码"),
                language="python",
                code="print(1)",
            ),
            Algorithm(
                id="alg:first",
                caption_inlines=_text("第一段算法"),
                body="1. 初始化",
            ),
            Heading(id="chap:second", level=1, inlines=_text("第二章")),
            Listing(
                id="lst:second",
                caption_inlines=_text("第二段代码"),
                language="python",
                code="print(2)",
            ),
            Algorithm(
                id="alg:second",
                caption_inlines=_text("第二段算法"),
                body="1. 迭代",
            ),
        ],
    )


def test_listing_and_algorithm_use_distinct_configured_policies() -> None:
    symbols = SymbolTable.from_document(_document(), _template())

    listing_first = symbols.entries["lst:first"]
    assert listing_first.target_type == "lst"
    assert listing_first.bookmark == "tf_lst_first"
    assert listing_first.display_label == "代码1-1"
    assert listing_first.numbering_inputs == NumberingInputs(
        kind="listing",
        chapter=1,
        mode="chapter",
        separator="-",
        sequence_value=1,
        number="1-1",
        caption_prefix="代码",
    )

    listing_second = symbols.entries["lst:second"]
    assert listing_second.display_label == "代码2-1"
    assert listing_second.numbering_inputs is not None
    assert listing_second.numbering_inputs.sequence_value == 1

    algorithm_first = symbols.entries["alg:first"]
    assert algorithm_first.target_type == "alg"
    assert algorithm_first.bookmark == "tf_alg_first"
    assert algorithm_first.display_label == "算法1"
    assert algorithm_first.numbering_inputs == NumberingInputs(
        kind="algorithm",
        chapter=1,
        mode="continuous",
        separator="-",
        sequence_value=1,
        number="1",
        caption_prefix="算法",
    )

    algorithm_second = symbols.entries["alg:second"]
    assert algorithm_second.display_label == "算法2"
    assert algorithm_second.numbering_inputs is not None
    assert algorithm_second.numbering_inputs.sequence_value == 2


@pytest.mark.parametrize("kind", ["listing", "algorithm"])
def test_listing_and_algorithm_numbering_can_be_disabled(kind: str) -> None:
    template = _template(listing_mode="none", algorithm_mode="none")
    symbols = SymbolTable.from_document(_document(), template)

    entry = symbols.entries[f"{'lst' if kind == 'listing' else 'alg'}:first"]
    assert entry.display_label in {"第一段代码", "第一段算法"}
    assert entry.numbering_inputs == NumberingInputs(
        kind=kind,
        chapter=1,
        mode="none",
        separator="-",
        sequence_value=None,
        number=None,
        caption_prefix="代码" if kind == "listing" else "算法",
    )


def test_listing_algorithm_template_modes_are_validated() -> None:
    with pytest.raises(ValidationError):
        _template(listing_mode="invalid")
