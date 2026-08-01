from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, TypeVar

from .models import WebSourceHandle

ResultT = TypeVar("ResultT")


class TaskRunner(Protocol):
    def submit(
        self,
        operation: Callable[[], ResultT],
        *,
        on_success: Callable[[ResultT], None],
        on_error: Callable[[Exception], None],
    ) -> None: ...


class SynchronousTaskRunner:
    def submit(
        self,
        operation: Callable[[], ResultT],
        *,
        on_success: Callable[[ResultT], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        try:
            result = operation()
        except Exception as error:  # noqa: BLE001 - task failures cross this boundary
            on_error(error)
            return
        on_success(result)


class WorkspaceFileSystem(Protocol):
    def read_text(self, path: Path) -> str: ...

    def write_text_atomic(self, path: Path, text: str) -> None: ...


class WebWorkspacePersistence(Protocol):
    def save_workspace(
        self,
        handle: WebSourceHandle,
        source_path: Path,
        text: str,
    ) -> Path: ...

    def download(
        self,
        handle: WebSourceHandle,
        source_path: Path,
        text: str,
    ) -> Path: ...
