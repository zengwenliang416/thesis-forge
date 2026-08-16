"""Render the GB/T 7714 corpus with ThesisForge's handwritten Gbt7714Formatter.

Each @entry of corpus/gbt7714-corpus.bib is loaded individually through the
project's LocalBibTeXLoader (src/ layout, imported via sys.path). Entry types
outside the handwritten formatter's five supported types, and entries missing
required fields, are recorded as failures with the loader's own error message.
Writes results/thesisforge.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIB_PATH = ROOT / "corpus" / "gbt7714-corpus.bib"
OUT_PATH = ROOT / "results" / "thesisforge.json"
TMP_DIR = ROOT / ".tmp"
PROJECT_SRC = ROOT.parents[2] / "src"

if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

ENTRY_START_RE = re.compile(r"@([A-Za-z]+)\s*\{")


def iter_bib_entries(text: str) -> list[str]:
    """Split a .bib file into raw @entry{...} chunks (brace-balanced)."""
    chunks = []
    for match in ENTRY_START_RE.finditer(text):
        index = match.end()
        depth = 1
        in_quote = False
        while index < len(text) and depth > 0:
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_quote = not in_quote
            elif not in_quote:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
            index += 1
        chunks.append(text[match.start() : index])
    return chunks


def main() -> int:
    from thesis_forge.bibliography.bibtex import LocalBibTeXLoader
    from thesis_forge.bibliography.formatter import Gbt7714Formatter

    TMP_DIR.mkdir(exist_ok=True)
    loader = LocalBibTeXLoader()
    formatter = Gbt7714Formatter()

    text = BIB_PATH.read_text(encoding="utf-8")
    entries: list[dict] = []
    failures: list[dict] = []

    for chunk in iter_bib_entries(text):
        probe = TMP_DIR / "thesisforge-single-entry.bib"
        probe.write_text(chunk + "\n", encoding="utf-8")
        key = ENTRY_START_RE.match(chunk) and chunk.split("{", 1)[1].split(",", 1)[0].strip()
        try:
            database = loader.load(probe)
            record = next(iter(database.records.values()))
            key = record.key
            ordinal = len(entries) + 1
            (rendered,) = formatter.format_bibliography([record], [ordinal])
            entries.append(
                {
                    "key": record.key,
                    "ordinal": ordinal,
                    "entry_type": record.entry_type,
                    "text": rendered.removeprefix(f"[{ordinal}] "),
                }
            )
        except Exception as error:  # noqa: BLE001 - per-entry isolation is the point
            failures.append(
                {"key": str(key), "error": f"{type(error).__name__}: {error}"}
            )

    payload = {
        "engine": "thesisforge Gbt7714Formatter (handwritten)",
        "engine_version": "thesis_forge 0.1.0 (src checkout)",
        "entries": entries,
        "failures": failures,
        "note": "ordinals are assigned over the supported subset only, in .bib order",
    }
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"thesisforge: rendered {len(entries)} entries, {len(failures)} failures")
    print(f"written: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
