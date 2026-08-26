from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import yaml
from lxml import etree

from thesis_forge.application import (
    ApplicationDependencies,
    preview_service,
    validation_service,
)
from thesis_forge.core.parser_backend import create_parser_backend
from thesis_forge.core.validator import ValidationContext
from thesis_forge.renderers.docx.package import validate_docx_package
from thesis_forge.templates import load_template

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ASSET = ROOT / "tests" / "fixtures" / "v2-project" / "assets" / "model.png"
HUT_TEMPLATE = (
    ROOT
    / "templates"
    / "schools"
    / "hunan-university-of-technology"
    / "master-2026.yaml"
)
EXAMPLE_TEMPLATE = (
    ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
)
CLI = ROOT / ".venv" / "bin" / "thesisforge"

ACCEPTANCE_SOURCE = """# 摘要 {#chap:abstract-zh}

本文设计并实现一种本地优先、确定性、模板驱动的学位论文编译器。
系统将 Markdown 解析为与 Word 实现无关的论文领域模型，经结构化验证、模板解析与统一编译后生成可编辑 DOCX。

关键词：Markdown；论文编译；OOXML；确定性构建

# Abstract {#chap:abstract-en}

This thesis presents a local-first, deterministic and template-driven compiler for structured academic documents.
Markdown becomes a renderer-neutral domain model and then an editable DOCX package.

Keywords: Markdown; thesis compiler; OOXML; deterministic build

# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

传统 Word 排版要求作者反复调整正文、标题、图表编号、公式和参考文献。
结构化学术文档方法能够降低内容与版式的耦合 [@ref-example-1]，而确定性编译进一步提高了重复构建的可验证性 [@ref-example-2]。[^determinism]

### 现有流程的局限 {#sec:limitations}

手工排版容易在章节调整后产生编号、目录、交叉引用和页眉页脚不一致的问题。
模板驱动编译把学校规则集中在强类型 YAML 中，使同一论文内容可以在不修改 Markdown 的情况下切换版式。

## 研究内容 {#sec:scope}

本文围绕以下内容展开：

1. 定义可验证的结构化 Markdown 输入；
2. 建立与 Word 无关的论文领域模型；
3. 通过模板解析正文和特殊章节版式；
4. 生成包含真实 OOXML 对象的 DOCX。

## 技术路线 {#sec:technical-route}

系统总体架构如[图](#fig:architecture)所示。

![ThesisForge 确定性编译架构](assets/model.png){#fig:architecture}

# 系统设计 {#chap:design}

## 编译流水线 {#sec:pipeline}

系统采用 Markdown -> ForgeDocument -> Validation -> Template -> RenderPlan -> DOCX 的单向编译链路，其抽象关系见[式](#eq:pipeline)。

$$
D_{docx} = R(C(V(P(D_{md}))))
$$
{#eq:pipeline}

## 能力模型 {#sec:capabilities}

P0 核心能力见[表](#tbl:capabilities)。

| 能力 | 输入 | DOCX 输出 |
| --- | --- | --- |
| 正文与特殊章节 | Markdown 语义段落 | 模板驱动 Word 样式 |
| 图 | 本地图片 | Drawing、题注与书签 |
| 表 | Markdown 表格 | 三线表、题注与书签 |
| 公式 | LaTeX 子集 | OMML、编号与书签 |
| 引用 | BibTeX key | 上标顺序编码引用 |

: ThesisForge P0 核心能力 {#tbl:capabilities}

## 安全构建算法 {#sec:safe-build}

安全构建流程见[算法](#alg:build)。

```algorithm {#alg:build title="安全构建流程"}
输入：本地 V2 项目
输出：结构化 DOCX
1. 解析并验证本地输入；
2. 编译 renderer-neutral RenderPlan；
3. 渲染到目标目录临时文件；
4. 校验 DOCX ZIP 与核心 XML；
5. 原子替换最终输出。
```

## 应用服务接口 {#sec:application-service}

核心服务接口示意见[代码](#lst:service)。

```python {#lst:service title="安全构建服务调用"}
result = build_service(
    source="thesisforge.yaml",
    output="thesis.docx",
)
```

# 实验结果与分析 {#chap:results}

## 离线验收 {#sec:offline-acceptance}

在禁用网络连接并移除 AI 服务凭据后，inspect、validate 与 build 均只读取本地 Markdown、YAML、BibTeX 和图片资源。
重复构建生成的 RenderPlan 和规范化 Word XML 保持一致。

# 结论与展望 {#chap:conclusion}

本文完成了 ThesisForge 的模板化编译链和端到端验收。

# 参考文献 {#chap:bibliography}

# 致谢 {#chap:acknowledgements}

感谢指导教师和同学在系统设计、文档验证与兼容性测试过程中提供的帮助。

# 附录 A 验收命令 {#chap:appendix-a}

本附录记录完整样例使用的离线命令：

1. thesisforge inspect project
2. thesisforge validate project
3. thesisforge build project -o thesis.docx

[^determinism]: 确定性构建指相同输入、模板和依赖版本产生一致的 RenderPlan、编号、引用、字段、章节结构和规范化 OOXML。
"""

