from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

ReplaceFile = Callable[[Path, Path], None]


@contextmanager
def temporary_output_path(target: str | Path) -> Iterator[Path]:
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.",
        suffix=".tmp.docx",
        dir=target_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        yield temporary_path
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def replace_output(
    temporary_path: Path,
    target_path: Path,
    *,
    replace_file: ReplaceFile = os.replace,
) -> None:
    replace_file(temporary_path, target_path)
