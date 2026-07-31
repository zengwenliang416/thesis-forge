from __future__ import annotations

import re
from collections.abc import Collection

REFERENCABLE_ID_PREFIXES = frozenset({"chap", "sec", "fig", "tbl", "eq", "alg", "lst"})
STABLE_ID_RE = re.compile(r"^(?P<prefix>[a-z][a-z0-9_-]*):(?P<name>[A-Za-z0-9][A-Za-z0-9_.:-]*)$")


def split_stable_id(value: str) -> tuple[str, str] | None:
    match = STABLE_ID_RE.fullmatch(value)
    if match is None:
        return None
    return match.group("prefix"), match.group("name")


def is_valid_stable_id(
    value: str,
    allowed_prefixes: Collection[str] = REFERENCABLE_ID_PREFIXES,
) -> bool:
    parts = split_stable_id(value)
    return parts is not None and parts[0] in allowed_prefixes
