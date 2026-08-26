"""pandoc citeproc 可选外部 citation provider 测试（ADR-0004 §2.4）。

离线部分在任何机器可跑（伪造可执行文件/CSL 路径，不触网不装依赖）；
真 pandoc 用例用 skipif 探测保护（与 soffice 集成测试同款模式），有
pandoc 时逐字节对照 spike 基线（fixture 的 ``pandoc_text`` 字段，
pandoc 3.8.2.1 + 官方 2025 CSL）。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from docforge.bibliography import (
    BuiltinGbt7714Provider,
    LocalBibTeXLoader,
    PandocCiteprocProvider,
    PandocCiteprocUnavailableError,
    UnsupportedCitationStyleError,
    resolve_citation_provider,
)
from docforge.bibliography.engine import BibliographyRecord
from docforge.bibliography.pandoc_provider import record_to_csl_item

FIXTURES = Path(__file__).parent / "fixtures" / "bibliography"
CORPUS_BIB = FIXTURES / "gbt7714-2025-corpus.bib"
CORPUS_GOLDEN = FIXTURES / "gbt7714-2025-corpus.json"

FAKE_EXECUTABLE = "tf-definitely-not-a-real-pandoc-binary"
HAS_PANDOC = shutil.which("pandoc") is not None


def _record(**overrides) -> BibliographyRecord:
    fields = {
        "key": "k1",
        "entry_type": "article",
        "authors": ("王晓明", "李红霞"),
        "title": "示例标题",
        "journal": "示例学报",
        "year": "2024",
        "volume": "58",
        "number": "3",
        "pages": "245-252",
    }
    fields.update(overrides)
    return BibliographyRecord(**fields)


# ---------------------------------------------------------------------------
# 离线：CSL JSON 映射（纯函数）
# ---------------------------------------------------------------------------


def test_record_to_csl_item_article_mapping() -> None:
    item = record_to_csl_item(_record())

    assert item["id"] == "k1"
    assert item["type"] == "article-journal"
    assert item["container-title"] == "示例学报"
    # article 的 BibTeX number 是期号 → CSL issue
    assert item["issue"] == "3" and "number" not in item
    assert item["volume"] == "58"
    assert item["page"] == "245-252"
    assert item["issued"] == {"date-parts": [[2024]]}
    assert item["author"] == [{"literal": "王晓明"}, {"literal": "李红霞"}]


def test_record_to_csl_item_standard_number_keeps_csl_number() -> None:
    item = record_to_csl_item(
        _record(
            key="std", entry_type="standard", journal=None, number="GB/T 7714-2015"
        )
    )

    # legislation 的 number 是标准号（spike 实证：渲染为 "：GB/T 7714-2015"）
    assert item["type"] == "legislation"
    assert item["number"] == "GB/T 7714-2015" and "issue" not in item


def test_record_to_csl_item_names_and_dates() -> None:
    item = record_to_csl_item(
        _record(
            authors=("Zhang, San", "Jean Paul Sartre", "单名"),
            date="2025-03-05",
            urldate="2025-06-01",
            url="https://example.com",
            pages="12--34",
        )
    )

    assert item["author"] == [
        {"family": "Zhang", "given": "San"},
        {"family": "Sartre", "given": "Jean Paul"},
        {"literal": "单名"},
    ]
    assert item["issued"] == {"date-parts": [[2025, 3, 5]]}
    assert item["accessed"] == {"date-parts": [[2025, 6, 1]]}
    assert item["URL"] == "https://example.com"
    assert item["page"] == "12–34"  # BibTeX en-dash 归一


def test_record_to_csl_item_thesis_school_to_publisher() -> None:
    item = record_to_csl_item(
        _record(key="th", entry_type="phdthesis", journal=None, school="湖南大学")
    )

    assert item["type"] == "thesis"
    assert item["publisher"] == "湖南大学"


# ---------------------------------------------------------------------------
# 离线：可用性诊断与 provider 选择
# ---------------------------------------------------------------------------


def test_info_unavailable_when_executable_missing(tmp_path: Path) -> None:
    provider = PandocCiteprocProvider(
        executable=FAKE_EXECUTABLE, csl_path=tmp_path / "nope.csl"
    )
    info = provider.info()

    assert info.available is False
    assert info.version is None
    messages = " | ".join(info.diagnostics)
    assert FAKE_EXECUTABLE in messages
    assert "CSL" in messages  # 不可用原因逐项可读


def test_info_unavailable_on_csl_hash_mismatch(tmp_path: Path) -> None:
    fake_csl = tmp_path / "fake.csl"
    fake_csl.write_text("<cslstyle>not the official file</cslstyle>", encoding="utf-8")
    provider = PandocCiteprocProvider(csl_path=fake_csl)

    info = provider.info()

    assert info.available is False
    assert any("哈希" in message for message in info.diagnostics)


def test_format_bibliography_raises_structured_when_unavailable(tmp_path: Path) -> None:
    provider = PandocCiteprocProvider(
        executable=FAKE_EXECUTABLE, csl_path=tmp_path / "nope.csl"
    )

    with pytest.raises(PandocCiteprocUnavailableError) as excinfo:
        provider.format_bibliography([_record()], [1])
    assert excinfo.value.diagnostics  # 诊断随异常携带


def test_resolve_citation_provider_explicit_selection() -> None:
    builtin = resolve_citation_provider(None)
    assert isinstance(builtin, BuiltinGbt7714Provider)
    assert isinstance(resolve_citation_provider(None, provider="builtin"), BuiltinGbt7714Provider)

    pandoc_provider = resolve_citation_provider(None, provider="pandoc")
    assert isinstance(pandoc_provider, PandocCiteprocProvider)


def test_resolve_citation_provider_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="未知 citation provider"):
        resolve_citation_provider(None, provider="citeproc-py")
    with pytest.raises(UnsupportedCitationStyleError):
        resolve_citation_provider("ieee-what", provider="pandoc")


# ---------------------------------------------------------------------------
# 真 pandoc（本机自装时才运行）
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_PANDOC, reason="pandoc not available")
@pytest.mark.slow
class TestPandocRender:
    def test_corpus_subset_matches_spike_baseline(self) -> None:
        golden = json.loads(CORPUS_GOLDEN.read_text(encoding="utf-8"))
        database = LocalBibTeXLoader().load(CORPUS_BIB)
        provider = PandocCiteprocProvider()
        info = provider.info()
        assert info.available, info.diagnostics

        comparable = [e for e in golden["entries"] if e.get("pandoc_text")]
        assert len(comparable) >= 5  # 抽样下限守卫
        records = [database.records[e["key"]] for e in comparable]
        ordinals = [e["ordinal"] for e in comparable]
        rendered = provider.format_bibliography(records, ordinals)
        by_key = dict(zip((e["key"] for e in comparable), rendered))

        mismatches = []
        for entry in comparable:
            got = by_key[entry["key"]]
            if entry["key"] == "zh-map":
                # 有意差异：CSL JSON 通道给出 GB/T 2025 原生 [CM]，优于
                # spike 时 pandoc bibtex 解析 @map 的 [Z] 兜底（corpus_meta
                # 已记录该引擎盲区）
                assert "[CM]" in got
                continue
            expected = f"[{entry['ordinal']}] {entry['pandoc_text']}"
            if got != expected:
                mismatches.append((entry["key"], got, expected))
        assert not mismatches, mismatches[:3]

    def test_markers_identical_to_builtin(self) -> None:
        database = LocalBibTeXLoader().load(CORPUS_BIB)
        records = list(database.records.values())
        pandoc_provider = PandocCiteprocProvider()
        builtin = BuiltinGbt7714Provider()

        assert pandoc_provider.format_citation(records[:2], [1, 3]) == (
            builtin.format_citation(records[:2], [1, 3])
        )
        assert pandoc_provider.format_citation(
            records[:1], [2], locator="45"
        ) == builtin.format_citation(records[:1], [2], locator="45")
