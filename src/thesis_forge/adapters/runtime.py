from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from thesis_forge.application import (
    ApplicationStageError,
    BuildResult,
    InspectionResult,
    ValidationResult,
    build_service,
    inspect_service,
    validation_service,
)
from thesis_forge.core.model import Heading
from thesis_forge.ui.filesystem import LocalWorkspaceFileSystem

from .dto import PROTOCOL_VERSION, error_response, success_response

InspectService = Callable[..., InspectionResult]
ValidationService = Callable[..., ValidationResult]
BuildService = Callable[..., BuildResult]


class RuntimePaths(Protocol):
    def source_path(self, source: dict) -> Path: ...

    def output_path(self, output: dict) -> Path: ...

    def save_source(self, source: dict, text: str) -> Path: ...

    def present_source(self, source: dict, path: Path) -> dict: ...

    def present_output(self, output: dict, path: Path) -> dict: ...


class DesktopRuntime:
    def __init__(self) -> None:
        self._filesystem = LocalWorkspaceFileSystem()

    def source_path(self, source: dict) -> Path:
        if source.get("kind") != "desktop" or not source.get("path"):
            raise ValueError("desktop source path is required")
        return Path(source["path"])

    def output_path(self, output: dict) -> Path:
        if output.get("kind") != "desktop" or not output.get("path"):
            raise ValueError("desktop output path is required")
        return Path(output["path"])

    def save_source(self, source: dict, text: str) -> Path:
        path = self.source_path(source)
        self._filesystem.write_text_atomic(path, text)
        return path

    def present_source(self, source: dict, path: Path) -> dict:
        return {"kind": "desktop", "name": source.get("fileName") or path.name}

    def present_output(self, output: dict, path: Path) -> dict:
        return {"kind": "desktop", "name": output.get("fileName") or path.name}


