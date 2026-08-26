from __future__ import annotations

import errno
import os
import shutil
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
    try:
        replace_file(temporary_path, target_path)
        return
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise

    descriptor, staged_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.",
        suffix=".tmp",
        dir=target_path.parent,
    )
    os.close(descriptor)
    staged_path = Path(staged_name)
    try:
        shutil.copyfile(temporary_path, staged_path)
        replace_file(staged_path, target_path)
    finally:
        try:
            staged_path.unlink()
        except FileNotFoundError:
            pass
