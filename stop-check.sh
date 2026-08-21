#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

fail() {
  printf 'STOP-CHECK: FAIL — %s\n' "$1" >&2
  exit 1
}

[[ -f LOOP.md ]] || fail "LOOP.md is missing"
[[ -x ./lint-loop.sh ]] || fail "lint-loop.sh is missing or not executable"
./lint-loop.sh

section_items() {
  local section="$1"
  awk -v target="$section" '
    $0 == "## " target { inside=1; next }
    /^## / { if (inside) exit }
    inside && /^[[:space:]]*-[[:space:]]*\[[^]]+\]/ { print }
  ' LOOP.md
}

OPEN_ITEMS="$(section_items Open)"
BLOCKED_ITEMS="$(section_items Blocked)"

if [[ -n "$OPEN_ITEMS" ]]; then
  printf '%s\n' "$OPEN_ITEMS" >&2
  fail "LOOP.md still contains Open items"
fi

if [[ -n "$BLOCKED_ITEMS" ]]; then
  printf '%s\n' "$BLOCKED_ITEMS" >&2
  fail "LOOP.md still contains Blocked items"
fi

[[ -f scripts/verify_thesisforge_v2_goal.py ]] \
  || fail "scripts/verify_thesisforge_v2_goal.py is missing"

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x .venv/bin/python ]]; then
    PYTHON=.venv/bin/python
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  else
    fail "no Python interpreter found"
  fi
fi

"$PYTHON" scripts/verify_thesisforge_v2_goal.py

FULL_VERIFY_CMD="${FULL_VERIFY_CMD:-make verify}"
printf 'STOP-CHECK: running %s\n' "$FULL_VERIFY_CMD"
bash -lc "$FULL_VERIFY_CMD"

printf 'STOP-CHECK: PASS — Goal behavior and full repository verification are green.\n'
