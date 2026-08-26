from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from docforge.application.contracts import PreviewResult
from docforge.core.model import Algorithm, ForgeDocument, Listing, SourceLocation
from docforge.core.render_plan import (
    AlgorithmInstruction,
    ListingInstruction,
    RenderPlan,
)
from docforge.core.validator import ValidationContext
from docforge.presentation.review import (
    ReviewAlgorithmContent,
    ReviewListingContent,
    map_review_result,
)


def test_review_projects_listing_and_algorithm_content_with_source_navigation(
    tmp_path: Path,
) -> None:
    listing_code = "print('@fig:inside')\n# [@literal] {#code-id} /tmp/keep"
    document = ForgeDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Listing(
                id="lst:service",
                location=SourceLocation(line=10),
            ),
            Algorithm(
                id="alg:build",
                location=SourceLocation(line=20),
            ),
        ],
    )
    review = map_review_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(),
            plan=RenderPlan(
                nodes=(
                    ListingInstruction(
                        source_id="lst:service",
                        caption="构建服务",
                        language="python",
                        code=listing_code,
                        bookmark="tf_lst_service",
                    ),
                    AlgorithmInstruction(
                        source_id="alg:build",
                        caption="安全构建",
                        body="1. 读取输入\n2. 执行渲染\n3. 输出结果",
                        bookmark="tf_alg_build",
                    ),
                )
            ),
        )
    )

    listing_block, algorithm_block = review.blocks
    assert isinstance(listing_block.content, ReviewListingContent)
    assert isinstance(algorithm_block.content, ReviewAlgorithmContent)
    assert listing_block.content.caption == "构建服务"
    assert listing_block.content.language == "python"
    assert listing_block.content.code == listing_code
    assert algorithm_block.content.caption == "安全构建"
    assert algorithm_block.content.body == "1. 读取输入\n2. 执行渲染\n3. 输出结果"

    assert listing_block.source is not None
    assert listing_block.source.line == 10
    assert algorithm_block.source is not None
    assert algorithm_block.source.line == 20

    listing_visible = json.dumps(asdict(listing_block.content), ensure_ascii=False)
    algorithm_visible = json.dumps(asdict(algorithm_block.content), ensure_ascii=False)
    for technical_marker in (
        "lst:service",
        "alg:build",
        "tf_lst_service",
        "tf_alg_build",
        "[@citation-key]",
        "{#caption-id}",
        "/tmp/source.md",
    ):
        assert technical_marker not in listing_visible
        assert technical_marker not in algorithm_visible

    assert "@fig:inside" in listing_block.content.code
    assert "[@literal]" in listing_block.content.code
    assert "{#code-id}" in listing_block.content.code
    assert "/tmp/keep" in listing_block.content.code


def test_review_hides_technical_markers_from_algorithm_body_and_caption() -> None:
    content = map_review_result(
        PreviewResult(
            document=ForgeDocument(source_path=Path("thesis.md")),
            context=ValidationContext(),
            issues=(),
            plan=RenderPlan(
                nodes=(
                    AlgorithmInstruction(
                        source_id="alg:body",
                        caption="安全构建 [@caption-key] {#alg:caption}",
                        body=(
                            "1. 读取 @alg:target\n"
                            "2. 使用 [@source-key] {#body-id} /tmp/secret"
                        ),
                        bookmark="tf_alg_body",
                    ),
                )
            ),
        )
    )

    algorithm = content.blocks[0].content
    assert isinstance(algorithm, ReviewAlgorithmContent)
    assert "安全构建" in algorithm.caption
    assert "caption-key" not in algorithm.caption
    assert "alg:caption" not in algorithm.caption
    assert "alg:target" not in algorithm.body
    assert "source-key" not in algorithm.body
    assert "body-id" not in algorithm.body
    assert "/tmp/secret" not in algorithm.body
