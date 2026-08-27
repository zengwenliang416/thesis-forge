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

from docforge.application.contracts import (
    ApplicationStageError,
    ProjectIdentity,
    ProjectOutput,
    ProjectRequest,
    ProjectRequestIntent,
)
from docforge.application.office_refresh import (
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
from docforge.application.services import (
    ApplicationDependencies,
    ProjectApplicationService,
)
from docforge.renderers.docx import DocxRenderer
from docforge.renderers.docx.package import (
    DocxPackageValidationError,
    validate_docx_package,
)

ROOT = Path(__file__).resolve().parents[1]
HUT_TEMPLATE = (
    ROOT / "templates" / "schools" / "hunan-university-of-technology" / "master-2026.yaml"
)
EXPECTED_TOC_INSTRUCTION = 'TOC \\o "1-3" \\h \\z \\u'

V2_SOURCE = r"""# 摘要 {#chap:abstract-zh}

本文验证 V2 manifest 项目经过 canonical parser 和 application service 后，
仍能生成包含真实 Word 字段的论文文档。

关键词：论文编译；DOCX；确定性构建

# Abstract {#chap:abstract-en}

This fixture verifies the canonical V2 project path and LibreOffice finalizer.

Keywords: thesis compiler; DOCX; deterministic build

# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

已有研究表明，**结构化编译**与*可验证反馈*能够提升论文工程的一致性 [@smith2025]。
本项目使用 `docforge.yaml` 作为入口，普通源码换行
不应在 Word 中产生手动换行，模型流程见[图](#fig:model)。

![模型总体结构](assets/model.png){#fig:model}

# 系统设计 {#chap:design}

损失函数定义如下：

$$
L=-\sum_{i=1}^{N} y_i \log \hat y_i
$$
{#eq:loss}

其计算方式见[式](#eq:loss)。

| 指标 | 实验组 | 对照组 |
|---|---:|---:|
| **准确率** | 96.2% | 91.8% |
| 召回率 | 94.1% | 89.6% |

: 模型实验结果 {#tbl:experiment}

结果汇总见[表](#tbl:experiment)。

```python {#lst:training title="训练代码"}
# 代码中的 {#literal}、[@literal] 与 @fig:literal 必须保持字面量
for epoch in range(epochs):
    train_one_epoch()
```

```algorithm {#alg:training title="训练流程"}
输入：训练集 D
输出：模型 M
1. 初始化参数
2. 迭代优化
```

这里包含一个说明性脚注[^scope]。\
这一行使用显式 HardBreak。

[^scope]: Review 中显示脚注号和正文，DOCX 中生成原生脚注。

# 参考文献
"""

V2_MANIFEST = """schema: docforge.project.v1

project:
  id: lo-finalizer-fixture
  language: zh-CN

document:
  source: document.md
  type: academic

metadata:
  title:
    zh: DocForge finalizer V2 fixture
    en: DocForge finalizer V2 fixture
  authors:
    - name: 张三

academic:
  student:
    name: 张三
    id: "20260001"
  institution:
    name: 示例大学
    department: 计算机学院
  degree:
    name: 工学硕士
    major: 计算机科学与技术
  advisor:
    name: 李教授
    title: 教授
  completion:
    date: "2026-05"

resources:
  root: .
  assets: assets
  bibliography: references.bib

render:
  template_id: hut-master-2026
  citation_style: GB-T-7714-2025

layout:
  objects:
    fig:model:
      width: 85%

output:
  directory: build
  docx: document.docx

review:
  directory: review
  markdown: document.review.md
  source_map: document.review-map.json
"""

V2_BIBLIOGRAPHY = """@article{smith2025,
  author  = {Smith, Jane and Zhang, Wei},
  title   = {Typed Document Pipelines for Academic Publishing},
  journal = {Journal of Document Engineering},
  year    = {2025},
  volume  = {12},
  number  = {3},
  pages   = {101--120}
}
"""

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
def v2_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    project_root = tmp_path_factory.mktemp("v2-project")
    (project_root / "assets").mkdir()
    template_root = project_root / "templates"
    template_root.mkdir()
    (project_root / "docforge.yaml").write_text(V2_MANIFEST, encoding="utf-8")
    (project_root / "document.md").write_text(V2_SOURCE, encoding="utf-8")
    (project_root / "references.bib").write_text(
        V2_BIBLIOGRAPHY,
        encoding="utf-8",
    )
    shutil.copy2(HUT_TEMPLATE, template_root / HUT_TEMPLATE.name)
    shutil.copy2(
        ROOT / "tests" / "fixtures" / "v2-project" / "assets" / "model.png",
        project_root / "assets" / "model.png",
    )
    return project_root


def _project_request(
    project_root: Path,
    intent: ProjectRequestIntent,
    *,
    output: Path | None = None,
) -> ProjectRequest:
    project_root = project_root.resolve()
    return ProjectRequest(
        project=ProjectIdentity(
            project_id="lo-finalizer-fixture",
            project_root=project_root,
            manifest_path=(project_root / "docforge.yaml").resolve(),
        ),
        intent=intent,
        output=ProjectOutput(output.resolve()) if output is not None else None,
    )


def _project_service(
    *,
    document_refresher=None,
) -> ProjectApplicationService:
    return ProjectApplicationService(
        ApplicationDependencies(document_refresher=document_refresher)
        if document_refresher is not None
        else ApplicationDependencies()
    )


def test_manifest_template_id_controls_default_template_selection(
    v2_project: Path,
    tmp_path: Path,
) -> None:
    mutated_project = tmp_path / "missing-template"
    shutil.copytree(v2_project, mutated_project)
    manifest_path = mutated_project / "docforge.yaml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            "hut-master-2026",
            "mutation-missing-template",
        ),
        encoding="utf-8",
    )

    result = _project_service().preview(
        _project_request(mutated_project, ProjectRequestIntent.REVIEW)
    )

    assert result.plan is None
    assert result.context.template is None
    assert any(issue.code == "missing-template" for issue in result.issues)


