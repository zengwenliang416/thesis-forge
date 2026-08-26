from __future__ import annotations

import os
import stat
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ReplaceFile = Callable[[Path, Path], None]


@dataclass(frozen=True, slots=True)
class LocalWorkspaceFileSystem:
    replace_file: ReplaceFile = os.replace

    def read_text(self, path: Path) -> str:
        with Path(path).open("r", encoding="utf-8", newline="") as source:
            return source.read()

    def write_text_atomic(self, path: Path, text: str) -> None:
        target = Path(path)
        existing_mode = (
            stat.S_IMODE(target.stat().st_mode)
            if target.exists()
            else None
        )
        descriptor = -1
        temporary_path: Path | None = None

        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.",
                suffix=".tmp",
                dir=target.parent,
            )
            temporary_path = Path(temporary_name)
            stream = os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
                newline="",
            )
            descriptor = -1
            with stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            if existing_mode is not None:
                temporary_path.chmod(existing_mode)
            self.replace_file(temporary_path, target)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