ACCEPTANCE_BIBLIOGRAPHY = """@article{ref-example-1,
  author  = {Zhang, San and Li, Si},
  title   = {Structured Academic Document Compilation},
  journal = {Journal of Document Engineering},
  year    = {2025},
  volume  = {10},
  number  = {2},
  pages   = {100--120},
  doi     = {10.0000/example.2025.001}
}

@book{ref-example-2,
  author    = {Smith, John},
  title     = {Deterministic Thesis Compilation},
  publisher = {Example University Press},
  address   = {Beijing},
  year      = {2024}
}
"""

ACCEPTANCE_MANIFEST = """schema: thesisforge.project.v2

project:
  id: {project_id}
  language: zh-CN

document:
  source: thesis.md

metadata:
  title:
    zh: 面向结构化学术文档的确定性论文编译系统设计
    en: Design of a Deterministic Thesis Compiler for Structured Academic Documents
  author:
    name: 曾文亮
    student_id: "2024000001"
  institution:
    university: 湖南工业大学
    college: 计算机学院
  degree:
    name: 工学硕士
    major: 计算机科学与技术
  advisor:
    name: 指导教师
    title: 教授
  dates:
    completed: "2026-06"

resources:
  root: .
  assets: assets
  bibliography: references.bib

render:
  template_id: {template_id}
  citation_style: GB-T-7714-2025

output:
  directory: build
  docx: thesis.docx
  retain_last_successful_preview: true
"""

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_context(
    document,
    template_path: str | Path | None,
) -> ValidationContext:
    return ValidationContext.from_document(
        document,
        template_path=template_path,
        required_metadata=(),
    )


def _canonical_dependencies() -> ApplicationDependencies:
    return ApplicationDependencies(
        parser_backend=create_parser_backend(),
        context_factory=_canonical_context,
    )


def _offline_environment(tmp_path: Path) -> dict[str, str]:
    blocker = tmp_path / "offline"
    blocker.mkdir(exist_ok=True)
    (blocker / "sitecustomize.py").write_text(
        """import socket
def blocked(*args, **kwargs):
    raise RuntimeError("network access is forbidden in acceptance tests")
socket.create_connection = blocked
socket.socket.connect = blocked
""",
        encoding="utf-8",
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if not any(
            marker in key.upper()
            for marker in (
                "OPENAI",
                "ANTHROPIC",
                "GEMINI",
                "GOOGLE_API_KEY",
                "AZURE",
                "DEEPSEEK",
            )
        )
    }
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(blocker), existing_python_path) if value
    )
    environment["NO_PROXY"] = "*"
    environment["no_proxy"] = "*"
    return environment


def _run_cli(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), *arguments],
        cwd=tmp_path,
        env=_offline_environment(tmp_path),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _materialize_project(
    tmp_path: Path,
    *,
    template_path: Path,
    project_name: str,
    source_text: str = ACCEPTANCE_SOURCE,
) -> Path:
    project = tmp_path / project_name
    project.mkdir()
    assets = project / "assets"
    assets.mkdir()
    templates = project / "templates"
    templates.mkdir()

    template_data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    template_id = template_data["id"]
    shutil.copy2(template_path, templates / template_path.name)
    (project / "thesis.md").write_text(source_text, encoding="utf-8")
    (project / "references.bib").write_text(
        ACCEPTANCE_BIBLIOGRAPHY,
        encoding="utf-8",
    )
    shutil.copy2(CANONICAL_ASSET, assets / "model.png")
    (project / "thesisforge.yaml").write_text(
        ACCEPTANCE_MANIFEST.format(
            project_id=project_name.replace("_", "-"),
            template_id=template_id,
        ),
        encoding="utf-8",
    )
    return project


def _project_inputs(project: Path) -> tuple[Path, ...]:
    template_files = tuple((project / "templates").glob("*.yaml"))
    assert len(template_files) == 1
    return (
        project / "thesis.md",
        project / "thesisforge.yaml",
        project / "references.bib",
        project / "assets" / "model.png",
        template_files[0],
    )


def _xml_part(path: Path, part: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(part))


def _field_instructions(document_xml) -> tuple[str, ...]:
    return tuple(
        " ".join(text.split())
        for text in document_xml.xpath(".//w:instrText/text()", namespaces=NS)
    )


def _semantic_snapshot(path: Path) -> dict[str, object]:
    document_xml = _xml_part(path, "word/document.xml")
    with ZipFile(path) as package:
        header_footer_snapshot = tuple(
            (
                name,
                tuple(
                    etree.fromstring(package.read(name)).xpath(
                        ".//w:t/text()",
                        namespaces=NS,
                    )
                ),
                tuple(
                    " ".join(text.split())
                    for text in etree.fromstring(package.read(name)).xpath(
                        ".//w:instrText/text()",
                        namespaces=NS,
                    )
                ),
            )
            for name in sorted(package.namelist())
            if name.startswith(("word/header", "word/footer"))
            and name.endswith(".xml")
        )
    return {
        "text": tuple(
            document_xml.xpath(".//w:body//w:t/text()", namespaces=NS)
        ),
        "fields": tuple(
            instruction
            for instruction in _field_instructions(document_xml)
            if instruction.startswith(("TOC ", "SEQ ", "REF "))
        ),
        "bookmarks": tuple(
            document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
        ),
        "drawing_count": len(document_xml.xpath(".//w:drawing", namespaces=NS)),
        "table_count": len(document_xml.xpath(".//w:tbl", namespaces=NS)),
        "math_count": len(document_xml.xpath(".//m:oMath", namespaces=NS)),
        "header_footer": header_footer_snapshot,
    }


