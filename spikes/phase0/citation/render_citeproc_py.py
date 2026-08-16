"""Render the GB/T 7714 corpus with citeproc-py.

Primary path: the corpus BibTeX is converted to CSL JSON by pandoc
(`pandoc -f bibtex -t csljson`) so that both CSL engines see identical
input data; the JSON is rendered with citeproc-py + the same CSL style.

Secondary path (diagnostic): citeproc-py's own BibTeX source is tried as
well, to document its field/type coverage. Writes results/citeproc_py.json.
"""

from __future__ import annotations

import hashlib
import html
import importlib.metadata
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIB_PATH = ROOT / "corpus" / "gbt7714-corpus.bib"
CSL_PATH = ROOT / "corpus" / "china-national-standard-gb-t-7714-2025-numeric.csl"
CSL_JSON_PATH = ROOT / "corpus" / "gbt7714-corpus.csl.json"
OUT_PATH = ROOT / "results" / "citeproc_py.json"

ORDINAL_RE = re.compile(r"^\[(\d+)\]\s*(.*)$", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain_text(rendered: str) -> str:
    return " ".join(html.unescape(TAG_RE.sub("", rendered)).split())


def ensure_csl_json() -> list[dict]:
    """Convert the corpus .bib to CSL JSON with pandoc (same input for both engines)."""
    proc = subprocess.run(
        ["pandoc", "-f", "bibtex", "-t", "csljson", str(BIB_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc bib->csljson failed: {proc.stderr.strip()}")
    CSL_JSON_PATH.write_text(proc.stdout, encoding="utf-8")
    return json.loads(proc.stdout)


def render_with_csl_json(items: list[dict]) -> tuple[list[dict], list[dict], list[str]]:
    from citeproc import (
        Citation,
        CitationItem,
        CitationStylesBibliography,
        CitationStylesStyle,
        formatter,
    )
    from citeproc.source.json import CiteProcJSON

    source = CiteProcJSON(items)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        style = CitationStylesStyle(str(CSL_PATH), validate=False)
        bibliography = CitationStylesBibliography(style, source, formatter.html)
        keys = [str(item["id"]) for item in items]
        for key in keys:
            bibliography.register(Citation([CitationItem(key)]))
        rendered = [plain_text(str(entry)) for entry in bibliography.bibliography()]
    warning_texts = sorted({str(w.message) for w in caught})

    entries: list[dict] = []
    failures: list[dict] = []
    if len(rendered) != len(keys):
        failures.append(
            {
                "key": "*",
                "error": f"bibliography size mismatch: {len(rendered)} rendered "
                f"vs {len(keys)} registered; key alignment may be off",
            }
        )
    for key, text in zip(keys, rendered, strict=False):
        match = ORDINAL_RE.match(text)
        if match is None:
            failures.append({"key": key, "error": f"no [n] ordinal prefix: {text[:60]}"})
            continue
        entries.append(
            {"key": key, "ordinal": int(match.group(1)), "text": match.group(2).strip()}
        )
    return entries, failures, warning_texts


def render_with_native_bibtex() -> dict:
    """Diagnostic: citeproc-py's own BibTeX frontend (expected to lose fields)."""
    from citeproc import (
        Citation,
        CitationItem,
        CitationStylesBibliography,
        CitationStylesStyle,
        formatter,
    )
    from citeproc.source.bibtex import BibTeX

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            source = BibTeX(str(BIB_PATH), encoding="utf-8")
            style = CitationStylesStyle(str(CSL_PATH), validate=False)
            bibliography = CitationStylesBibliography(style, source, formatter.html)
            keys = [ref.key for ref in source]
            for key in keys:
                bibliography.register(Citation([CitationItem(key)]))
            rendered = [plain_text(str(entry)) for entry in bibliography.bibliography()]
        return {
            "status": "ok",
            "entries_rendered": len(rendered),
            "warnings": sorted({str(w.message) for w in caught}),
        }
    except Exception as error:  # noqa: BLE001 - diagnostic path records any failure
        return {"status": "failed", "error": f"{type(error).__name__}: {error}"}


def main() -> int:
    items = ensure_csl_json()
    entries, failures, warning_texts = render_with_csl_json(items)
    native = render_with_native_bibtex()

    payload = {
        "engine": "citeproc-py",
        "engine_version": importlib.metadata.version("citeproc-py"),
        "csl_file": CSL_PATH.name,
        "csl_sha256": sha256_of(CSL_PATH),
        "input": "CSL JSON converted from gbt7714-corpus.bib via pandoc -f bibtex -t csljson",
        "entries": entries,
        "failures": failures,
        "csl_parse_warnings": warning_texts,
        "native_bibtex_source_diagnostic": native,
    }
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"citeproc-py: rendered {len(entries)} entries, {len(failures)} failures")
    print(f"native bibtex diagnostic: {native['status']}")
    print(f"written: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