def test_project_service_uses_production_package_validator_by_default() -> None:
    assert _project_service().dependencies.package_validator is validate_docx_package


def test_production_package_validator_rejects_invalid_docx(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.docx"
    with ZipFile(invalid, "w") as package:
        package.writestr("not-a-docx.txt", b"invalid")

    with pytest.raises(DocxPackageValidationError, match="TF-DOCX-OPC-003"):
        validate_docx_package(invalid)


def test_build_invokes_configured_package_validator(
    v2_project: Path,
    tmp_path: Path,
) -> None:
    calls: list[Path] = []

    def package_validator(path: str | Path) -> None:
        calls.append(Path(path))
        validate_docx_package(path)

    service = ProjectApplicationService(
        ApplicationDependencies(
            document_refresher=_NoRefresh(),
            package_validator=package_validator,
        )
    )
    output = tmp_path / "validated.docx"
    service.build(
        _project_request(
            v2_project,
            ProjectRequestIntent.BUILD,
            output=output,
        )
    )

    assert len(calls) == 1
    assert output.is_file()


def test_build_preserves_existing_output_when_package_validation_fails(
    v2_project: Path,
    tmp_path: Path,
) -> None:
    class InvalidDocxRenderer:
        def render(self, _plan, output: str | Path) -> None:
            with ZipFile(output, "w") as package:
                package.writestr("not-a-docx.txt", b"invalid")

    output = tmp_path / "existing.docx"
    original = b"previous-output"
    output.write_bytes(original)
    service = ProjectApplicationService(
        ApplicationDependencies(
            renderer=InvalidDocxRenderer(),
            document_refresher=_NoRefresh(),
        )
    )

    with pytest.raises(ApplicationStageError, match="TF-DOCX-OPC-003"):
        service.build(
            _project_request(
                v2_project,
                ProjectRequestIntent.BUILD,
                output=output,
            )
        )

    assert output.read_bytes() == original


def _normalize_libreoffice_footnote_ids(path: Path) -> None:
    """把 LO 的保留脚注 ID 归一化为渲染器的 canonical 表示。"""
    from lxml import etree

    w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    w = f"{{{w_ns}}}"
    namespaces = {"w": w_ns}
    with ZipFile(path) as package:
        footnotes_xml = package.read("word/footnotes.xml")
        document_xml = package.read("word/document.xml")

    footnotes_root = etree.fromstring(footnotes_xml)
    body_ids: dict[str, str] = {}
    separator_ids: list[str] = []
    continuation_separator_ids: list[str] = []
    next_id = 1
    for footnote in footnotes_root.xpath("./w:footnote", namespaces=namespaces):
        footnote_id = footnote.get(f"{w}id")
        footnote_type = footnote.get(f"{w}type")
        if footnote_type == "separator":
            if footnote_id != "0":
                raise ValueError(
                    "LibreOffice produced an unexpected separator footnote ID: "
                    f"{footnote_id}"
                )
            separator_ids.append(footnote_id)
            footnote.set(f"{w}id", "-1")
        elif footnote_type == "continuationSeparator":
            if footnote_id != "1":
                raise ValueError(
                    "LibreOffice produced an unexpected continuation separator "
                    f"footnote ID: {footnote_id}"
                )
            continuation_separator_ids.append(footnote_id)
            footnote.set(f"{w}id", "0")
        else:
            if footnote_id is None or not footnote_id.isdigit():
                raise ValueError(
                    f"LibreOffice produced an invalid body footnote ID: {footnote_id}"
                )
            if footnote_id in body_ids:
                raise ValueError(
                    f"LibreOffice produced a duplicate body footnote ID: {footnote_id}"
                )
            body_ids[footnote_id] = str(next_id)
            footnote.set(f"{w}id", str(next_id))
            next_id += 1

    if separator_ids != ["0"] or continuation_separator_ids != ["1"]:
        raise ValueError(
            "LibreOffice produced an unexpected footnote separator layout"
        )
    if not body_ids:
        raise ValueError("LibreOffice produced no body footnote definitions")
    expected_body_ids = {str(index) for index in range(2, 2 + len(body_ids))}
    if set(body_ids) != expected_body_ids:
        raise ValueError(
            "LibreOffice produced non-contiguous body footnote IDs: "
            f"{sorted(body_ids)}"
        )

    document_root = etree.fromstring(document_xml)
    references = document_root.xpath(
        ".//w:footnoteReference",
        namespaces=namespaces,
    )
    if not references:
        raise ValueError("LibreOffice removed all body footnote references")
    for reference in references:
        old_id = reference.get(f"{w}id")
        if old_id not in body_ids:
            raise ValueError(
                f"LibreOffice produced an unknown body footnote reference: {old_id}"
            )
        reference.set(f"{w}id", body_ids[old_id])

    _replace_package_part(
        path,
        "word/footnotes.xml",
        etree.tostring(
            footnotes_root,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        ),
    )
    _replace_package_part(
        path,
        "word/document.xml",
        etree.tostring(
            document_root,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        ),
    )


class _LibreOfficeFootnoteNormalizer:
    def __init__(self, delegate) -> None:
        self._delegate = delegate

    def refresh(self, path) -> bool:
        refreshed = self._delegate.refresh(path)
        if refreshed:
            try:
                _normalize_libreoffice_footnote_ids(Path(path))
            except Exception as error:
                # Refresh failures may be treated as a no-op by production;
                # malformed normalization must instead fail this build.
                raise ValueError(
                    "LibreOffice footnote normalization failed"
                ) from error
        return refreshed


@pytest.mark.parametrize("error_type", (RuntimeError, OSError, ValueError))
def test_libreoffice_footnote_normalizer_does_not_swallow_errors(
    monkeypatch,
    error_type,
) -> None:
    class Refreshed:
        def refresh(self, _path) -> bool:
            return True

    def fail_normalization(_path) -> None:
        raise error_type("normalization sentinel")

    monkeypatch.setattr(
        sys.modules[__name__],
        "_normalize_libreoffice_footnote_ids",
        fail_normalization,
    )

    with pytest.raises(ValueError, match="normalization failed"):
        _LibreOfficeFootnoteNormalizer(Refreshed()).refresh(
            Path("unused.docx")
        )


@pytest.fixture(scope="module")
def raw_docx(
    tmp_path_factory: pytest.TempPathFactory,
    v2_project: Path,
) -> Path:
    """生成态构建（绕开 finalizer），保留渲染器原始字段状态。"""
    output = tmp_path_factory.mktemp("raw") / "thesis.docx"
    preview = _project_service().preview(
        _project_request(v2_project, ProjectRequestIntent.REVIEW)
    )
    assert preview.plan is not None, preview.issues
    DocxRenderer().render(preview.plan, output)
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

    def test_raw_docx_contains_footnote_and_hardbreak(self, raw_docx: Path):
        with ZipFile(raw_docx) as package:
            document_xml = package.read("word/document.xml")
            footnotes_xml = package.read("word/footnotes.xml")
        assert b"<w:footnoteReference" in document_xml
        assert b"<w:br" in document_xml
        assert b"<w:footnoteRef" in footnotes_xml

    @pytest.mark.parametrize(
        ("mutation", "expected_error"),
        (
            ("missing-node", "unexpected footnote separator layout"),
            ("missing-id", "unexpected continuation separator footnote ID"),
            ("wrong-id", "unexpected continuation separator footnote ID"),
            ("wrong-separator-id", "unexpected separator footnote ID"),
        ),
    )
    def test_footnote_normalizer_rejects_continuation_mutations(
        self,
        raw_docx: Path,
        tmp_path: Path,
        mutation: str,
        expected_error: str,
    ):
        from lxml import etree

        path = tmp_path / f"{mutation}.docx"
        shutil.copy(raw_docx, path)
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        w = f"{{{w_ns}}}"
        namespaces = {"w": w_ns}
        with ZipFile(path) as package:
            footnotes_xml = package.read("word/footnotes.xml")
            document_xml = package.read("word/document.xml")
        footnotes_root = etree.fromstring(footnotes_xml)
        document_root = etree.fromstring(document_xml)

        for footnote in footnotes_root.xpath("./w:footnote", namespaces=namespaces):
            footnote_type = footnote.get(f"{w}type")
            if footnote_type == "separator":
                footnote.set(f"{w}id", "0")
            elif footnote_type == "continuationSeparator":
                footnote.set(f"{w}id", "1")
            else:
                footnote.set(
                    f"{w}id",
                    str(int(footnote.get(f"{w}id", "0")) + 1),
                )
        for reference in document_root.xpath(
            ".//w:footnoteReference",
            namespaces=namespaces,
        ):
            reference.set(
                f"{w}id",
                str(int(reference.get(f"{w}id", "0")) + 1),
            )
        _replace_package_part(
            path,
            "word/footnotes.xml",
            etree.tostring(
                footnotes_root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone=True,
            ),
        )
        _replace_package_part(
            path,
            "word/document.xml",
            etree.tostring(
                document_root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone=True,
            ),
        )

        with ZipFile(path) as package:
            footnotes_root = etree.fromstring(package.read("word/footnotes.xml"))
        continuation = footnotes_root.xpath(
            "./w:footnote[@w:type='continuationSeparator']",
            namespaces=namespaces,
        )[0]
        if mutation == "missing-node":
            continuation.getparent().remove(continuation)
        elif mutation == "missing-id":
            del continuation.attrib[f"{w}id"]
        elif mutation == "wrong-id":
            continuation.set(f"{w}id", "99")
        else:
            separator = footnotes_root.xpath(
                "./w:footnote[@w:type='separator']",
                namespaces=namespaces,
            )[0]
            separator.set(f"{w}id", "99")
        _replace_package_part(
            path,
            "word/footnotes.xml",
            etree.tostring(
                footnotes_root,
                xml_declaration=True,
                encoding="UTF-8",
                standalone=True,
            ),
        )

        with pytest.raises(ValueError, match=expected_error):
            _normalize_libreoffice_footnote_ids(path)


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
def lo_final_docx(
    tmp_path_factory: pytest.TempPathFactory,
    v2_project: Path,
) -> Path:
    """真 final-auto 路径：ProjectApplicationService + LibreOffice。"""
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
    _project_service(
        document_refresher=_LibreOfficeFootnoteNormalizer(
            dependencies.document_refresher
        )
    ).build(
        _project_request(
            v2_project,
            ProjectRequestIntent.BUILD,
            output=output,
        )
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