def _normalized_word_ooxml(path: Path) -> dict[str, bytes]:
    with ZipFile(path) as package:
        parts = {
            name: package.read(name)
            for name in package.namelist()
            if name.startswith("word/")
            and name.endswith((".xml", ".rels"))
        }
    return {
        name: etree.tostring(
            etree.fromstring(content),
            method="c14n",
            with_comments=False,
        )
        for name, content in sorted(parts.items())
    }


def _render_plan_snapshot(path: Path, *, template_path: Path | None = None):
    preview = preview_service(path, template_path=template_path)
    assert not preview.errors
    assert preview.plan is not None
    nodes = []
    for node in preview.plan.nodes:
        payload = node.payload
        if isinstance(payload, dict) and "asset_path" in payload:
            payload = {
                **payload,
                "asset_path": Path(payload["asset_path"]).name,
            }
        nodes.append((node.kind, payload))
    return {
        "nodes": tuple(nodes),
        "bookmarks": preview.plan.bookmarks,
        "references": preview.plan.references,
        "citation_order": preview.plan.citation_order,
        "initial_section_role": preview.plan.initial_section_role,
    }


def _write_alternate_style_template(tmp_path: Path) -> Path:
    data = yaml.safe_load(HUT_TEMPLATE.read_text(encoding="utf-8"))
    data["id"] = "hut-master-2026-alternate-style"
    data["name"] = "湖南工业大学硕士学位论文样式对照模板"
    data["body"]["font"]["east_asia"] = "仿宋"
    data["body"]["size"] = "11pt"
    data["heading"]["level1"]["size"] = "18pt"
    path = tmp_path / "alternate-style.yaml"
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _write_minimal_source(path: Path, *, template_id: str) -> None:
    path.write_text(
        """# 绪论 {#chap:introduction}

## 背景 {#sec:background}

### 研究范围 {#sec:scope}

正文。
""",
        encoding="utf-8",
    )
    (path.parent / "thesisforge.yaml").write_text(
        f"""schema: thesisforge.project.v2

project:
  id: acceptance-fixture
  language: zh-CN

document:
  source: {path.name}

metadata:
  title:
    zh: Template validation fixture
  author:
    name: ThesisForge

render:
  template_id: {template_id}
""",
        encoding="utf-8",
    )


def _write_list_project(project: Path, *, template_path: Path) -> Path:
    return _materialize_project(
        project.parent,
        template_path=template_path,
        project_name=project.name,
        source_text="""# 列表验收 {#chap:list}

3. 有序一级
  1. 有序二级
    1. 有序三级
      1. 有序四级复用

- 无序一级
  - 无序二级
    - 无序三级
      - 无序四级复用
""",
    )


def _numbering_definition_for_paragraph(numbering_xml, paragraph):
    number_id = paragraph.xpath(
        "./w:pPr/w:numPr/w:numId/@w:val",
        namespaces=NS,
    )[0]
    abstract_id = numbering_xml.xpath(
        f"./w:num[@w:numId='{number_id}']/w:abstractNumId/@w:val",
        namespaces=NS,
    )[0]
    abstract = numbering_xml.xpath(
        f"./w:abstractNum[@w:abstractNumId='{abstract_id}']",
        namespaces=NS,
    )[0]
    return number_id, abstract


def _relationship_targets(path: Path) -> dict[str, str]:
    relationships = _xml_part(path, "word/_rels/document.xml.rels")
    return {
        relationship.get("Id"): relationship.get("Target")
        for relationship in relationships.xpath(
            "./pr:Relationship",
            namespaces=NS,
        )
    }


def test_complete_example_inventory_and_offline_inspect_are_read_only(tmp_path: Path):
    project = _materialize_project(
        tmp_path,
        template_path=HUT_TEMPLATE,
        project_name="acceptance-project",
    )
    input_paths = _project_inputs(project)
    before = {path: _digest(path) for path in input_paths}

    result = _run_cli(tmp_path, "inspect", str(project))

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    block_kinds = {block["kind"] for block in payload["blocks"]}
    assert {
        "Heading",
        "Paragraph",
        "ListBlock",
        "Figure",
        "Table",
        "Equation",
        "Listing",
        "Algorithm",
        "FootnoteDefinition",
    } <= block_kinds
    block_ids = {block["id"] for block in payload["blocks"] if block.get("id")}
    assert {
        "chap:abstract-zh",
        "chap:abstract-en",
        "chap:introduction",
        "chap:design",
        "fig:architecture",
        "tbl:capabilities",
        "eq:pipeline",
        "alg:build",
        "lst:service",
        "chap:bibliography",
        "chap:acknowledgements",
        "chap:appendix-a",
    } <= block_ids
    assert {"fig:architecture", "tbl:capabilities", "eq:pipeline"} <= {
        reference["target"] for reference in payload["cross_references"]
    }
    assert {"ref-example-1", "ref-example-2"} <= {
        key for citation in payload["citations"] for key in citation["keys"]
    }
    assert {reference["label"] for reference in payload["footnote_references"]} == {
        "determinism"
    }
    assert {path: _digest(path) for path in input_paths} == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "acceptance-project",
        "offline",
    ]


