#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x .venv/bin/python ]]; then
    PYTHON=.venv/bin/python
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  else
    echo "LOOP-LINT: FAIL — no Python interpreter found" >&2
    exit 1
  fi
fi

"$PYTHON" - <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path("LOOP.md")
if not path.is_file():
    raise SystemExit("LOOP-LINT: FAIL — LOOP.md is missing")

text = path.read_text(encoding="utf-8")
errors: list[str] = []

required_headers = [
    "## Rules",
    "## Discovery",
    "## Open",
    "## Done",
    "## Blocked",
    "## Cycle log",
    "## Sync log",
]
for header in required_headers:
    count = len(re.findall(rf"^{re.escape(header)}\s*$", text, re.MULTILINE))
    if count != 1:
        errors.append(f"{header!r} must occur exactly once as a section heading")

status_match = re.search(r"^\*\*Status:\*\*\s*(\S+)\s*$", text, re.MULTILINE)
if not status_match:
    errors.append("missing **Status:** field")
else:
    status = status_match.group(1)
    if status not in {"active", "paused", "blocked", "done"}:
        errors.append(f"unsupported Status value: {status}")

for field in ("Goal", "Stop condition", "Verification surface", "Human gate", "Bounds"):
    if not re.search(rf"^\*\*{re.escape(field)}:\*\*\s*\S", text, re.MULTILINE):
        errors.append(f"missing or empty **{field}:** field")

section_pattern = re.compile(r"^## ([^\n]+)\n", re.MULTILINE)
sections: dict[str, str] = {}
matches = list(section_pattern.finditer(text))
for index, match in enumerate(matches):
    start = match.end()
    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
    sections[match.group(1).strip()] = text[start:end]

item_header = re.compile(r"^- \[([A-Za-z0-9_-]+)\]\s+(.+)$", re.MULTILINE)
ids: dict[str, str] = {}

for section_name in ("Open", "Done", "Blocked"):
    body = sections.get(section_name, "")
    matches = list(item_header.finditer(body))
    for index, match in enumerate(matches):
        item_id = match.group(1)
        if item_id in ids:
            errors.append(f"duplicate item ID {item_id!r} in {section_name} and {ids[item_id]}")
        ids[item_id] = section_name
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        block = body[block_start:block_end]

        if section_name == "Open":
            files_line = re.search(r"^\s{2}- Files:\s*(.+)$", block, re.MULTILINE)
            behavior = re.search(r"^\s{2}- Behavior:\s*\S", block, re.MULTILINE)
            verify = re.search(r"^\s{2}- Verify:\s*`([^`]+)`\s*$", block, re.MULTILINE)
            acceptance = re.search(r"^\s{2}- Acceptance:\s*\S", block, re.MULTILINE)
            surface = re.search(
                r"^\s{2}- Verification-surface change:\s*\S", block, re.MULTILINE
            )
            attempts = re.search(r"^\s{2}- Attempts:\s*(\d+)\s*$", block, re.MULTILINE)

            if not files_line:
                errors.append(f"{item_id}: missing Files line")
            else:
                files = re.findall(r"`([^`]+)`", files_line.group(1))
                if not 1 <= len(files) <= 3:
                    errors.append(
                        f"{item_id}: expected 1-3 exact files, found {len(files)}"
                    )
                if len(files) != len(set(files)):
                    errors.append(f"{item_id}: duplicate file entries")
                for file in files:
                    if file.startswith("/") or ".." in Path(file).parts:
                        errors.append(f"{item_id}: unsafe repository path {file!r}")

            if not behavior:
                errors.append(f"{item_id}: missing Behavior")
            if not verify or not verify.group(1).strip():
                errors.append(f"{item_id}: missing executable Verify command")
            if not acceptance:
                errors.append(f"{item_id}: missing Acceptance")
            if not surface:
                errors.append(f"{item_id}: missing Verification-surface change")
            if not attempts:
                errors.append(f"{item_id}: missing integer Attempts")
            elif int(attempts.group(1)) > 3:
                errors.append(f"{item_id}: Attempts exceeds the three-attempt bound")

open_body = sections.get("Open", "")
blocked_body = sections.get("Blocked", "")
if status_match and status_match.group(1) == "done":
    if item_header.search(open_body):
        errors.append("Status is done but Open contains items")
    if item_header.search(blocked_body):
        errors.append("Status is done but Blocked contains items")

if "at most 3 repository files" not in text and "at most three repository files" not in text:
    errors.append("three-file rule is missing")

if errors:
    print("LOOP-LINT: FAIL", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    raise SystemExit(1)

open_count = len(item_header.findall(open_body))
done_count = len(item_header.findall(sections.get("Done", "")))
blocked_count = len(item_header.findall(blocked_body))
print(
    f"LOOP-LINT: PASS — open={open_count} done={done_count} blocked={blocked_count}"
)
PY