class WebWorkspaceRuntime:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._filesystem = LocalWorkspaceFileSystem()

    @staticmethod
    def _plain_file_name(file_name: object) -> str:
        if (
            not isinstance(file_name, str)
            or not file_name
            or Path(file_name).name != file_name
            or "/" in file_name
            or "\\" in file_name
        ):
            raise ValueError("web workspace fileName must be a plain file name")
        return file_name

    @staticmethod
    def _workspace_id(value: object) -> str:
        if (
            not isinstance(value, str)
            or len(value) != 32
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("invalid web workspace ID")
        return value

    def create_workspace(self, file_name: str, text: str) -> dict:
        safe_name = self._plain_file_name(file_name)
        workspace_id = uuid4().hex
        workspace = self.root / workspace_id
        workspace.mkdir(mode=0o700)
        self._filesystem.write_text_atomic(workspace / safe_name, text)
        return {
            "kind": "web-workspace",
            "workspaceId": workspace_id,
            "fileName": safe_name,
        }

    def source_path(self, source: dict) -> Path:
        if source.get("kind") not in {"web-workspace", "web-upload"}:
            raise ValueError("web workspace source is required")
        workspace_id = self._workspace_id(
            source.get("workspaceId") or source.get("uploadId")
        )
        file_name = self._plain_file_name(source.get("fileName"))
        path = self.root / workspace_id / file_name
        if not path.is_file():
            raise ValueError("web workspace source does not exist")
        return path

    def output_path(self, output: dict) -> Path:
        workspace_id = self._workspace_id(output.get("workspaceId"))
        file_name = self._plain_file_name(output.get("fileName") or "thesis.docx")
        workspace = self.root / workspace_id
        if not workspace.is_dir():
            raise ValueError("web workspace does not exist")
        return workspace / file_name

    def save_source(self, source: dict, text: str) -> Path:
        path = self.source_path(source)
        self._filesystem.write_text_atomic(path, text)
        return path

    def present_source(self, source: dict, path: Path) -> dict:
        return {"kind": source["kind"], "name": source.get("fileName") or path.name}

    def present_output(self, output: dict, path: Path) -> dict:
        return {
            "kind": "web-download",
            "name": output.get("fileName") or path.name,
            "downloadId": output.get("workspaceId"),
        }


class WorkbenchCommandDispatcher:
    def __init__(
        self,
        *,
        runtime: RuntimePaths,
        inspect: InspectService = inspect_service,
        validate: ValidationService = validation_service,
        build: BuildService = build_service,
    ) -> None:
        self._runtime = runtime
        self._inspect = inspect
        self._validate = validate
        self._build = build

    def dispatch(self, request: dict) -> dict:
        request_id = request.get("requestId")
        if not isinstance(request_id, str) or not request_id:
            request_id = "invalid-request"
        if request.get("protocol") != PROTOCOL_VERSION:
            return error_response(
                request_id,
                kind="protocol",
                message="unsupported protocol",
            )
        operation = request.get("operation")
        payload = request.get("payload")
        if not isinstance(payload, dict):
            return error_response(
                request_id,
                kind="request",
                message="payload must be an object",
            )

        try:
            if operation == "inspect":
                return success_response(
                    request_id,
                    self._inspect_result(payload),
                )
            if operation == "validate":
                return success_response(
                    request_id,
                    self._validation_result(payload),
                )
            if operation == "build":
                return success_response(
                    request_id,
                    self._build_result(payload),
                )
            if operation == "save":
                return success_response(
                    request_id,
                    self._save_result(payload),
                )
            return error_response(
                request_id,
                kind="request",
                message=f"unsupported operation: {operation}",
            )
        except ApplicationStageError as error:
            return error_response(
                request_id,
                kind="domain",
                message=str(error),
                stage=error.stage.value,
            )
        except PermissionError as error:
            return error_response(
                request_id,
                kind="permission",
                message=str(error),
            )
        except (KeyError, TypeError, ValueError) as error:
            return error_response(
                request_id,
                kind="request",
                message=str(error),
            )
        except Exception as error:  # noqa: BLE001 - exceptions cross transport boundary
            return error_response(
                request_id,
                kind="transport",
                message=str(error),
            )

    def _source(self, payload: dict) -> tuple[dict, Path]:
        source = payload.get("source")
        if not isinstance(source, dict):
            raise TypeError("source must be an object")
        return source, self._runtime.source_path(source)

    def _inspect_result(self, payload: dict) -> dict:
        source, source_path = self._source(payload)
        result = self._inspect(source_path)
        outline = [
            {
                "id": block.id,
                "level": block.level,
                "text": block.text,
                "line": block.location.line,
            }
            for block in result.document.blocks
            if isinstance(block, Heading)
        ]
        return {
            "source": self._runtime.present_source(source, source_path),
            "metadata": result.document.metadata,
            "outline": outline,
            "blockCount": len(result.document.blocks),
        }

    def _validation_result(self, payload: dict) -> dict:
        source, source_path = self._source(payload)
        result = self._validate(
            source_path,
            template_path=payload.get("templatePath"),
        )
        return {
            "source": self._runtime.present_source(source, source_path),
            "diagnostics": [asdict(issue) for issue in result.issues],
        }

    def _save_result(self, payload: dict) -> dict:
        source = payload.get("source")
        text = payload.get("text")
        if not isinstance(source, dict):
            raise TypeError("source must be an object")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        source_path = self._runtime.save_source(source, text)
        return {
            "source": self._runtime.present_source(source, source_path),
        }

    def _build_result(self, payload: dict) -> dict:
        source, source_path = self._source(payload)
        output = payload.get("output")
        if not isinstance(output, dict):
            raise TypeError("output must be an object")
        output_path = self._runtime.output_path(output)
        stages: list[str] = []
        result = self._build(
            source_path,
            output_path,
            template_path=payload.get("templatePath"),
            on_progress=lambda stage: stages.append(stage.value),
        )
        return {
            "source": self._runtime.present_source(source, source_path),
            "output": self._runtime.present_output(output, result.output_path),
            "diagnostics": [asdict(issue) for issue in result.issues],
            "progress": stages,
        }
