#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/references/external"
mkdir -p "$DEST"

clone_if_missing() {
  local url="$1"
  local name="$2"
  if [[ -d "$DEST/$name/.git" ]]; then
    echo "[skip] $name already exists"
  else
    git clone --depth 1 "$url" "$DEST/$name"
  fi
}

clone_if_missing https://github.com/AfishInLake/WordFormat.git WordFormat
clone_if_missing https://github.com/Drenches/gov-doc-formatter.git gov-doc-formatter
clone_if_missing https://github.com/wzbwan/gongwen-format-skill.git gongwen-format-skill
clone_if_missing https://github.com/xkonglong/gw.git gw
clone_if_missing https://github.com/python-openxml/python-docx.git python-docx
clone_if_missing https://github.com/jgm/pandoc.git pandoc
clone_if_missing https://github.com/citeproc-py/citeproc-py.git citeproc-py
clone_if_missing https://github.com/citation-style-language/styles.git csl-styles
clone_if_missing https://github.com/zhiyiYo/PyQt-Fluent-Widgets.git PyQt-Fluent-Widgets

echo "Reference repositories are in: $DEST"
echo "Do not commit this directory."