def test_complete_example_validates_and_builds_offline_without_mutating_inputs(
    tmp_path: Path,
):
    project = _materialize_project(
        tmp_path,
        template_path=HUT_TEMPLATE,
        project_name="acceptance-project",
    )
    input_paths = _project_inputs(project)
    before = {path: _digest(path) for path in input_paths}

    validation = _run_cli(
        tmp_path,
        "validate",
        str(project),
    )
    assert validation.returncode == 0, validation.stderr or validation.stdout
    assert "未发现结构性问题" in validation.stdout

    output = tmp_path / "acceptance.docx"
    build = _run_cli(
        tmp_path,
        "build",
        str(project),
        "-o",
        str(output),
    )
    assert build.returncode == 0, build.stderr or build.stdout
    assert output.is_file()
    validate_docx_package(output)
    document_xml = _xml_part(output, "word/document.xml")
    sections = document_xml.xpath(".//w:sectPr", namespaces=NS)
    assert len(sections) == 3
    assert sections[1].xpath("./w:pgNumType/@w:fmt", namespaces=NS) == [
        "upperRoman"
    ]
    assert {path: _digest(path) for path in input_paths} == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "acceptance-project",
        "acceptance.docx",
        "offline",
    ]


def test_complete_example_docx_contains_required_visible_content_and_word_objects(
    tmp_path: Path,
):
    project = _materialize_project(
        tmp_path,
        template_path=HUT_TEMPLATE,
        project_name="acceptance-project",
    )
    output = tmp_path / "complete-thesis.docx"
    build = _run_cli(tmp_path, "build", str(project), "-o", str(output))
    assert build.returncode == 0, build.stderr or build.stdout

    with ZipFile(output) as package:
        assert package.testzip() is None
        parts = set(package.namelist())
    assert {
        "word/document.xml",
        "word/styles.xml",
        "word/settings.xml",
        "word/numbering.xml",
        "word/footnotes.xml",
    } <= parts
    assert any(part.startswith("word/media/") for part in parts)
    assert any(part.startswith("word/header") for part in parts)
    assert any(part.startswith("word/footer") for part in parts)

    document_xml = _xml_part(output, "word/document.xml")
    styles_xml = _xml_part(output, "word/styles.xml")
    settings_xml = _xml_part(output, "word/settings.xml")
    for level in range(1, 4):
        heading_style = styles_xml.xpath(
            f".//w:style[@w:styleId='Heading{level}']",
            namespaces=NS,
        )[0]
        assert heading_style.xpath("./w:rPr/w:color/@w:val", namespaces=NS) == [
            "000000"
        ]
        assert not heading_style.xpath(
            "./w:rPr/w:color/@w:themeColor",
            namespaces=NS,
        )
        assert heading_style.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == [
            "left"
        ]
        assert heading_style.xpath("./w:pPr/w:ind/@w:left", namespaces=NS) == [
            "0"
        ]
        assert heading_style.xpath("./w:pPr/w:ind/@w:right", namespaces=NS) == [
            "0"
        ]
        assert heading_style.xpath(
            "./w:pPr/w:ind/@w:firstLine",
            namespaces=NS,
        ) == ["0"]
    document_text = "".join(document_xml.xpath(".//w:body//w:t/text()", namespaces=NS))
    for expected in (
        "湖南工业大学",
        "面向结构化学术文档的确定性论文编译系统设计",
        "曾文亮",
        "2024000001",
        "指导教师",
        "摘要",
        "Abstract",
        "绪论",
        "系统设计",
        "参考文献",
        "致谢",
        "附录 A",
    ):
        assert expected in document_text
    heading_texts = {
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in document_xml.xpath(
            (
                ".//w:p[w:pPr/w:pStyle["
                "starts-with(@w:val, 'Heading') "
                "or @w:val='TFAbstractZHTitle' "
                "or @w:val='TFAbstractENTitle'"
                "]]"
            ),
            namespaces=NS,
        )
    }
    assert {"摘要", "Abstract", "绪论", "系统设计"} <= heading_texts
    # 标题文本同时出现在 TOC cached 条目（TOC1 样式）中，需按样式区分
    assert len(
        document_xml.xpath(
            ".//w:p[w:pPr/w:pStyle[@w:val='TFAbstractZHTitle']]"
            "[.//w:t[text()='摘要']]",
            namespaces=NS,
        )
    ) == 1
    assert len(
        document_xml.xpath(
            ".//w:p[w:pPr/w:pStyle[@w:val='TFAbstractENTitle']]"
            "[.//w:t[text()='Abstract']]",
            namespaces=NS,
        )
    ) == 1
    assert {
        "湖南工业大学",
        "面向结构化学术文档的确定性论文编译系统设计",
    }.isdisjoint(heading_texts)
    expected_roles = {
        "摘要": "TFAbstractZHTitle",
        "关键词：Markdown；论文编译；OOXML；确定性构建": "TFKeywordsZH",
        "Abstract": "TFAbstractENTitle",
        "Keywords: Markdown; thesis compiler; OOXML; deterministic build": (
            "TFKeywordsEN"
        ),
        "参考文献": "TFBibliographyTitle",
        "致谢": "TFAcknowledgements",
    }
    for text, style_id in expected_roles.items():
        assert len(
            document_xml.xpath(
                ".//w:p[w:pPr/w:pStyle[@w:val=$style_id]][.//w:t[text()=$text]]",
                namespaces=NS,
                text=text,
                style_id=style_id,
            )
        ) == 1

    fields = _field_instructions(document_xml)
    assert any(field.startswith("TOC ") for field in fields)
    assert sum(field.startswith("SEQ ") for field in fields) >= 3
    assert any(field == "REF tf_fig_architecture \\h" for field in fields)
    assert any(field == "REF tf_tbl_capabilities \\h" for field in fields)
    assert any(field == "REF tf_eq_pipeline \\h" for field in fields)

    # TF-D4-TOC-019：TOC 字段带可读 cached 条目（ADR-0005 §2.1，D-11）
    toc_entry_paragraphs = document_xml.xpath(
        ".//w:p[w:pPr/w:pStyle[@w:val='TOC1' or @w:val='TOC2' or @w:val='TOC3']]",
        namespaces=NS,
    )
    assert len(toc_entry_paragraphs) == len(
        document_xml.xpath(
            ".//w:p[w:pPr/w:pStyle["
            "starts-with(@w:val, 'Heading') "
            "or @w:val='TFAbstractZHTitle' "
            "or @w:val='TFAbstractENTitle' "
            "or @w:val='TFBibliographyTitle' "
            "or @w:val='TFAcknowledgements'"
            "]]",
            namespaces=NS,
        )
    )
    for entry_paragraph in toc_entry_paragraphs:
        anchor = entry_paragraph.xpath("./w:hyperlink/@w:anchor", namespaces=NS)
        assert len(anchor) == 1
        pageref = entry_paragraph.xpath(
            "./w:hyperlink/w:r/w:instrText[starts-with(., 'PAGEREF ')]/text()",
            namespaces=NS,
        )
        assert pageref == [f"PAGEREF {anchor[0]} \\h"]
        assert anchor[0] in set(
            document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
        )
    footer_fields = tuple(
        field
        for part in sorted(parts)
        if part.startswith("word/footer") and part.endswith(".xml")
        for field in _field_instructions(_xml_part(output, part))
    )
    assert "PAGE" in footer_fields
    assert "NUMPAGES" not in footer_fields

    bookmark_names = set(
        document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
    )
    assert {
        "tf_fig_architecture",
        "tf_tbl_capabilities",
        "tf_eq_pipeline",
        "tf_alg_build",
        "tf_lst_service",
    } <= bookmark_names
    assert document_xml.xpath(".//m:oMath", namespaces=NS)
    assert document_xml.xpath(".//w:footnoteReference", namespaces=NS)
    assert len(document_xml.xpath(".//w:sectPr", namespaces=NS)) >= 3
    assert document_xml.xpath(".//w:headerReference", namespaces=NS)
    assert document_xml.xpath(".//w:footerReference", namespaces=NS)
    assert document_xml.xpath(".//w:drawing", namespaces=NS)
    assert document_xml.xpath(
        ".//w:r[w:rPr/w:vertAlign[@w:val='superscript']]",
        namespaces=NS,
    )

    tables = document_xml.xpath(".//w:tbl", namespaces=NS)
    assert tables
    borders = tables[0].xpath("./w:tblPr/w:tblBorders", namespaces=NS)
    assert borders
    assert borders[0].xpath("./w:top/@w:val", namespaces=NS) == ["single"]
    assert borders[0].xpath("./w:bottom/@w:val", namespaces=NS) == ["single"]
    assert "[1]" in document_text
    assert "[2]" in document_text
    assert "Deterministic Thesis Compilation" in document_text

    footnotes_xml = _xml_part(output, "word/footnotes.xml")
    footnote_text = "".join(
        footnotes_xml.xpath("./w:footnote[@w:id='1']//w:t/text()", namespaces=NS)
    )
    assert "确定性构建" in footnote_text

    normal = styles_xml.xpath(
        "./w:style[@w:styleId='Normal']",
        namespaces=NS,
    )[0]
    assert normal.xpath("./w:rPr/w:rFonts/@w:eastAsia", namespaces=NS) == ["宋体"]
    assert normal.xpath("./w:rPr/w:rFonts/@w:ascii", namespaces=NS) == [
        "Times New Roman"
    ]
    assert normal.xpath("./w:rPr/w:sz/@w:val", namespaces=NS) == ["24"]
    assert normal.xpath("./w:pPr/w:ind/@w:firstLine", namespaces=NS) == ["480"]
    assert normal.xpath("./w:pPr/w:spacing/@w:before", namespaces=NS) == ["0"]
    assert normal.xpath("./w:pPr/w:spacing/@w:after", namespaces=NS) == ["0"]
    assert normal.xpath("./w:pPr/w:spacing/@w:line", namespaces=NS) == ["400"]
    assert normal.xpath("./w:pPr/w:spacing/@w:lineRule", namespaces=NS) == [
        "exact"
    ]
    assert normal.xpath("./w:pPr/w:widowControl", namespaces=NS)

    for style_id in (
        "TFAbstractZHTitle",
        "TFAbstractZHBody",
        "TFKeywordsZH",
        "TFAbstractENTitle",
        "TFAbstractENBody",
        "TFKeywordsEN",
        "TFBibliographyTitle",
        "TFBibliographyEntry",
        "TFAcknowledgements",
        "TOC1",
        "TOC2",
        "TOC3",
    ):
        assert styles_xml.xpath(
            "./w:style[@w:styleId=$style_id]",
            namespaces=NS,
            style_id=style_id,
        )
    assert styles_xml.xpath(
        "./w:style[@w:styleId='TFBibliographyEntry']/w:pPr/w:ind/@w:left",
        namespaces=NS,
    ) == ["420"]
    assert styles_xml.xpath(
        "./w:style[@w:styleId='TFBibliographyEntry']/w:pPr/w:ind/@w:hanging",
        namespaces=NS,
    ) == ["420"]
    for level in (1, 2, 3):
        toc_style = styles_xml.xpath(
            "./w:style[@w:styleId=$style_id]",
            namespaces=NS,
            style_id=f"TOC{level}",
        )[0]
        assert toc_style.xpath(
            "./w:pPr/w:tabs/w:tab/@w:val",
            namespaces=NS,
        ) == ["right"]
        assert toc_style.xpath(
            "./w:pPr/w:tabs/w:tab/@w:leader",
            namespaces=NS,
        ) == ["dot"]

    sections = document_xml.xpath(".//w:sectPr", namespaces=NS)
    assert len(sections) >= 3
    for section in sections:
        assert section.xpath("./w:pgMar/@w:header", namespaces=NS) == ["850"]
        assert section.xpath("./w:pgMar/@w:footer", namespaces=NS) == ["992"]
        assert section.xpath("./w:docGrid/@w:type", namespaces=NS) == ["lines"]
        assert section.xpath("./w:docGrid/@w:linePitch", namespaces=NS) == ["400"]
    assert settings_xml.xpath("./w:evenAndOddHeaders", namespaces=NS)

    main_section = sections[-1]
    references = {
        (
            etree.QName(reference).localname,
            reference.get(f"{{{NS['w']}}}type"),
        ): reference.get(f"{{{NS['r']}}}id")
        for reference in main_section.xpath(
            "./w:headerReference | ./w:footerReference",
            namespaces=NS,
        )
    }
    assert set(references) == {
        ("headerReference", "default"),
        ("headerReference", "first"),
        ("headerReference", "even"),
        ("footerReference", "default"),
        ("footerReference", "first"),
        ("footerReference", "even"),
    }
    targets = _relationship_targets(output)
    default_header = _xml_part(
        output,
        f"word/{targets[references[('headerReference', 'default')]]}",
    )
    even_header = _xml_part(
        output,
        f"word/{targets[references[('headerReference', 'even')]]}",
    )
    first_header = _xml_part(
        output,
        f"word/{targets[references[('headerReference', 'first')]]}",
    )
    assert "湖南工业大学硕士学位论文" in "".join(
        default_header.xpath(".//w:t/text()", namespaces=NS)
    )
    assert "HUNAN UNIVERSITY OF TECHNOLOGY" in "".join(
        even_header.xpath(".//w:t/text()", namespaces=NS)
    )
    assert default_header.xpath(
        ".//w:pBdr/w:bottom/@w:val",
        namespaces=NS,
    ) == ["single"]
    assert not first_header.xpath(".//w:t | .//w:instrText", namespaces=NS)


