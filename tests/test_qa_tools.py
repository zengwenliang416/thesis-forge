"""qa/tools 质量门禁工具的测试。

- openxml_validate：对项目自身构建的真 docx 全量通过；对人为破坏的包报出对应失败项。
- no_repair_open：LibreOffice 分支真实运行（本机有 soffice）；
  Word/WPS 不进 CI，仅用 monkeypatch 验证参数解析、JSON 结构与退出码逻辑。
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from docforge.application import preview_service
from docforge.renderers.docx import DocxRenderer

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "qa" / "tools"
EXAMPLE_SOURCE = ROOT / "tests" / "fixtures" / "v2-project" / "document.md"
EXPECTED_CHECKS = {
    "zip_integrity",
    "content_types",
    "relationship_targets",
    "duplicate_relationship_ids",
    "xml_wellformed",
    "document_root",
    "bookmark_pairing",
    "field_pairing",
    "media_relationships",
    "section_properties",
    "style_references",
    "numbering_references",
    "footnote_references",
}

SOFFICE = shutil.which("soffice") or (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").is_file()
    else None
)


def _load_tool(name: str):
    """按路径加载 qa/tools 下的脚本模块（注册进 sys.modules 以支持 dataclass）。"""
    spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


openxml_validate = _load_tool("openxml_validate")
no_repair_open = _load_tool("no_repair_open")


@pytest.fixture(scope="module")
def sample_docx(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """用项目自身构建流程生成真实 docx 作为被测样本。"""
    output = tmp_path_factory.mktemp("qa-sample") / "sample.docx"
    preview = preview_service(EXAMPLE_SOURCE)
    assert preview.plan is not None, preview.issues
    DocxRenderer().render(preview.plan, output)
    return output


def _repack(source: Path, target: Path, drop: set[str] = frozenset(), replace=None):
    """重新打包 docx：删除 drop 中的部件，或用 replace 中的内容替换。"""
    with ZipFile(source) as zin, ZipFile(target, "w") as zout:
        for item in zin.infolist():
            if item.filename in drop:
                continue
            data = (replace or {}).get(item.filename, zin.read(item.filename))
            zout.writestr(item, data)


def _check_map(report: dict) -> dict[str, str]:
    return {check["name"]: check["status"] for check in report["checks"]}


def _run_main(module, argv: list[str], capsys) -> tuple[int, dict]:
    exit_code = module.main(argv)
    report = json.loads(capsys.readouterr().out)
    return exit_code, report


class TestOpenxmlValidate:
    def test_project_build_passes_all_checks(self, sample_docx: Path, capsys):
        exit_code, report = _run_main(openxml_validate, [str(sample_docx)], capsys)
        assert exit_code == 0
        assert report["ok"] is True
        assert {check["name"] for check in report["checks"]} == EXPECTED_CHECKS
        assert all(check["status"] == "pass" for check in report["checks"])

    def test_json_report_written_to_file(
        self, sample_docx: Path, tmp_path: Path, capsys
    ):
        json_path = tmp_path / "report.json"
        exit_code, stdout_report = _run_main(
            openxml_validate, [str(sample_docx), "--json", str(json_path)], capsys
        )
        assert exit_code == 0
        file_report = json.loads(json_path.read_text(encoding="utf-8"))
        assert file_report == stdout_report

    def test_missing_content_types_is_reported(
        self, sample_docx: Path, tmp_path: Path, capsys
    ):
        broken = tmp_path / "no-content-types.docx"
        _repack(sample_docx, broken, drop={"[Content_Types].xml"})
        exit_code, report = _run_main(openxml_validate, [str(broken)], capsys)
        assert exit_code == 1
        checks = _check_map(report)
        assert checks["content_types"] == "fail"
        assert checks["zip_integrity"] == "pass"
        detail = next(
            check["details"][0]
            for check in report["checks"]
            if check["name"] == "content_types"
        )
        assert "[Content_Types].xml" in detail

    def test_broken_document_xml_is_reported(
        self, sample_docx: Path, tmp_path: Path, capsys
    ):
        broken = tmp_path / "broken-xml.docx"
        _repack(sample_docx, broken, replace={"word/document.xml": b"<w:document>"})
        exit_code, report = _run_main(openxml_validate, [str(broken)], capsys)
        assert exit_code == 1
        checks = _check_map(report)
        assert checks["xml_wellformed"] == "fail"
        assert checks["document_root"] == "fail"

    def test_missing_media_part_is_reported(
        self, sample_docx: Path, tmp_path: Path, capsys
    ):
        broken = tmp_path / "no-media.docx"
        _repack(sample_docx, broken, drop={"word/media/image1.png"})
        exit_code, report = _run_main(openxml_validate, [str(broken)], capsys)
        assert exit_code == 1
        checks = _check_map(report)
        assert checks["relationship_targets"] == "fail"

    def test_missing_file_exits_2(self, tmp_path: Path, capsys):
        exit_code, report = _run_main(
            openxml_validate, [str(tmp_path / "missing.docx")], capsys
        )
        assert exit_code == 2
        assert report["ok"] is False

    def test_non_zip_file_exits_2(self, tmp_path: Path, capsys):
        fake = tmp_path / "fake.docx"
        fake.write_text("not a zip", encoding="utf-8")
        exit_code, report = _run_main(openxml_validate, [str(fake)], capsys)
        assert exit_code == 2
        assert report["ok"] is False

    def test_cli_entrypoint(self, sample_docx: Path):
        proc = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "openxml_validate.py"), str(sample_docx)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        assert json.loads(proc.stdout)["ok"] is True


def _fake_record(app: str, result: str) -> dict:
    return {
        "app": app,
        "version": "0.0",
        "result": result,
        "duration_seconds": 0.01,
        "notes": "fake",
    }


class TestNoRepairOpen:
    @pytest.mark.skipif(SOFFICE is None, reason="本机未安装 LibreOffice")
    def test_libreoffice_real_run(self, sample_docx: Path, capsys):
        exit_code, report = _run_main(
            no_repair_open,
            [str(sample_docx), "--apps", "libreoffice", "--timeout", "120"],
            capsys,
        )
        assert exit_code == 0
        (result,) = report["results"]
        assert result["app"] == "libreoffice"
        assert result["result"] == "pass"
        assert result["version"] != "unknown"
        assert result["duration_seconds"] > 0

    def test_apps_subset_and_json_structure(
        self, sample_docx: Path, capsys, monkeypatch
    ):
        monkeypatch.setattr(
            no_repair_open,
            "APP_CHECKS",
            {
                "word": lambda docx, timeout: _fake_record("word", "pass"),
                "wps": lambda docx, timeout: _fake_record("wps", "pending-human-review"),
            },
        )
        exit_code, report = _run_main(
            no_repair_open, [str(sample_docx), "--apps", "word,wps"], capsys
        )
        assert exit_code == 0
        assert report["ok"] is True
        assert [item["app"] for item in report["results"]] == ["word", "wps"]
        for item in report["results"]:
            assert {"app", "version", "result", "duration_seconds", "notes"} <= set(item)

    def test_fail_result_exits_1(self, sample_docx: Path, capsys, monkeypatch):
        monkeypatch.setattr(
            no_repair_open,
            "APP_CHECKS",
            {"word": lambda docx, timeout: _fake_record("word", "fail")},
        )
        exit_code, report = _run_main(
            no_repair_open, [str(sample_docx), "--apps", "word"], capsys
        )
        assert exit_code == 1
        assert report["ok"] is False

    def test_pending_and_skipped_do_not_fail(
        self, sample_docx: Path, capsys, monkeypatch
    ):
        monkeypatch.setattr(
            no_repair_open,
            "APP_CHECKS",
            {
                "word": lambda docx, timeout: _fake_record("word", "skipped"),
                "wps": lambda docx, timeout: _fake_record("wps", "pending-human-review"),
            },
        )
        exit_code, report = _run_main(
            no_repair_open, [str(sample_docx), "--apps", "word,wps"], capsys
        )
        assert exit_code == 0
        assert report["ok"] is True

    def test_unknown_app_rejected(self, sample_docx: Path):
        with pytest.raises(SystemExit) as excinfo:
            no_repair_open.main([str(sample_docx), "--apps", "word,emacs"])
        assert excinfo.value.code == 2

    def test_unreadable_file_exits_2(self, tmp_path: Path, capsys):
        fake = tmp_path / "fake.docx"
        fake.write_text("not a zip", encoding="utf-8")
        exit_code, report = _run_main(no_repair_open, [str(fake)], capsys)
        assert exit_code == 2
        assert report["ok"] is False
        exit_code, _ = _run_main(no_repair_open, [str(tmp_path / "missing.docx")], capsys)
        assert exit_code == 2
