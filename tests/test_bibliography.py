from __future__ import annotations

import json
from pathlib import Path

import pytest

from docforge.bibliography import (
    DEFAULT_CITATION_STYLE,
    BibliographyParseError,
    BuiltinGbt7714Provider,
    CitationProvider,
    DuplicateBibliographyKeyError,
    Gbt7714Formatter,
    LocalBibTeXLoader,
    MissingBibliographyFieldError,
    UnsupportedBibliographyTypeError,
    UnsupportedCitationStyleError,
    normalize_citation_style,
    probe_executable_version,
    resolve_citation_provider,
    supported_citation_styles,
)

FIXTURES = Path(__file__).parent / "fixtures" / "bibliography"


def test_local_bibtex_loader_normalizes_supported_v1_records():
    database = LocalBibTeXLoader().load(FIXTURES / "gbt7714-v1.bib")

    assert tuple(database.records) == (
        "smith2025",
        "doe2024",
        "lee2023",
        "chen2022",
        "liu2021",
        "uncited2020",
    )
    article = database.records["smith2025"]
    assert article.entry_type == "article"
    assert article.authors == ("Smith, John", "Wang, Li")
    assert article.title == "Deterministic Thesis Compilation"
    assert article.pages == "101-118"
    assert article.doi == "10.1000/tf.2025.001"
    assert database.records["chen2022"].school == "Tsinghua University"


def test_gbt7714_v1_formatter_matches_reviewed_golden_fixture():
    expected = json.loads(
        (FIXTURES / "gbt7714-v1.json").read_text(encoding="utf-8")
    )
    database = LocalBibTeXLoader().load(FIXTURES / "gbt7714-v1.bib")
    formatter = Gbt7714Formatter()
    citation = expected["citation"]
    citation_records = tuple(database.records[key] for key in citation["keys"])
    bibliography_keys = ("doe2024", "smith2025", "lee2023", "chen2022", "liu2021")
    bibliography_records = tuple(database.records[key] for key in bibliography_keys)

    assert formatter.format_citation(
        citation_records,
        tuple(citation["ordinals"]),
        locator=citation["locator"],
    ) == citation["text"]
    assert formatter.format_bibliography(
        bibliography_records,
        tuple(range(1, len(bibliography_records) + 1)),
    ) == tuple(expected["bibliography"])
    assert all("This Record Must Not Render" not in item for item in expected["bibliography"])


@pytest.mark.parametrize(
    ("content", "error_type", "message"),
    [
        (
            "@article{broken, author={Smith, John}, title={Missing close}",
            BibliographyParseError,
            "unterminated",
        ),
        (
            (
                "@book{duplicate, author={Doe, Jane}, title={One}, "
                "publisher={P}, year={2024}}\n"
                "@book{duplicate, author={Doe, Jane}, title={Two}, "
                "publisher={P}, year={2025}}"
            ),
            DuplicateBibliographyKeyError,
            "duplicate",
        ),
        (
            "@misc{unsupported, author={Doe, Jane}, title={Unknown}, year={2024}}",
            UnsupportedBibliographyTypeError,
            "misc",
        ),
        (
            "@article{missing, author={Doe, Jane}, title={No Journal}, year={2024}}",
            MissingBibliographyFieldError,
            "journal",
        ),
    ],
)
def test_local_bibtex_loader_rejects_invalid_input(
    tmp_path: Path,
    content: str,
    error_type: type[ValueError],
    message: str,
):
    path = tmp_path / "invalid.bib"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(error_type, match=message):
        LocalBibTeXLoader().load(path)


# ---------------------------------------------------------------------------
# GB/T 7714-2025 golden corpus（ADR-0004）
#
# 语料从 spikes/phase0/citation/corpus/gbt7714-corpus.bib 逐字节复制；golden
# JSON 中 19 条 passed-machine-check 逐字节锁定为内建引擎回归基线，9 条
# pending-human-review 仅校验结构完整性（must_contain），GA 前人工定稿后
# 转为逐字节（见 golden 文件 policy 字段与 ADR-0004 §2.6）。
# ---------------------------------------------------------------------------

CORPUS_BIB = FIXTURES / "gbt7714-2025-corpus.bib"
CORPUS_GOLDEN = FIXTURES / "gbt7714-2025-corpus.json"


def _corpus():
    golden = json.loads(CORPUS_GOLDEN.read_text(encoding="utf-8"))
    database = LocalBibTeXLoader().load(CORPUS_BIB)
    return golden, database


def test_gbt7714_2025_corpus_loads_all_28_entries():
    golden, database = _corpus()

    assert len(database.records) == 28
    assert tuple(database.records) == tuple(entry["key"] for entry in golden["entries"])
    # 逐条核对 corpus 覆盖的 BibTeX 类型（ADR-0004 §2.2 验收范围）。
    types = {record.entry_type for record in database.records.values()}
    assert types == {
        "article", "book", "incollection", "inproceedings", "collection",
        "mastersthesis", "phdthesis", "techreport", "standard", "patent",
        "online", "dataset", "map", "unpublished",
    }
    # 版本、译者、日期、URL 字段不丢失。
    edition = database.records["en-book-edition"]
    assert edition.edition == "2"
    translator = database.records["zh-book-translator"]
    assert translator.translators == ("周琪", "刘绯")
    newspaper = database.records["zh-newspaper"]
    assert newspaper.date == "2025-03-05" and newspaper.year == "2025"
    online = database.records["zh-online"]
    assert online.url and online.urldate == "2025-06-01"


