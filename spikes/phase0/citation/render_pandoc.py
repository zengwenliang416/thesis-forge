"""Render the GB/T 7714 corpus with pandoc --citeproc.

Reads corpus/gbt7714-corpus.bib, renders every entry through
pandoc --citeproc with the GB/T 7714-2025 numeric CSL style, and writes
results/pandoc.json. Only stdlib + the pandoc executable are used.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIB_PATH = ROOT / "corpus" / "gbt7714-corpus.bib"
CSL_PATH = ROOT / "corpus" / "china-national-standard-gb-t-7714-2025-numeric.csl"
OUT_PATH = ROOT / "results" / "pandoc.json"
TMP_DIR = ROOT / ".tmp"

ORDINAL_RE = re.compile(r"^\[(\d+)\]\s*(.*)$", re.DOTALL)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pandoc_version() -> str:
    proc = subprocess.run(
        ["pandoc", "--version"], capture_output=True, text=True, check=True
    )
    return proc.stdout.splitlines()[0].strip()


def render_html() -> str:
    TMP_DIR.mkdir(exist_ok=True)
    markdown = TMP_DIR / "render-pandoc-input.md"
    markdown.write_text(
        "---\n"
        "title: corpus\n"
        f"bibliography: {BIB_PATH}\n"
        f"csl: {CSL_PATH}\n"
        "nocite: |\n"
        "  @*\n"
        "---\n\n"
        "Corpus placeholder body.\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["pandoc", "--citeproc", str(markdown), "-t", "html"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc --citeproc failed: {proc.stderr.strip()}")
    return proc.stdout


class _RefsHTMLParser(HTMLParser):
    """Collect text of every <div id="ref-KEY" class="csl-entry"> block."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: dict[str, str] = {}
        self._key: str | None = None
        self._depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "div":
            return
        attr = dict(attrs)
        if self._key is not None:
            self._depth += 1
            return
        entry_id = attr.get("id") or ""
        if entry_id.startswith("ref-"):
            self._key = entry_id[4:]
            self._depth = 1
            self._chunks = []

    def handle_endtag(self, tag: str) -> None:
        if tag != "div" or self._key is None:
            return
        self._depth -= 1
        if self._depth == 0:
            self.entries[self._key] = " ".join("".join(self._chunks).split())
            self._key = None

    def handle_data(self, data: str) -> None:
        if self._key is not None:
            self._chunks.append(data)


def main() -> int:
    html = render_html()
    parser = _RefsHTMLParser()
    parser.feed(html)

    entries = []
    failures = []
    for key, text in parser.entries.items():
        match = ORDINAL_RE.match(text)
        if match is None:
            failures.append({"key": key, "error": f"no [n] ordinal prefix: {text[:60]}"})
            continue
        entries.append(
            {"key": key, "ordinal": int(match.group(1)), "text": match.group(2).strip()}
        )
    entries.sort(key=lambda item: item["ordinal"])

    payload = {
        "engine": "pandoc --citeproc",
        "engine_version": pandoc_version(),
        "csl_file": CSL_PATH.name,
        "csl_sha256": sha256_of(CSL_PATH),
        "entries": entries,
        "failures": failures,
    }
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"pandoc: rendered {len(entries)} entries, {len(failures)} failures")
    print(f"written: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