def test_complete_example_repeated_builds_have_identical_plan_and_word_ooxml(
    tmp_path: Path,
):
    project = _materialize_project(
        tmp_path,
        template_path=HUT_TEMPLATE,
        project_name="acceptance-project",
    )
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"

    source = project / "thesis.md"
    assert _render_plan_snapshot(source) == _render_plan_snapshot(source)
    first_result = _run_cli(tmp_path, "build", str(project), "-o", str(first))
    second_result = _run_cli(tmp_path, "build", str(project), "-o", str(second))

    assert first_result.returncode == 0, first_result.stderr or first_result.stdout
    assert second_result.returncode == 0, second_result.stderr or second_result.stdout
    assert _normalized_word_ooxml(first) == _normalized_word_ooxml(second)


def test_template_failures_return_structured_validation_issues(tmp_path: Path):
    missing_source = tmp_path / "missing.md"
    _write_minimal_source(missing_source, template_id="missing-template-id")
    missing = validation_service(
        missing_source,
        dependencies=_canonical_dependencies(),
    )
    assert {(issue.code, issue.target) for issue in missing.errors} == {
        ("missing-template", "missing-template-id")
    }

    templates = tmp_path / "templates"
    templates.mkdir()
    duplicate_data = yaml.safe_load(HUT_TEMPLATE.read_text(encoding="utf-8"))
    duplicate_data["id"] = "duplicate-template"
    for name in ("first.yaml", "second.yaml"):
        (templates / name).write_text(
            yaml.safe_dump(
                duplicate_data,
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    ambiguous_source = tmp_path / "ambiguous.md"
    _write_minimal_source(
        ambiguous_source,
        template_id="duplicate-template",
    )
    ambiguous = validation_service(
        ambiguous_source,
        dependencies=_canonical_dependencies(),
    )
    assert {(issue.code, issue.target) for issue in ambiguous.errors} == {
        ("ambiguous-template", "duplicate-template")
    }

    invalid_data = yaml.safe_load(HUT_TEMPLATE.read_text(encoding="utf-8"))
    invalid_data["body"]["unknown_policy"] = True
    invalid_template = tmp_path / "invalid.yaml"
    invalid_template.write_text(
        yaml.safe_dump(invalid_data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    invalid = validation_service(
        ambiguous_source,
        template_path=invalid_template,
        dependencies=_canonical_dependencies(),
    )
    assert {(issue.code, issue.target) for issue in invalid.errors} == {
        ("invalid-template", "body.unknown_policy")
    }

    missing_style_data = yaml.safe_load(EXAMPLE_TEMPLATE.read_text(encoding="utf-8"))
    missing_style_data["heading"].pop("level3")
    missing_style_template = tmp_path / "missing-style.yaml"
    missing_style_template.write_text(
        yaml.safe_dump(
            missing_style_data,
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    missing_style = validation_service(
        ambiguous_source,
        template_path=missing_style_template,
        dependencies=_canonical_dependencies(),
    )
    assert {(issue.code, issue.target) for issue in missing_style.errors} == {
        ("missing-template-style", "heading.level3")
    }


def test_complete_example_two_templates_change_style_not_semantics(tmp_path: Path):
    hut_output = tmp_path / "hut.docx"
    alternate_output = tmp_path / "alternate.docx"
    alternate_template = _write_alternate_style_template(tmp_path)
    hut_project = _materialize_project(
        tmp_path,
        template_path=HUT_TEMPLATE,
        project_name="hut-project",
    )
    alternate_project = _materialize_project(
        tmp_path,
        template_path=alternate_template,
        project_name="alternate-project",
    )

    hut_plan = _render_plan_snapshot(hut_project / "thesis.md")
    alternate_plan = _render_plan_snapshot(
        alternate_project / "thesis.md",
    )
    assert hut_plan == alternate_plan

    hut_result = _run_cli(
        tmp_path,
        "build",
        str(hut_project),
        "-o",
        str(hut_output),
    )
    alternate_result = _run_cli(
        tmp_path,
        "build",
        str(alternate_project),
        "-o",
        str(alternate_output),
    )
    assert hut_result.returncode == 0, hut_result.stderr or hut_result.stdout
    assert alternate_result.returncode == 0, (
        alternate_result.stderr or alternate_result.stdout
    )
    assert _semantic_snapshot(hut_output) == _semantic_snapshot(alternate_output)
    hut_ooxml = _normalized_word_ooxml(hut_output)
    alternate_ooxml = _normalized_word_ooxml(alternate_output)
    presentation_parts = {
        name
        for name in hut_ooxml
        if name == "word/styles.xml"
        or name == "word/document.xml"
        or name.startswith(("word/header", "word/footer"))
    }
    assert {
        name: content
        for name, content in hut_ooxml.items()
        if name not in presentation_parts
    } == {
        name: content
        for name, content in alternate_ooxml.items()
        if name not in presentation_parts
    }
    assert _xml_part(hut_output, "word/styles.xml").xpath(
        "./w:style[@w:styleId='Normal']/w:pPr/w:spacing/@w:after",
        namespaces=NS,
    ) == ["0"]
    assert hut_ooxml["word/styles.xml"] != alternate_ooxml["word/styles.xml"]


def test_same_list_markdown_uses_hut_and_default_template_policies_offline(
    tmp_path: Path,
):
    hut_output = tmp_path / "hut-list.docx"
    hut_repeat_output = tmp_path / "hut-list-repeat.docx"
    example_output = tmp_path / "example-list.docx"
    hut_project = _write_list_project(
        tmp_path / "hut-list-project",
        template_path=HUT_TEMPLATE,
    )
    example_project = _write_list_project(
        tmp_path / "example-list-project",
        template_path=EXAMPLE_TEMPLATE,
    )
    input_paths = _project_inputs(hut_project) + _project_inputs(example_project)
    before = {path: _digest(path) for path in input_paths}

    assert _render_plan_snapshot(
        hut_project / "thesis.md",
    ) == _render_plan_snapshot(
        example_project / "thesis.md",
    )

    for project, output in (
        (hut_project, hut_output),
        (hut_project, hut_repeat_output),
        (example_project, example_output),
    ):
        result = _run_cli(
            tmp_path,
            "build",
            str(project),
            "-o",
            str(output),
        )
        assert result.returncode == 0, result.stderr or result.stdout
        validate_docx_package(output)

    assert {path: _digest(path) for path in input_paths} == before
    assert _semantic_snapshot(hut_output) == _semantic_snapshot(hut_repeat_output)
    assert _normalized_word_ooxml(hut_output)[
        "word/numbering.xml"
    ] == _normalized_word_ooxml(hut_repeat_output)["word/numbering.xml"]
    assert _normalized_word_ooxml(hut_output)[
        "word/document.xml"
    ] == _normalized_word_ooxml(hut_repeat_output)["word/document.xml"]

    hut_document = _xml_part(hut_output, "word/document.xml")
    hut_numbering = _xml_part(hut_output, "word/numbering.xml")
    example_document = _xml_part(example_output, "word/document.xml")
    example_numbering = _xml_part(example_output, "word/numbering.xml")
    hut_paragraphs = hut_document.xpath(".//w:p[w:pPr/w:numPr]", namespaces=NS)
    example_paragraphs = example_document.xpath(
        ".//w:p[w:pPr/w:numPr]",
        namespaces=NS,
    )
    assert len(hut_paragraphs) == len(example_paragraphs) == 8
    assert [
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in hut_paragraphs
    ] == [
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in example_paragraphs
    ]
    assert [
        paragraph.xpath("./w:pPr/w:numPr/w:ilvl/@w:val", namespaces=NS)[0]
        for paragraph in hut_paragraphs
    ] == ["0", "1", "2", "3", "0", "1", "2", "3"]

    hut_ordered_id, hut_ordered = _numbering_definition_for_paragraph(
        hut_numbering,
        hut_paragraphs[0],
    )
    hut_unordered_id, hut_unordered = _numbering_definition_for_paragraph(
        hut_numbering,
        hut_paragraphs[4],
    )
    example_ordered_id, example_ordered = _numbering_definition_for_paragraph(
        example_numbering,
        example_paragraphs[0],
    )
    example_unordered_id, example_unordered = _numbering_definition_for_paragraph(
        example_numbering,
        example_paragraphs[4],
    )
    assert hut_ordered_id != hut_unordered_id
    assert example_ordered_id != example_unordered_id

    assert hut_ordered.xpath(
        "./w:lvl[@w:ilvl='0']/w:start/@w:val",
        namespaces=NS,
    ) == ["3"]
    assert hut_ordered.xpath(
        "./w:lvl[@w:ilvl='0']/w:lvlText/@w:val",
        namespaces=NS,
    ) == ["%1、"]
    assert hut_ordered.xpath(
        "./w:lvl[@w:ilvl='1']/w:numFmt/@w:val",
        namespaces=NS,
    ) == ["lowerLetter"]
    assert hut_ordered.xpath(
        "./w:lvl[@w:ilvl='2']/w:numFmt/@w:val",
        namespaces=NS,
    ) == ["lowerRoman"]
    assert hut_ordered.xpath(
        "./w:lvl[@w:ilvl='3']/w:lvlText/@w:val",
        namespaces=NS,
    ) == ["(%4)"]
    assert hut_ordered.xpath(
        "./w:lvl[@w:ilvl='3']/w:pPr/w:ind/@w:left",
        namespaces=NS,
    ) == ["1440"]
    assert hut_unordered.xpath(
        "./w:lvl[@w:ilvl='0']/w:lvlText/@w:val",
        namespaces=NS,
    ) == ["●"]
    assert hut_unordered.xpath(
        "./w:lvl[@w:ilvl='3']/w:lvlText/@w:val",
        namespaces=NS,
    ) == ["■"]

    assert example_ordered.xpath(
        "./w:lvl[@w:ilvl='0']/w:lvlText/@w:val",
        namespaces=NS,
    ) == ["%1."]
    assert example_ordered.xpath(
        "./w:lvl[@w:ilvl='3']/w:pPr/w:ind/@w:left",
        namespaces=NS,
    ) == ["420"]
    assert example_unordered.xpath(
        "./w:lvl[@w:ilvl='3']/w:lvlText/@w:val",
        namespaces=NS,
    ) == ["•"]
    assert etree.tostring(hut_ordered) != etree.tostring(example_ordered)
    assert etree.tostring(hut_unordered) != etree.tostring(example_unordered)

    first_hut_list_paragraph = hut_paragraphs[0]
    assert first_hut_list_paragraph.xpath(
        "./w:r/w:rPr/w:rFonts/@w:eastAsia",
        namespaces=NS,
    ) == ["宋体"]
    assert first_hut_list_paragraph.xpath(
        "./w:r/w:rPr/w:sz/@w:val",
        namespaces=NS,
    ) == ["24"]
    assert first_hut_list_paragraph.xpath(
        "./w:pPr/w:spacing/@w:line",
        namespaces=NS,
    ) == ["400"]
    assert first_hut_list_paragraph.xpath(
        "./w:pPr/w:spacing/@w:lineRule",
        namespaces=NS,
    ) == ["exact"]
    assert first_hut_list_paragraph.xpath(
        "./w:pPr/w:jc/@w:val",
        namespaces=NS,
    ) == ["both"]


def test_hut_template_contains_school_values_without_renderer_hardcoding():
    template = load_template(HUT_TEMPLATE)
    assert template.id == "hut-master-2026"
    assert str(template.page.header_distance) == "15mm"
    assert str(template.page.footer_distance) == "17.5mm"
    assert template.citation is not None
    assert template.citation.presentation == "superscript"
    assert template.sections.main is not None
    assert template.sections.front_matter is not None
    assert template.sections.front_matter.page_number.format == "roman-upper"
    assert template.sections.main.header.even is not None
    assert template.sections.main.footer.default is not None
    assert template.sections.main.footer.default.page_number is not None
    assert template.sections.main.footer.default.page_number.include_total is False
    assert [item.field or item.text for item in template.cover.items[:4]] == [
        "university.name",
        "硕士学位论文",
        "thesis.title",
        "thesis.title_en",
    ]
    assert template.cover.items[0].style.font is not None
    assert template.cover.items[0].style.font.east_asia == "黑体"
    assert str(template.cover.items[0].style.size) == "24pt"
    assert template.cover.items[4].prefix == "培养单位："
    assert str(template.cover.items[4].style.left_indent) == "45mm"
    for level in range(1, 4):
        heading = template.heading.for_level(level)
        assert heading is not None
        assert heading.color == "000000"
        assert heading.alignment == "left"
        assert str(heading.left_indent) == "0pt"
        assert str(heading.right_indent) == "0pt"
        assert str(heading.first_line_indent) == "0pt"
    assert [level.format for level in template.list.ordered.levels] == [
        "decimal",
        "lower_letter",
        "lower_roman",
    ]
    assert [level.marker for level in template.list.unordered.levels] == ["●", "○", "■"]

    renderer_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "src/thesis_forge/renderers/docx").rglob("*.py"))
        if not path.name.startswith("._")
    )
    for school_value in (
        "湖南工业大学",
        "HUNAN UNIVERSITY OF TECHNOLOGY",
        "17.5mm",
        "%1、",
        "●",
    ):
        assert school_value not in renderer_text
