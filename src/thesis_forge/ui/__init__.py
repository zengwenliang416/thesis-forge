from typing import TYPE_CHECKING

from .filesystem import LocalWorkspaceFileSystem
from .models import (
    DiagnosticViewModel,
    OperationKind,
    OperationToken,
    OutputViewModel,
    ProgressViewModel,
    WebSourceHandle,
    WorkspaceActions,
    WorkspaceSourceKind,
    WorkspaceStatus,
    WorkspaceViewModel,
)
from .tasks import (
    SynchronousTaskRunner,
    TaskRunner,
    WebWorkspacePersistence,
    WorkspaceFileSystem,
)

if TYPE_CHECKING:
    from .controller import WorkspaceController


def __getattr__(name: str):
    if name == "WorkspaceController":
        from .controller import WorkspaceController

        return WorkspaceController
    raise AttributeError(name)

__all__ = [
    "DiagnosticViewModel",
    "LocalWorkspaceFileSystem",
    "OperationKind",
    "OperationToken",
    "OutputViewModel",
    "ProgressViewModel",
    "SynchronousTaskRunner",
    "TaskRunner",
    "WebSourceHandle",
    "WebWorkspacePersistence",
    "WorkspaceActions",
    "WorkspaceController",
    "WorkspaceFileSystem",
    "WorkspaceSourceKind",
    "WorkspaceStatus",
    "WorkspaceViewModel",
]
