"""pandoc 可选外部 math provider 测试（ADR-0003 §2.4）。

离线部分不触网不装依赖；真 pandoc 用例 skipif 探测保护（与 citation
provider 测试同款模式），抽样 spike 50 条 OMML 语料（≥10 条）断言产物为
可解析的 ``m:oMath`` 根元素，并验证 render_equation 的包装点（书签/SEQ）
在 provider 链路下保持不变。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from lxml import etree

from thesis_forge.core.render_plan import EquationInstruction
from thesis_forge.renderers.docx.equations import render_equation
from thesis_forge.renderers.docx.math_provider import (
    MATH_NS,
    PandocMathConversionError,
    PandocMathProvider,
    PandocMathUnavailableError,
)

CORPUS = (
    Path(__file__).resolve().parents[1] / "spikes/phase0/omml/corpus/formulas.yaml"
)

FAKE_EXECUTABLE = "tf-definitely-not-a-real-pandoc-binary"
HAS_PANDOC = shutil.which("pandoc") is not None


# ---------------------------------------------------------------------------
# 离线：可用性诊断与失败路径
# ---------------------------------------------------------------------------


def test_info_unavailable_when_executable_missing() -> None:
    info = PandocMathProvider(executable=FAKE_EXECUTABLE).info()

    assert info.available is False
    assert info.version is None
    assert any(FAKE_EXECUTABLE in message for message in info.diagnostics)


def test_convert_raises_structured_when_unavailable() -> None:
    provider = PandocMathProvider(executable=FAKE_EXECUTABLE)

    with pytest.raises(PandocMathUnavailableError) as excinfo:
        provider.convert_to_omml(r"\alpha + \beta")
    assert excinfo.value.diagnostics


# ---------------------------------------------------------------------------
# 真 pandoc（本机自装时才运行）
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_PANDOC, reason="pandoc not available")
@pytest.mark.slow
class TestPandocMathRender:
    def _corpus_formulas(self) -> list[dict[str, str]]:
        data = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
        return data["formulas"]

    def test_corpus_sample_produces_parseable_omath(self) -> None:
        provider = PandocMathProvider()
        assert provider.info().available

        formulas = self._corpus_formulas()
        sample = formulas[::5][:12]  # 覆盖各学科的确定性抽样
        assert len(sample) >= 10
        for formula in sample:
            omath = provider.convert_to_omml(formula["latex"])
            assert omath.tag == f"{{{MATH_NS}}}oMath"
            # lxml 可解析且无残留未转义文本
            etree.tostring(omath)

    def test_known_structure_fraction_and_matrix(self) -> None:
        provider = PandocMathProvider()

        fraction = provider.convert_to_omml(r"\frac{a}{b}")
        assert fraction.findall(f".//{{{MATH_NS}}}f"), "分式应产出 m:f"

        matrix = provider.convert_to_omml(
            r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}"
        )
        assert matrix.findall(f".//{{{MATH_NS}}}m"), "矩阵应产出 m:m"

    def test_unconvertible_formula_raises_structured_error(self) -> None:
        provider = PandocMathProvider()

        # spike eq22 同款失败：裸 \\ 换行不在任何环境内，texmath 拒绝
        with pytest.raises(PandocMathConversionError) as excinfo:
            provider.convert_to_omml("a \\\\ b")
        assert "a \\\\ b" in str(excinfo.value) or excinfo.value.latex == "a \\\\ b"

    def test_render_equation_wrapping_intact_with_provider(self) -> None:
        from docx import Document

        provider = PandocMathProvider()
        document = Document()
        instruction = EquationInstruction(
            source_id="eq:test-1",
            latex=r"E = mc^2",
            alignment="center",
            chapter=1,
            number="1-1",
            label="式（1-1）",
            bookmark="eq:test-1",
            sequence=None,
        )

        render_equation(document, instruction, omml_provider=provider)

        paragraph_xml = etree.tostring(document.paragraphs[0]._p)
        root = etree.fromstring(paragraph_xml)
        assert root.findall(f".//{{{MATH_NS}}}oMath")
        # 包装点不迁移：书签与题注文本仍在段落上（ADR-0003 §2.4）
        bookmark_names = {
            el.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name")
            for el in root.iter(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bookmarkStart"
            )
        }
        assert "eq:test-1" in bookmark_names
        assert "式（1-1）" in "".join(root.itertext())