def test_gbt7714_2025_corpus_passed_entries_match_golden_byte_exact():
    golden, database = _corpus()
    formatter = Gbt7714Formatter()
    passed = [entry for entry in golden["entries"] if entry["review"] == "passed-machine-check"]
    assert len(passed) == 19  # 守卫：golden 治理要求人工审查后才允许增减

    for entry in passed:
        (rendered,) = formatter.format_bibliography(
            [database.records[entry["key"]]],
            [entry["ordinal"]],
        )
        assert rendered == entry["text"], entry["key"]


def test_gbt7714_2025_corpus_pending_entries_structural_only():
    # pending-human-review：验证结构完整性而非精确匹配；定稿前不得改为
    # 逐字节断言（spikes/phase0/citation golden 的 9 条 pending 同源）。
    golden, database = _corpus()
    formatter = Gbt7714Formatter()
    pending = [entry for entry in golden["entries"] if entry["review"] == "pending-human-review"]
    assert len(pending) == 9

    for entry in pending:
        (rendered,) = formatter.format_bibliography(
            [database.records[entry["key"]]],
            [entry["ordinal"]],
        )
        assert rendered.startswith(f"[{entry['ordinal']}] "), entry["key"]
        for token in entry["must_contain"]:
            assert token in rendered, f"{entry['key']}: {token}"


def _single_record(content: str, tmp_path: Path):
    path = tmp_path / "single.bib"
    path.write_text(content, encoding="utf-8")
    database = LocalBibTeXLoader().load(path)
    return next(iter(database.records.values()))


def _render(record, ordinal: int = 1) -> str:
    (rendered,) = Gbt7714Formatter().format_bibliography([record], [ordinal])
    return rendered


def test_truncation_uses_et_al_for_western_and_deng_for_chinese(tmp_path: Path):
    chinese = _single_record(
        """@article{zh5,
  author = {刘洋 and 赵敏 and 孙建国 and 周丽萍 and 吴国强},
  title = {城市轨道交通客流预测方法综述},
  journal = {交通运输工程学报},
  year = {2023}
}
""",
        tmp_path,
    )
    western = _single_record(
        """@article{en4,
  author = {Smith, John and Doe, Jane and Roe, Richard and Poe, Ann},
  title = {Deterministic Compilation},
  journal = {Journal of Document Engineering},
  year = {2024},
  langid = {english}
}
""",
        tmp_path,
    )

    assert "刘洋，赵敏，孙建国，等." in _render(chinese)
    assert "SMITH J, DOE J, ROE R, et al." in _render(western)


def test_language_heuristic_and_punctuation_switch(tmp_path: Path):
    # 无 langid 时按题名/著者字符启发式判定：中文著者 + 西文题名仍按中文
    # 条目输出全角标点。
    mixed = _single_record(
        """@article{mixed,
  author = {张伟 and 李娜},
  title = {An Efficient Algorithm},
  journal = {Chinese Journal of Computers},
  year = {2023},
  volume = {46},
  number = {9},
  pages = {1901--1915}
}
""",
        tmp_path,
    )
    # langid 优先于字符启发式：全 CJK 题名 + langid=english 按西文渲染。
    forced = _single_record(
        """@book{forced,
  author = {Huntington, Samuel P},
  title = {文明的冲突},
  publisher = {新华出版社},
  year = {2010},
  langid = {english}
}
""",
        tmp_path,
    )

    assert "Computers，2023，46（9）：1901-1915." in _render(mixed)
    assert "HUNTINGTON SP. 文明的冲突[M]. 新华出版社, 2010." == _render(forced).removeprefix("[1] ")


def test_article_without_volume_omits_comma_before_issue(tmp_path: Path):
    record = _single_record(
        """@article{novol,
  author = {陈思远},
  title = {乡村教师队伍建设的路径分析},
  journal = {教育研究},
  year = {2023},
  number = {6},
  pages = {88--95}
}
""",
        tmp_path,
    )

    # 修复缺陷："2023, (6)" → "2023（6）"。
    assert "教育研究，2023（6）：88-95." in _render(record)


def test_book_edition_and_translator_render(tmp_path: Path):
    record = _single_record(
        """@book{edition,
  author = {Kuhn, Thomas S},
  title = {The Structure of Scientific Revolutions},
  edition = {2},
  address = {Chicago},
  publisher = {University of Chicago Press},
  year = {1970},
  langid = {english}
}
""",
        tmp_path,
    )

    assert _render(record).endswith("[M]. 2nd ed. Chicago: University of Chicago Press, 1970.")


# ---------------------------------------------------------------------------
# CitationProvider 接口与注册表（ADR-0004 §2.1，D-07）
# ---------------------------------------------------------------------------


def test_citation_style_aliases_normalize_to_default_style():
    for alias in ("GB-T-7714-2025", "gb-t-7714-2025", "GBT7714", "gbt7714-2025", "gbt7714-2025-numeric", " GB-T-7714-2025 "):
        assert normalize_citation_style(alias) == DEFAULT_CITATION_STYLE
    assert normalize_citation_style("apa") is None


def test_resolve_citation_provider_defaults_to_builtin_gbt7714():
    provider = resolve_citation_provider(None)

    assert isinstance(provider, CitationProvider)
    assert isinstance(provider, BuiltinGbt7714Provider)
    info = provider.info()
    assert info.available and info.version is None and info.diagnostics == ()
    assert DEFAULT_CITATION_STYLE in info.styles

    for alias in ("GB-T-7714-2025", "gbt7714"):
        assert isinstance(resolve_citation_provider(alias), BuiltinGbt7714Provider)

    with pytest.raises(UnsupportedCitationStyleError) as error:
        resolve_citation_provider("apa")
    assert error.value.style == "apa"
    assert error.value.supported_styles == supported_citation_styles()


def test_probe_executable_version_reports_missing_binary():
    assert probe_executable_version("thesisforge-definitely-not-installed") is None
