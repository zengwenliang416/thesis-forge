"""Template Package v2 `.tftpl` 打包/校验/解包与 v0.3→v2 迁移（SCHEMA §7/§8）。

正例使用 spike 样例包 `spikes/phase0/docx-template/package-sample/` 与 v0.3
模板 `templates/base/bachelor.yaml`；负例（篡改 / Zip Slip / 解压炸弹）
在 tmp_path 手工构造。
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from thesis_forge.cli import app
from thesis_forge.templates import v2
from thesis_forge.templates.v2.migrate import (
    DROPPED,
    MANUAL_REQUIRED,
    MIGRATED,
    MigrateError,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACKAGE = (
    REPO_ROOT / "spikes" / "phase0" / "docx-template" / "package-sample"
)
BACHELOR_YAML = REPO_ROOT / "templates" / "base" / "bachelor.yaml"

runner = CliRunner()


# ---------------------------------------------------------------------------
# 构造辅助
# ---------------------------------------------------------------------------


def _write_l1_complete_package(package_dir: Path, data: dict) -> Path:
    """最小 L1/L2 合法包（与 test_template_v2.py 同款构造）。"""
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "template.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.'
        'wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body/></w:document>"
    )
    with zipfile.ZipFile(package_dir / "reference.docx", "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document)
    (package_dir / "README.md").write_text(
        "# 演示模板\n\n## 使用说明\n\n略。\n\n## 已知限制\n\n略。\n", encoding="utf-8"
    )
    (package_dir / "provenance.yaml").write_text(
        "school:\n"
        "  name: 演示大学\n"
        "  official_document:\n"
        "    title: 演示大学学位论文撰写规范\n"
        '    version: "2026"\n'
        "    source_type: manual\n"
        "maintainers:\n"
        "  - name: 演示维护者\n"
        "    contact: mailto:maintainer@example.invalid\n"
        "licenses:\n"
        "  template_code: Apache-2.0\n"
        "  school_assets: CC0-1.0\n"
        "review:\n"
        "  last_verified: 2026-08-15\n"
        "  verified_with:\n"
        "    - LibreOffice 25.x\n",
        encoding="utf-8",
    )
    (package_dir / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## {data['version']}\n\n- 初始版本。\n", encoding="utf-8"
    )
    minimal = package_dir / "fixtures" / "minimal"
    minimal.mkdir(parents=True)
    (minimal / "thesis.md").write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")
    return package_dir


def _template_data(**overrides) -> dict:
    data = {
        "schema_version": 2,
        "id": "demo.pack",
        "version": "1.0.0",
        "name": "演示模板",
        "compatibility": {
            "thesisforge": ">=0.0.0",
            "document_types": ["master_thesis"],
        },
        "page": {
            "margin": {"top": "25mm", "bottom": "25mm", "inner": "30mm", "outer": "25mm"}
        },
        "fonts": {"body": {"east_asia": "宋体", "latin": "Times New Roman"}},
        "styles": {
            "paragraph": {"body": "TF Body"},
            "heading": {
                "1": "TF Heading 1",
                "2": "TF Heading 2",
                "3": "TF Heading 3",
                "4": "TF Heading 4",
            },
        },
        "regions": {"order": ["main"]},
    }
    data.update(overrides)
    return data


def _repack_with_tamper(tftpl: Path, output: Path, target: str) -> None:
    """重打包并篡改指定 entry 内容（manifest 保持不变）。"""
    with zipfile.ZipFile(tftpl) as source, zipfile.ZipFile(output, "w") as sink:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == target:
                data = data + b"tampered"
            sink.writestr(info.filename, data)


def _build_malicious_tftpl(
    output: Path, entries: dict[str, bytes], *, manifest_entries: list[str] | None
) -> None:
    """手工构造 .tftpl：manifest.json + 给定 entry。"""
    names = manifest_entries if manifest_entries is not None else list(entries)
    manifest = {
        "manifest_version": 1,
        "generator": {"name": "thesisforge", "version": "0.1.0"},
        "template": {
            "id": "demo.pack",
            "version": "1.0.0",
            "schema_version": 2,
            "language": "zh-CN",
        },
        "compatibility": {
            "thesisforge": ">=0.0.0",
            "document_types": ["master_thesis"],
        },
        "entries": [
            {
                "path": name,
                "sha256": "sha256:" + hashlib.sha256(entries[name]).hexdigest(),
                "size": len(entries[name]),
            }
            for name in sorted(names)
            if name in entries
        ],
        "provenance_hash": "sha256:" + "0" * 64,
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        for name, data in entries.items():
            archive.writestr(name, data)


# ---------------------------------------------------------------------------
# pack / verify / unpack 闭环
# ---------------------------------------------------------------------------


def test_pack_verify_unpack_load_roundtrip(tmp_path: Path) -> None:
    tftpl = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "sample.tftpl")
    assert tftpl.is_file()

    report = v2.verify_package(tftpl)
    assert not report.has_errors, [i.message for i in report.issues]
    assert report.package is not None
    assert report.package.template.id == "hunan-university-of-technology.master.2026.sample"
    assert any(i.code == "signature-absent" for i in report.issues)  # §7.3 info

    dest = tmp_path / "unpacked"
    v2.unpack_package(tftpl, dest)
    package = v2.load_package(dest)
    assert package.template.id == "hunan-university-of-technology.master.2026.sample"
    assert package.reference_docx.is_file()


def test_pack_manifest_structure(tmp_path: Path) -> None:
    tftpl = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "sample.tftpl")
    with zipfile.ZipFile(tftpl) as archive:
        names = archive.namelist()
        assert names[0] == "manifest.json"  # §7.2：manifest.json 居首
        assert names[1:] == sorted(names[1:], key=lambda n: n.encode("utf-8"))
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)  # 固定 DOS 纪元
            assert info.compress_type == zipfile.ZIP_DEFLATED
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

    assert manifest["manifest_version"] == 1
    assert manifest["generator"]["name"] == "thesisforge"
    header = yaml.safe_load(
        (SAMPLE_PACKAGE / "template.yaml").read_text(encoding="utf-8")
    )
    assert manifest["template"] == {
        "id": header["id"],
        "version": header["version"],
        "schema_version": 2,
        "language": header["language"],
    }
    assert manifest["compatibility"] == header["compatibility"]
    paths = [entry["path"] for entry in manifest["entries"]]
    assert "manifest.json" not in paths and "signature.json" not in paths
    assert paths == sorted(paths, key=lambda n: n.encode("utf-8"))
    assert set(paths) == set(names[1:])
    for entry in manifest["entries"]:
        data = (SAMPLE_PACKAGE / entry["path"]).read_bytes()
        assert entry["sha256"] == "sha256:" + hashlib.sha256(data).hexdigest()
        assert entry["size"] == len(data)
    expected_provenance = hashlib.sha256(
        (SAMPLE_PACKAGE / "provenance.yaml").read_bytes()
    ).hexdigest()
    assert manifest["provenance_hash"] == "sha256:" + expected_provenance


def test_pack_deterministic(tmp_path: Path) -> None:
    first = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "a.tftpl")
    second = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "b.tftpl")
    assert first.read_bytes() == second.read_bytes()


def test_pack_excludes_junk_and_rebuilds_manifest(tmp_path: Path) -> None:
    package_dir = _write_l1_complete_package(tmp_path / "pkg", _template_data())
    (package_dir / ".DS_Store").write_bytes(b"junk")
    (package_dir / ".hidden").write_bytes(b"junk")
    (package_dir / "manifest.json").write_text("{}", encoding="utf-8")  # 目录形态误置
    tftpl = v2.pack_package(package_dir, tmp_path / "pkg.tftpl")
    with zipfile.ZipFile(tftpl) as archive:
        names = archive.namelist()
    assert ".DS_Store" not in names and ".hidden" not in names
    manifest = json.loads(zipfile.ZipFile(tftpl).read("manifest.json"))
    assert manifest["manifest_version"] == 1  # 剔除后重建，非目录形态那份


def test_pack_refused_when_lint_fails(tmp_path: Path) -> None:
    bad = dict(_template_data())
    bad["unknown_section"] = {"foo": "bar"}  # extra=forbid → L2 invalid-template
    package_dir = _write_l1_complete_package(tmp_path / "bad", bad)
    output = tmp_path / "bad.tftpl"
    with pytest.raises(v2.PackError) as excinfo:
        v2.pack_package(package_dir, output)
    assert any(i.code == "invalid-template" for i in excinfo.value.issues)
    assert not output.exists()  # 失败不产出包


def test_pack_output_inside_package_rejected(tmp_path: Path) -> None:
    package_dir = _write_l1_complete_package(tmp_path / "pkg", _template_data())
    with pytest.raises(v2.PackError):
        v2.pack_package(package_dir, package_dir / "self.tftpl")


# ---------------------------------------------------------------------------
# verify 负例：篡改 / Zip Slip / 解压炸弹
# ---------------------------------------------------------------------------


def test_verify_tampered_entry_fails(tmp_path: Path) -> None:
    tftpl = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "sample.tftpl")
    tampered = tmp_path / "tampered.tftpl"
    _repack_with_tamper(tftpl, tampered, "README.md")
    report = v2.verify_package(tampered)
    assert report.has_errors
    assert any(i.code == "hash-mismatch" and i.target == "README.md" for i in report.issues)


def test_verify_manifest_template_mismatch(tmp_path: Path) -> None:
    tftpl = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "sample.tftpl")
    mismatched = tmp_path / "mismatched.tftpl"
    with zipfile.ZipFile(tftpl) as source:
        entries = {info.filename: source.read(info.filename) for info in source.infolist()}
    manifest = json.loads(entries["manifest.json"])
    manifest["template"]["version"] = "9.9.9"  # entries 不动，只改 header 元数据
    entries["manifest.json"] = json.dumps(manifest).encode("utf-8")
    with zipfile.ZipFile(mismatched, "w") as sink:
        for name, data in entries.items():
            sink.writestr(name, data)
    report = v2.verify_package(mismatched)
    assert report.has_errors
    assert any(i.code == "manifest-mismatch" for i in report.issues)


@pytest.mark.parametrize(
    "evil_name",
    ["../evil.txt", "sub/../../evil.txt", "/abs/evil.txt", "C:\\evil.txt", "a\\b.txt"],
)
def test_verify_zip_slip_rejected(tmp_path: Path, evil_name: str) -> None:
    malicious = tmp_path / "evil.tftpl"
    _build_malicious_tftpl(
        malicious, {evil_name: b"evil", "README.md": b"x"}, manifest_entries=None
    )
    report = v2.verify_package(malicious)
    assert report.has_errors
    assert any(i.code == "package-path-unsafe" for i in report.issues)


def test_verify_bomb_single_file_limit(tmp_path: Path) -> None:
    payload = b"\0" * (65 * 1024 * 1024)  # 65 MB 零字节，压缩后极小
    bomb = tmp_path / "bomb.tftpl"
    _build_malicious_tftpl(bomb, {"big.bin": payload}, manifest_entries=None)
    assert bomb.stat().st_size < 1024 * 1024  # 确为高压缩率构造
    report = v2.verify_package(bomb)
    assert report.has_errors
    assert any(
        i.code == "package-path-unsafe" and "64 MB" in i.message for i in report.issues
    )


def test_verify_rejects_missing_manifest(tmp_path: Path) -> None:
    bare = tmp_path / "bare.tftpl"
    with zipfile.ZipFile(bare, "w") as archive:
        archive.writestr("README.md", "x")
    report = v2.verify_package(bare)
    assert report.has_errors
    assert any(i.code == "missing-package-file" for i in report.issues)


def test_unpack_refuses_nonempty_dest(tmp_path: Path) -> None:
    tftpl = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "sample.tftpl")
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "existing.txt").write_text("x", encoding="utf-8")
    with pytest.raises(v2.PackError):
        v2.unpack_package(tftpl, dest)


# ---------------------------------------------------------------------------
# migrate
# ---------------------------------------------------------------------------


def test_migrate_bachelor_ledger_and_lint(tmp_path: Path) -> None:
    out = tmp_path / "bachelor-v2"
    report = v2.migrate_template(BACHELOR_YAML, out)

    assert not report.lint_report.has_errors, [
        i.message for i in report.lint_report.issues
    ]
    assert {"L1", "L2", "L3"} <= set(report.lint_report.levels_run)

    by_field = {entry.field: entry for entry in report.entries}
    assert {entry.status for entry in report.entries} <= {
        MIGRATED,
        MANUAL_REQUIRED,
        DROPPED,
    }
    assert by_field["id"].status == MIGRATED
    assert by_field["id"].target == "template.yaml#id"
    assert by_field["page.margin.left/right"].status == MIGRATED
    assert by_field["year"].status == MANUAL_REQUIRED
    assert by_field["citation.style"].status == MANUAL_REQUIRED
    assert by_field["cover.items"].status == MANUAL_REQUIRED
    # dropped：显式值与 v2 默认一致（figure.numbering.separator 等）
    dropped = [e for e in report.entries if e.status == DROPPED]
    assert dropped and all(e.reason for e in dropped)
    assert any(e.field == "figure.numbering.separator" for e in dropped)
    assert report.summary[MANUAL_REQUIRED] >= 1

    # 产物结构 + 可加载
    for name in (
        "template.yaml",
        "reference.docx",
        "provenance.yaml",
        "README.md",
        "CHANGELOG.md",
        "migration-report.json",
    ):
        assert (out / name).is_file(), name
    assert any((out / "fixtures" / "minimal").iterdir())
    package = v2.load_package(out)
    assert package.template.id == "bachelor-base"
    assert package.template.version == "0.1.0"
    page = package.resolved_data["page"]
    assert page["margin"]["inner"] == "30mm"  # v0.3 left → v2 inner
    assert page["mirror_margins"] is False
    assert "TF Body" in report.reference_styles
    assert "TF Heading 4" in report.reference_styles

    saved = json.loads((out / "migration-report.json").read_text(encoding="utf-8"))
    assert saved["summary"] == report.summary
    assert saved["lint"]["errors"] == 0
    assert {e["status"] for e in saved["entries"]} <= set(v2.LEDGER_STATUSES)


def test_migrate_school_template_with_sections(tmp_path: Path) -> None:
    source = REPO_ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
    out = tmp_path / "example-v2"
    report = v2.migrate_template(source, out)
    assert not report.lint_report.has_errors
    sections = report.lint_report and v2.load_package(out).resolved_data["sections"]
    assert sections["cover"]["page_number"] == {"display": False}  # format: none → display
    assert sections["front_matter"]["page_number"]["format"] == "roman-upper"
    manual_fields = {e.field for e in report.entries if e.status == MANUAL_REQUIRED}
    assert any(f.startswith("sections.") and "footer" in f for f in manual_fields)


def test_migrate_refuses_nonempty_output_and_is_idempotent(tmp_path: Path) -> None:
    out = tmp_path / "bachelor-v2"
    first = v2.migrate_template(BACHELOR_YAML, out, today=date(2026, 8, 15))
    with pytest.raises(MigrateError):
        v2.migrate_template(BACHELOR_YAML, out)  # 非空目录拒绝覆盖
    second = v2.migrate_template(BACHELOR_YAML, out, force=True, today=date(2026, 8, 15))
    # 幂等：同参数重复执行，台账与 template.yaml 产物一致
    assert first.entries == second.entries
    assert (out / "template.yaml").read_bytes()


# ---------------------------------------------------------------------------
# CLI 退出码
# ---------------------------------------------------------------------------


def test_cli_template_pack_success(tmp_path: Path) -> None:
    output = tmp_path / "sample.tftpl"
    result = runner.invoke(app, ["template", "pack", str(SAMPLE_PACKAGE), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert output.is_file()


def test_cli_template_pack_missing_dir_exits_two(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["template", "pack", str(tmp_path / "missing"), "-o", str(tmp_path / "x.tftpl")]
    )
    assert result.exit_code == 2


def test_cli_template_pack_lint_failure_exits_one(tmp_path: Path) -> None:
    bad = dict(_template_data())
    bad["unknown_section"] = {}
    package_dir = _write_l1_complete_package(tmp_path / "bad", bad)
    result = runner.invoke(
        app, ["template", "pack", str(package_dir), "-o", str(tmp_path / "x.tftpl")]
    )
    assert result.exit_code == 1


def test_cli_template_verify_exit_codes(tmp_path: Path) -> None:
    tftpl = v2.pack_package(SAMPLE_PACKAGE, tmp_path / "sample.tftpl")
    ok = runner.invoke(app, ["template", "verify", str(tftpl)])
    assert ok.exit_code == 0, ok.output

    tampered = tmp_path / "tampered.tftpl"
    _repack_with_tamper(tftpl, tampered, "README.md")
    bad = runner.invoke(app, ["template", "verify", str(tampered), "--json"])
    assert bad.exit_code == 1
    payload = json.loads(bad.output)
    assert any(i["code"] == "hash-mismatch" for i in payload["issues"])

    missing = runner.invoke(app, ["template", "verify", str(tmp_path / "none.tftpl")])
    assert missing.exit_code == 2


def test_cli_template_migrate_exit_codes(tmp_path: Path) -> None:
    out = tmp_path / "bachelor-v2"
    result = runner.invoke(app, ["template", "migrate", str(BACHELOR_YAML), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert (out / "migration-report.json").is_file()

    again = runner.invoke(app, ["template", "migrate", str(BACHELOR_YAML), "-o", str(out)])
    assert again.exit_code == 2  # 非空目录拒绝覆盖

    forced = runner.invoke(
        app, ["template", "migrate", str(BACHELOR_YAML), "-o", str(out), "--force"]
    )
    assert forced.exit_code == 0, forced.output

    missing = runner.invoke(
        app, ["template", "migrate", str(tmp_path / "none.yaml"), "-o", str(tmp_path / "x")]
    )
    assert missing.exit_code == 2
