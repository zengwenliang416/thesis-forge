"""pandoc citeproc 可选外部 citation provider（ADR-0004 §2.4）。

进程边界约定（`bibliography/provider.py` 模块注释）：

- 子进程调用用户自装的 pandoc，输入走 CSL JSON 通道，输出解析为纯文本条目；
- pandoc 不随包分发、不进入编译依赖——`resolve_citation_provider` 只有在
  调用方**显式选择**本 provider 时才会构造它；默认路径永远是内建引擎
  （离线、确定性）；
- 构造期不抛错：可用性探测延迟到 `info()`，不可用时返回
  ``ProviderInfo(available=False, diagnostics=...)``，调用方据此回退默认
  provider 或给出结构化诊断；
- CSL 固定为官方 GB/T 7714-2025 numeric（ADR-0004 §2.5 记录来源、commit
  与 SHA256）；副本缺失或哈希不符都视为不可用。

与内建引擎的分工：正文引用标记（``[1-3]`` 上标序列）**不外委**——编号是
编译器权威计算结果（AGENTS.md §3），标记复用内建 formatter，保证两个
provider 的正文标记逐字节一致；pandoc 只负责文后参考文献条目文本。

注意：本 provider 输出随 pandoc 版本浮动，因此**不进入离线回归基线**；
golden corpus 的生成与引擎回归基线固定使用 pandoc + 官方 CSL（§2.4）。
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .engine import BibliographyError, BibliographyRecord
from .formatter import Gbt7714Formatter
from .provider import (
    DEFAULT_CITATION_STYLE,
    ProviderInfo,
    probe_executable_version,
)

PANDOC_PROVIDER_NAME = "pandoc-citeproc"

# ADR-0004 §2.5：官方 CSL 仓库 2025 numeric 版，commit 440c9c9…（2026-05-10），
# CC-BY-SA-3.0。进入模板包时须按 Template Package v2 §1.1 做哈希与
# provenance 对账；在此之前运行时副本取自 spike 语料目录。
GB_T_2025_CSL_SHA256 = (
    "3b5ab6249ce23b57954c9a4a67e0df422d8759b0573cae7e7de2f2ef94895faf"
)
_DEFAULT_CSL_RELPATH = Path(
    "spikes/phase0/citation/corpus/"
    "china-national-standard-gb-t-7714-2025-numeric.csl"
)

# numeric CSL 会在条目文本前渲染 citeproc 自己的序号前缀；编号是编译器
# 权威结果（AGENTS.md §3），剥掉后由 format_bibliography 重加。
_ORDINAL_PREFIX_RE = re.compile(r"^\[\d+\]\s*")

# BibTeX 类型 → CSL type。非标准类型（collection/standard/map…）按 spike
# 实测的 pandoc bibtex 语义映射（REPORT §2：collection→book、
# standard→legislation、map 不识别→兜底 [Z]）。
_ENTRY_TYPE_TO_CSL: dict[str, str] = {
    "article": "article-journal",
    "book": "book",
    "incollection": "chapter",
    "inproceedings": "paper-conference",
    "collection": "book",
    "mastersthesis": "thesis",
    "phdthesis": "thesis",
    "techreport": "report",
    "standard": "legislation",
    "patent": "patent",
    "online": "webpage",
    "electronic": "webpage",
    "dataset": "dataset",
    "map": "map",
    "unpublished": "manuscript",
}


class PandocCiteprocUnavailableError(BibliographyError):
    """在 provider 不可用时调用其渲染方法（调用方应先看 info()）。"""

    def __init__(self, diagnostics: tuple[str, ...]):
        self.diagnostics = tuple(diagnostics)
        detail = "；".join(diagnostics) if diagnostics else "原因未知"
        super().__init__(f"pandoc citeproc provider 不可用：{detail}")


def _default_csl_path() -> Path:
    # src/docforge/bibliography/pandoc_provider.py → 仓库根（4 级）
    return Path(__file__).resolve().parents[3] / _DEFAULT_CSL_RELPATH


def _name_to_csl(name: str) -> dict[str, str] | None:
    """BibTeX 姓名串 → CSL name 对象，跟随 pandoc bibtex 语义。

    含逗号 → ``Family, Given``；无逗号 → 末词为 family；单词名按 literal。
    """

    name = " ".join(name.split())
    if not name:
        return None
    if "," in name:
        family, _, given = name.partition(",")
        item: dict[str, str] = {"family": family.strip()}
        if given.strip():
            item["given"] = given.strip()
        return item
    parts = name.split()
    if len(parts) == 1:
        return {"literal": name}
    return {"family": parts[-1], "given": " ".join(parts[:-1])}


def _names_to_csl(names: tuple[str, ...]) -> list[dict[str, str]] | None:
    items = [item for name in names if (item := _name_to_csl(name)) is not None]
    return items or None


def _date_parts(value: str) -> list[int] | None:
    parts: list[int] = []
    for chunk in value.strip().split("-"):
        try:
            parts.append(int(chunk))
        except ValueError:
            return None
    return parts or None


def record_to_csl_item(record: BibliographyRecord) -> dict[str, Any]:
    """BibliographyRecord → CSL JSON item（纯函数，离线可测）。"""

    item: dict[str, Any] = {
        "id": record.key,
        "type": _ENTRY_TYPE_TO_CSL.get(record.entry_type, "entry"),
    }
    if record.authors:
        item["author"] = _names_to_csl(record.authors)
    if record.title:
        item["title"] = record.title
    if record.journal:
        item["container-title"] = record.journal
    elif record.booktitle:
        item["container-title"] = record.booktitle
    if record.publisher:
        item["publisher"] = record.publisher
    if record.school:
        # CSL thesis/report 的机构落在 publisher
        item.setdefault("publisher", record.school)
    if record.address:
        item["publisher-place"] = record.address
    if record.volume:
        item["volume"] = record.volume
    if record.number:
        csl_type = item["type"]
        # article-journal 的 BibTeX number 是期号 → issue；legislation/patent
        # 等类型的 number 是标准号/专利号，CSL 字段同名 number（spike 实证：
        # standard 的 "：GB/T 7714-2015" 由 number 渲染）。
        item["issue" if csl_type == "article-journal" else "number"] = record.number
    if record.pages:
        item["page"] = record.pages.replace("--", "–")
    issued = _date_parts(record.date) if record.date else None
    if issued is None and record.year:
        issued = _date_parts(record.year)
    if issued is not None:
        item["issued"] = {"date-parts": [issued]}
    if record.urldate:
        accessed = _date_parts(record.urldate)
        if accessed is not None:
            item["accessed"] = {"date-parts": [accessed]}
    if record.url:
        item["URL"] = record.url
    if record.doi:
        item["DOI"] = record.doi
    if record.edition:
        item["edition"] = record.edition
    if record.translators:
        item["translator"] = _names_to_csl(record.translators)
    if record.editors:
        item["editor"] = _names_to_csl(record.editors)
    if record.entrysubtype:
        item["genre"] = record.entrysubtype
    if record.language:
        item["language"] = record.language
    if record.note:
        item["note"] = record.note
    return item


class _RefsHTMLParser(HTMLParser):
    """收集 ``<div id="ref-KEY" class="csl-entry">`` 的文本（spike 同构）。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: dict[str, str] = {}
        self._key: str | None = None
        self._depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "div":
            return
        if self._key is not None:
            self._depth += 1
            return
        entry_id = dict(attrs).get("id") or ""
        if entry_id.startswith("ref-"):
            self._key = entry_id[4:]
            self._depth = 1
            self._chunks = []

    def handle_endtag(self, tag: str) -> None:
        if tag != "div" or self._key is None:
            return
        self._depth -= 1
        if self._depth == 0:
            text = " ".join("".join(self._chunks).split())
            self.entries[self._key] = _ORDINAL_PREFIX_RE.sub("", text)
            self._key = None

    def handle_data(self, data: str) -> None:
        if self._key is not None:
            self._chunks.append(data)


