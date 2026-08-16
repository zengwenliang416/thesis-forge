"""final-auto（LibreOffice 无头刷新）修复的测试（ADR-0005 §5.3 第 2 项）。

单元层（不需要 soffice）：
- 渲染器无条件定义 LO 刷新会引用的字符样式（IndexLink/FootnoteCharacters）；
- 字段指令捕获/还原：SEQ `\r` 钉值与 TOC 指令在刷新后恢复编译期原状；
- 字段数量/种类对不上时 refresh_document_safely 回滚。

集成层（本机无 soffice 或无 uno python 时跳过）：
- 真 LibreOffice 刷新后 openxml_validate 全过；
- SEQ `\r` 钉值与 TOC 指令保持编译期原状；
- TOC 条目被真值填充、updateFields 被移除（LO 刷新收益保留）。
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from thesis_forge.application.office_refresh import (
    LibreOfficeDocumentRefresher,
    _capture_field_instructions,
    _field_instruction_kind,
    _iter_field_instructions,
    _replace_package_part,
    _restore_field_instructions,
    discover_libreoffice_executable,
    discover_libreoffice_python,
    refresh_document_safely,
)
from thesis_forge.application.services import (
    ApplicationDependencies,
    build_service,
)
from thesis_forge.core.compiler import compile_document
from thesis_forge.core.parser import parse_markdown
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.templates import load_template

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SOURCE = ROOT / "examples" / "complete-thesis" / "thesis.md"
HUT_TEMPLATE = (
    ROOT / "templates" / "schools" / "hunan-university-of-technology" / "master-2026.yaml"
)
EXPECTED_TOC_INSTRUCTION = 'TOC \\o "1-3" \\h \\z \\u'

SOFFICE = shutil.which("soffice") or (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").is_file()
    else None
)


def _load_tool(name: str):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "qa" / "tools" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


openxml_validate = _load_tool("openxml_validate")


class _NoRefresh:
    def refresh(self, path) -> bool:
        return False


@pytest.fixture(scope="module")
def raw_docx(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """生成态构建（绕开 finalizer），保留渲染器原始字段状态。"""
    output = tmp_path_factory.mktemp("raw") / "thesis.docx"
    document = parse_markdown(EXAMPLE_SOURCE)
    template = load_template(HUT_TEMPLATE)
    DocxRenderer().render(compile_document(document, template=template), output)
    return output


def _simulate_lo_instruction_rewrite(path: Path) -> None:
    """模拟 LibreOffice 刷新对字段指令的改写：剥 SEQ `\r`、改写 TOC 指令。

    LO 还会给 instrText 加首尾空格（`xml:space="preserve"`），一并模拟。
    """
    with ZipFile(path) as package:
        document_xml = package.read("word/document.xml")
    from lxml import etree

    root = etree.fromstring(document_xml)
    for instr_elements in _iter_field_instructions(root):
        instruction = "".join(element.text or "" for element in instr_elements)
        kind = _field_instruction_kind(instruction)
        if kind == "SEQ":
            instr_elements[0].text = (
                " " + re.sub(r"\\r \d+ ", "", instruction.strip()) + " "
            )
        elif kind == "TOC":
            instr_elements[0].text = ' TOC \\f \\o "1-3" \\h '
    rewritten = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    _replace_package_part(path, "word/document.xml", rewritten)


class TestRendererStyles:
    def test_lo_referenced_character_styles_defined(self, raw_docx: Path):
        with ZipFile(raw_docx) as package:
            styles_xml = package.read("word/styles.xml").decode("utf-8")
        for style_id in ("IndexLink", "FootnoteCharacters"):
            match = re.search(
                rf'<w:style w:type="character"[^>]*w:styleId="{style_id}"',
                styles_xml,
            )
            assert match is not None, f"styles.xml 缺少字符样式 {style_id}"


class TestFieldInstructionCapture:
    def test_captures_toc_and_seq_in_document_order(self, raw_docx: Path):
        captured = _capture_field_instructions(raw_docx.read_bytes())
        assert captured["TOC"] == [EXPECTED_TOC_INSTRUCTION]
        assert captured["SEQ"] == [
            "SEQ TF_Figure_1 \\r 1 \\* ARABIC",
            "SEQ TF_Equation_2 \\r 1 \\* ARABIC",
            "SEQ TF_Table_2 \\r 1 \\* ARABIC",
        ]

    def test_ignores_package_without_document(self):
        import io
        import zipfile

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("word/styles.xml", b"<styles/>")
        assert _capture_field_instructions(buffer.getvalue()) == {
            "TOC": [],
            "SEQ": [],
        }


class TestFieldInstructionRestore:
    def test_roundtrip_after_simulated_lo_rewrite(
        self, raw_docx: Path, tmp_path: Path
    ):
        refreshed = tmp_path / "refreshed.docx"
        shutil.copy(raw_docx, refreshed)
        captured = _capture_field_instructions(refreshed.read_bytes())
        _simulate_lo_instruction_rewrite(refreshed)

        degraded = _capture_field_instructions(refreshed.read_bytes())
        assert degraded["TOC"] == ['TOC \\f \\o "1-3" \\h']
        assert all("\\r" not in instruction for instruction in degraded["SEQ"])

        _restore_field_instructions(refreshed, captured)
        assert _capture_field_instructions(refreshed.read_bytes()) == captured

    def test_rejects_field_kind_change(self, raw_docx: Path, tmp_path: Path):
        refreshed = tmp_path / "refreshed.docx"
        shutil.copy(raw_docx, refreshed)
        captured = _capture_field_instructions(refreshed.read_bytes())

        with ZipFile(refreshed) as package:
            document_xml = package.read("word/document.xml")
        from lxml import etree

        root = etree.fromstring(document_xml)
        for instr_elements in _iter_field_instructions(root):
            instruction = "".join(element.text or "" for element in instr_elements)
            if _field_instruction_kind(instruction) == "SEQ":
                # LO 把字段改没了（变成另一个 REF 指令）
                instr_elements[0].text = " REF tf_eq_pipeline \\h "
                break
        _replace_package_part(
            refreshed,
            "word/document.xml",
            etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            ),
        )

        with pytest.raises(RuntimeError, match="dropped 1 TOC/SEQ"):
            _restore_field_instructions(refreshed, captured)

    def test_rejects_extra_field(self, raw_docx: Path, tmp_path: Path):
        refreshed = tmp_path / "refreshed.docx"
        shutil.copy(raw_docx, refreshed)
        captured = _capture_field_instructions(refreshed.read_bytes())
        captured["SEQ"] = captured["SEQ"][:-1]
        with pytest.raises(RuntimeError, match="unexpected SEQ"):
            _restore_field_instructions(refreshed, captured)


class TestRefreshDocumentSafelyRestore:
    def test_restores_instructions_after_refresh(
        self, raw_docx: Path, tmp_path: Path
    ):
        document = tmp_path / "thesis.docx"
        shutil.copy(raw_docx, document)
        original_instructions = _capture_field_instructions(document.read_bytes())

        class LoLikeRefresher:
            def refresh(self, path) -> bool:
                _simulate_lo_instruction_rewrite(Path(path))
                return True

        assert refresh_document_safely(LoLikeRefresher(), document)
        assert (
            _capture_field_instructions(document.read_bytes())
            == original_instructions
        )
        report = openxml_validate.validate_docx(document)
        assert report["ok"], report["checks"]

    def test_rolls_back_when_restore_fails(self, raw_docx: Path, tmp_path: Path):
        document = tmp_path / "thesis.docx"
        shutil.copy(raw_docx, document)
        original_bytes = document.read_bytes()

        class FieldDroppingRefresher:
            def refresh(self, path) -> bool:
                with ZipFile(path) as package:
                    document_xml = package.read("word/document.xml")
                from lxml import etree

                root = etree.fromstring(document_xml)
                for instr_elements in _iter_field_instructions(root):
                    text = "".join(el.text or "" for el in instr_elements)
                    if _field_instruction_kind(text) == "TOC":
                        instr_elements[0].text = " REF nowhere \\h "
                _replace_package_part(
                    Path(path),
                    "word/document.xml",
                    etree.tostring(
                        root, xml_declaration=True, encoding="UTF-8", standalone=True
                    ),
                )
                return True

        assert not refresh_document_safely(FieldDroppingRefresher(), document)
        assert document.read_bytes() == original_bytes


def _toc_result_text(path: Path) -> str:
    """TOC 字段 cached result（separate..end 之间）的纯文本。"""
    with ZipFile(path) as package:
        document_xml = package.read("word/document.xml")
    from lxml import etree

    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    root = etree.fromstring(document_xml)
    stack: list[dict] = []
    for element in root.iter():
        if element.tag == f"{w}fldChar":
            kind = element.get(f"{w}fldCharType")
            if kind == "begin":
                stack.append({"toc": False, "sep": False, "text": []})
            elif kind == "separate" and stack:
                stack[-1]["sep"] = True
            elif kind == "end" and stack:
                field = stack.pop()
                if field["toc"]:
                    return "".join(field["text"])
        elif element.tag == f"{w}instrText" and stack and not stack[-1]["sep"]:
            instruction = element.text or ""
            if _field_instruction_kind(instruction) == "TOC":
                stack[-1]["toc"] = True
        elif element.tag == f"{w}t" and stack and stack[-1]["sep"]:
            stack[-1]["text"].append(element.text or "")
    return ""


@pytest.fixture(scope="module")
def lo_final_docx(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """真 final-auto 路径：build_service + LibreOfficeDocumentRefresher。"""
    if SOFFICE is None:
        pytest.skip("本机未安装 LibreOffice")
    executable = discover_libreoffice_executable()
    assert executable is not None
    python_executable = discover_libreoffice_python(executable)
    if python_executable is None:
        pytest.skip("未找到可 import uno 的 LibreOffice Python")
    output = tmp_path_factory.mktemp("final-auto") / "thesis.docx"
    dependencies = ApplicationDependencies(
        document_refresher=LibreOfficeDocumentRefresher(
            executable=executable,
            python_executable=python_executable,
            timeout_seconds=180.0,
        )
    )
    build_service(
        EXAMPLE_SOURCE,
        output,
        template_path=HUT_TEMPLATE,
        dependencies=dependencies,
    )
    return output


@pytest.mark.skipif(SOFFICE is None, reason="本机未安装 LibreOffice")
class TestLibreOfficeFinalAuto:
    def test_refresh_actually_ran(self, lo_final_docx: Path):
        with ZipFile(lo_final_docx) as package:
            settings = package.read("word/settings.xml").decode("utf-8")
        assert "updateFields" not in settings

    def test_openxml_validate_passes(self, lo_final_docx: Path):
        report = openxml_validate.validate_docx(lo_final_docx)
        failed = [
            check for check in report["checks"] if check["status"] != "pass"
        ]
        assert failed == [], failed

    def test_seq_pins_and_toc_instruction_preserved(
        self, lo_final_docx: Path, raw_docx: Path
    ):
        expected = _capture_field_instructions(raw_docx.read_bytes())
        actual = _capture_field_instructions(lo_final_docx.read_bytes())
        assert actual["TOC"] == [EXPECTED_TOC_INSTRUCTION]
        assert actual["TOC"] == expected["TOC"]
        assert actual["SEQ"] == expected["SEQ"]
        assert all("\\r" in instruction for instruction in actual["SEQ"])

    def test_toc_entries_filled_with_real_values(self, lo_final_docx: Path):
        toc_text = _toc_result_text(lo_final_docx)
        assert "绪论" in toc_text
        # HUT 模板前置节为 upperRoman 页码：真值填充后出现罗马数字页码
        #（编译期 cached 条目的页码占位恒为 "1"）。
        assert re.search(r"[IVX]{2,}", toc_text), toc_text

    def test_toc_entries_use_defined_styles(self, lo_final_docx: Path):
        with ZipFile(lo_final_docx) as package:
            styles_xml = package.read("word/styles.xml").decode("utf-8")
        for style_id in ("IndexLink", "FootnoteCharacters", "TOC1", "TOC2", "TOC3"):
            assert f'w:styleId="{style_id}"' in styles_xml
