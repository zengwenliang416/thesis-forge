from pathlib import Path

from docforge.core.compiler import compile_document
from docforge.core.parser_markdown_it import MarkdownItParserBackend
from docforge.core.render_plan import AlgorithmInstruction, ListingInstruction
from docforge.templates import load_template
from docforge.templates.model import (
    AlgorithmSpec,
    CaptionSpec,
    ListingSpec,
    NumberingSpec,
)

BACKEND = MarkdownItParserBackend()


def _parse(source: str):
    return BACKEND.parse_text(source, source_path=Path("/tmp/thesis.md"))


def _template(*, listing_mode: str = "chapter", algorithm_mode: str = "continuous"):
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


def test_compile_listing_algorithm_carries_numbering_and_bookmarks() -> None:
    document = _parse(
        """# 第一章 {#chap:intro}

```python {#lst:service title="构建服务"}
build_service(source, output)
```

```algorithm {#alg:build title="安全构建"}
1. validate
2. render
```
""",
    )

    plan = compile_document(document, template=_template())
    listing = next(node for node in plan.nodes if isinstance(node, ListingInstruction))
    algorithm = next(
        node for node in plan.nodes if isinstance(node, AlgorithmInstruction)
    )

    assert listing.code == "build_service(source, output)"
    assert listing.chapter == 1
    assert listing.number == "1-1"
    assert listing.label == "代码1-1"
    assert listing.bookmark == "tf_lst_service"
    assert listing.sequence is not None
    assert listing.sequence.name == "TF_Listing_1"
    assert listing.sequence.field_code == "SEQ TF_Listing_1 \\r 1 \\* ARABIC"
    assert listing.sequence.result == "代码1-1"
    assert listing.payload["sequence"]["result"] == "代码1-1"
    assert "field_code" not in listing.payload["sequence"]
    assert "raw" not in listing.payload
    assert "markdown" not in listing.payload

    assert algorithm.body == "1. validate\n2. render"
    assert algorithm.chapter == 1
    assert algorithm.number == "1"
    assert algorithm.label == "算法1"
    assert algorithm.bookmark == "tf_alg_build"
    assert algorithm.sequence is not None
    assert algorithm.sequence.name == "TF_Algorithm"
    assert algorithm.sequence.field_code == "SEQ TF_Algorithm \\r 1 \\* ARABIC"
    assert algorithm.sequence.result == "算法1"
    assert algorithm.payload["sequence"]["result"] == "算法1"
    assert "field_code" not in algorithm.payload["sequence"]
    assert "raw" not in algorithm.payload
    assert "markdown" not in algorithm.payload


def test_compile_listing_algorithm_omits_sequence_when_disabled() -> None:
    document = _parse(
        """```python {#lst:plain title="普通代码"}
x = 1
```

```algorithm {#alg:plain title="普通算法"}
1. stop
```
""",
    )

    plan = compile_document(
        document,
        template=_template(listing_mode="none", algorithm_mode="none"),
    )
    listing = next(node for node in plan.nodes if isinstance(node, ListingInstruction))
    algorithm = next(
        node for node in plan.nodes if isinstance(node, AlgorithmInstruction)
    )

    assert listing.number is None
    assert listing.label == "普通代码"
    assert listing.sequence is None
    assert algorithm.number is None
    assert algorithm.label == "普通算法"
    assert algorithm.sequence is None