class PandocCiteprocProvider:
    """可选外部 provider：pandoc ``--citeproc`` + 官方 GB/T 2025 CSL。"""

    def __init__(
        self,
        *,
        executable: str = "pandoc",
        csl_path: str | Path | None = None,
        timeout: float = 60.0,
        marker_formatter: Gbt7714Formatter | None = None,
    ):
        self._executable = executable
        self._csl_path = (
            Path(csl_path).expanduser() if csl_path is not None else _default_csl_path()
        )
        self._timeout = timeout
        self._marker_formatter = marker_formatter or Gbt7714Formatter()

    # -- CitationProvider 协议 -------------------------------------------

    def info(self) -> ProviderInfo:
        diagnostics: list[str] = []
        version = probe_executable_version(self._executable)
        if version is None:
            diagnostics.append(
                f"未找到可执行文件 {self._executable!r}：pandoc 不随包分发，"
                "请自行安装（https://pandoc.org）后重试"
            )
        csl_ok = False
        if self._csl_path.is_file():
            digest = hashlib.sha256(self._csl_path.read_bytes()).hexdigest()
            if digest == GB_T_2025_CSL_SHA256:
                csl_ok = True
            else:
                diagnostics.append(
                    f"CSL 副本哈希与 ADR-0004 §2.5 记录不符：{self._csl_path}"
                    f"（sha256 {digest[:12]}…，期望 {GB_T_2025_CSL_SHA256[:12]}…）"
                )
        else:
            diagnostics.append(
                f"官方 GB/T 7714-2025 numeric CSL 副本不存在：{self._csl_path}"
                "（运行时副本位于 spikes 语料目录；模板包内置后改由包提供）"
            )
        return ProviderInfo(
            name=PANDOC_PROVIDER_NAME,
            styles=(DEFAULT_CITATION_STYLE,),
            version=version,
            available=version is not None and csl_ok,
            diagnostics=tuple(diagnostics),
        )

    def format_citation(
        self,
        records: list[BibliographyRecord] | tuple[BibliographyRecord, ...],
        ordinals: list[int] | tuple[int, ...],
        *,
        locator: str | None = None,
    ) -> str:
        # 编译器权威编号的正文标记不外委（模块注释）；与内建引擎逐字节一致。
        return self._marker_formatter.format_citation(
            records, ordinals, locator=locator
        )

    def format_bibliography(
        self,
        records: list[BibliographyRecord] | tuple[BibliographyRecord, ...],
        ordinals: list[int] | tuple[int, ...],
    ) -> tuple[str, ...]:
        info = self.info()
        if not info.available:
            raise PandocCiteprocUnavailableError(info.diagnostics)
        rendered = self._render_entries(records)
        missing = [record.key for record in records if record.key not in rendered]
        if missing:
            raise BibliographyError(
                f"pandoc citeproc 未渲染以下条目：{', '.join(missing)}"
            )
        return tuple(
            f"[{ordinal}] {rendered[record.key]}"
            for record, ordinal in zip(records, ordinals, strict=True)
        )

    # -- 内部 ------------------------------------------------------------

    def _render_entries(
        self, records: list[BibliographyRecord] | tuple[BibliographyRecord, ...]
    ) -> dict[str, str]:
        items = [record_to_csl_item(record) for record in records]
        with tempfile.TemporaryDirectory(prefix="tf-pandoc-cite-") as tmp:
            work = Path(tmp)
            bib_path = work / "bibliography.json"
            bib_path.write_text(
                json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            markdown = work / "input.md"
            markdown.write_text(
                "---\n"
                "title: bibliography\n"
                f"bibliography: {bib_path}\n"
                f"csl: {self._csl_path}\n"
                "nocite: |\n"
                "  @*\n"
                "---\n\nBody.\n",
                encoding="utf-8",
            )
            try:
                completed = subprocess.run(
                    [self._executable, "--citeproc", str(markdown), "-t", "html"],
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise BibliographyError(
                    f"pandoc citeproc 超时（>{self._timeout}s）"
                ) from error
            except OSError as error:
                raise PandocCiteprocUnavailableError(
                    (f"无法启动 {self._executable!r}：{error}",)
                ) from error
        if completed.returncode != 0:
            raise BibliographyError(
                f"pandoc citeproc 失败（exit {completed.returncode}）："
                f"{completed.stderr.strip()[:400]}"
            )
        parser = _RefsHTMLParser()
        parser.feed(completed.stdout)
        return parser.entries
