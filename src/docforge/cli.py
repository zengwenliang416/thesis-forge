from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table as RichTable

from docforge.adapters.dto import serialize_build_report
from docforge.application import (
    ApplicationStageError,
    BuildValidationError,
)
from docforge.application.contracts import (
    BuildDiagnostic,
    BuildIntent,
    BuildOutcome,
    BuildOutput,
    BuildReport,
    ProjectIdentity,
    ProjectOutput,
    ProjectRequest,
    ProjectRequestIntent,
)
from docforge.application.services import ProjectApplicationService
from docforge.core.index import DocumentIndex
from docforge.presentation import localized_issue_message
from docforge.presentation.review import map_review_result
from docforge.presentation.review_markdown import (
    render_review_markdown,
    serialize_review_source_map,
)
from docforge.project.constants import DEFAULT_DOCX_PATH, MANIFEST_FILENAME
from docforge.project.loader import ProjectLoadError, load_project
from docforge.project.paths import ProjectPathError, resolve_project_paths
from docforge.templates import TemplateLoadError
from docforge.templates import v2 as template_v2

app = typer.Typer(help="DocForge — Markdown document compiler")
template_app = typer.Typer(help="Template Package v2 工具（ADR-0002）")
app.add_typer(template_app, name="template")
console = Console(width=160)


def _is_project_input(path: Path) -> bool:
    return path.is_dir() or path.name == MANIFEST_FILENAME


def _project_request(
    source: Path,
    intent: ProjectRequestIntent,
    *,
    output: Path | None = None,
    editor_snapshot: str | None = None,
) -> ProjectRequest:
    project = load_project(source)
    return ProjectRequest(
        project=ProjectIdentity(
            project_id=project.manifest.project.id,
            project_root=project.project_root,
            manifest_path=project.manifest_path,
        ),
        intent=intent,
        output=ProjectOutput(output) if output is not None else None,
        editor_snapshot=editor_snapshot,
    )


def _require_project_input(source: Path) -> None:
    if not _is_project_input(source):
        raise ProjectLoadError(
            "TF-PROJECT-ENTRY-REQUIRED",
            f"a project directory or {MANIFEST_FILENAME} is required",
            path=source,
        )


def _report_project_error(error: ProjectLoadError | ProjectPathError) -> None:
    console.print(f"[red]项目加载失败（{error.code}）：{error}[/red]")
    raise typer.Exit(2) from None


def _report_project_build_error(
    error: BuildValidationError | ApplicationStageError,
    *,
    exit_code: int,
    build_id: str,
    report_json: Path | None = None,
) -> None:
    report = (
        error.to_report(
            build_id=build_id,
            intent=BuildIntent.PUBLISH,
        )
        if isinstance(error, BuildValidationError)
        else BuildReport.from_error(
            error,
            build_id=build_id,
            intent=BuildIntent.PUBLISH,
        )
    )
    message = (
        f"编译停止（{error.stage}）：存在 {len(error.issues)} 个验证错误。"
        "请先运行 validate。"
        if isinstance(error, BuildValidationError)
        else f"构建失败（{error.stage}）：{error}"
    )
    _emit_report({"message": message, "report": serialize_build_report(report)}, report_json)
    raise typer.Exit(exit_code) from None


def _emit_report(payload: dict, report_json: Path | None) -> None:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        default=str,
        indent=2,
        sort_keys=True,
    )
    if report_json is not None:
        report_json = report_json.expanduser().resolve()
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report_json.write_text(serialized + "\n", encoding="utf-8")
    console.print(serialized)


def _project_success_report(project, result) -> BuildReport:
    build_id = f"cli-{project.manifest.project.id}-{result.output_path.name}"
    diagnostics = tuple(
        BuildDiagnostic.from_validation_issue(
            issue,
            sequence=sequence,
            source_file=project.manifest.document.source.root,
        )
        for sequence, issue in enumerate(result.issues, start=1)
    )
    primary = next(
        (
            diagnostic.id
            for diagnostic in diagnostics
            if diagnostic.severity.value == "error"
        ),
        None,
    )
    final_preview = result.final_preview
    return BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id=build_id,
        intent=BuildIntent.PUBLISH,
        outcome=BuildOutcome.SUCCEEDED,
        stages=BuildReport.default_stages(
            failed_stage=None,
            outcome=BuildOutcome.SUCCEEDED,
        ),
        failed_stage=None,
        primary_diagnostic_id=primary,
        diagnostics=diagnostics,
        logs=(),
        output=BuildOutput(
            docx_path=result.output_path,
            pdf_path=final_preview.path if final_preview is not None else None,
            preview_stale=False,
            successful_build_id=build_id,
        ),
    )


def _report_application_error(error: ApplicationStageError, *, source: Path) -> None:
    if error.stage == "parse":
        if isinstance(error.cause, OSError):
            detail = error.cause.strerror or str(error.cause)
            console.print(f"[red]读取失败：{source}：{detail}[/red]")
        else:
            console.print(f"[red]解析失败：{error}[/red]")
    else:
        console.print(f"[red]处理失败（{error.stage}）：{error}[/red]")
    raise typer.Exit(2) from None


def _report_review_error(
    error: ProjectLoadError | ProjectPathError | ApplicationStageError | OSError,
) -> None:
    if isinstance(error, (ProjectLoadError, ProjectPathError)):
        code = error.code
    elif isinstance(error, ApplicationStageError):
        code = f"TF-REVIEW-{error.stage.upper()}"
    else:
        code = "TF-REVIEW-OUTPUT-WRITE"
    payload = {
        "error": {
            "code": code,
            "message": str(error),
        }
    }
    if getattr(error, "path", None) is not None:
        payload["error"]["path"] = str(error.path)
    console.print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        markup=False,
        soft_wrap=True,
    )
    raise typer.Exit(2) from None


@app.command()
def inspect(source: Path) -> None:
    """解析 Markdown 并输出结构。"""
    try:
        _require_project_input(source)
        doc = ProjectApplicationService().inspect(
            _project_request(source, ProjectRequestIntent.INSPECT)
        ).document
    except (ProjectLoadError, ProjectPathError) as error:
        _report_project_error(error)
    except ApplicationStageError as error:
        _report_application_error(error, source=source)
    index = DocumentIndex.from_document(doc)
    data = {
        "source": str(doc.source_path),
        "metadata": doc.metadata,
        "bibliography": asdict(doc.bibliography) if doc.bibliography else None,
        "blocks": [
            {"kind": block.__class__.__name__, **asdict(block)} for block in doc.blocks
        ],
        "inline_content": [
            {"kind": inline.__class__.__name__, **asdict(inline)}
            for inline in index.inlines
        ],
        "cross_references": [asdict(reference) for reference in index.cross_references],
        "citations": [asdict(citation) for citation in index.citations],
        "footnote_references": [asdict(reference) for reference in index.footnote_references],
    }
    console.print_json(json.dumps(data, ensure_ascii=False, default=str))


@app.command()
def validate(
    source: Path,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="以 JSON 输出结构化诊断"),
    ] = False,
) -> None:
    """检查结构和引用问题。"""
    try:
        _require_project_input(source)
        result = ProjectApplicationService().validate(
            _project_request(source, ProjectRequestIntent.VALIDATE)
        )
    except (ProjectLoadError, ProjectPathError) as error:
        _report_project_error(error)
    except ApplicationStageError as error:
        _report_application_error(error, source=source)
    issues = result.issues

    if json_output:
        console.print_json(
            json.dumps(
                {"issues": [asdict(issue) for issue in issues]},
                ensure_ascii=False,
                default=str,
            )
        )
        if any(issue.severity == "error" for issue in issues):
            raise typer.Exit(1)
        raise typer.Exit(0)

    if not issues:
        console.print("[green]✓ 未发现结构性问题[/green]")
        raise typer.Exit(0)

    table = RichTable()
    table.add_column("Severity", no_wrap=True)
    table.add_column("Code", no_wrap=True)
    table.add_column("Line", no_wrap=True)
    table.add_column("Target", overflow="fold")
    table.add_column("Message", overflow="fold")
    for issue in issues:
        table.add_row(
            issue.severity,
            issue.code,
            str(issue.line or ""),
            issue.target or "",
            localized_issue_message(issue),
        )
    console.print(table)

    if any(i.severity == "error" for i in issues):
        raise typer.Exit(1)


@app.command()
def review(
    source: Path,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Review 导出目录"),
    ] = None,
) -> None:
    """生成 reader-facing Review Markdown 和 source map。"""
    try:
        _require_project_input(source)
        project = load_project(source)
        request = ProjectRequest(
            project=ProjectIdentity(
                project_id=project.manifest.project.id,
                project_root=project.project_root,
                manifest_path=project.manifest_path,
            ),
            intent=ProjectRequestIntent.REVIEW,
        )
        preview = ProjectApplicationService().preview(request)
        review_document = map_review_result(preview)
        rendered = render_review_markdown(
            review_document,
            source_name=project.manifest.document.source.root,
        )
        source_map = serialize_review_source_map(rendered)

        if output_dir is None:
            paths = resolve_project_paths(project)
            markdown_path = paths.review_markdown
            source_map_path = paths.source_map
        else:
            output_root = output_dir.expanduser().resolve()
            markdown_path = (
                output_root / project.manifest.review.markdown.root
            ).resolve()
            source_map_path = (
                output_root / project.manifest.review.source_map.root
            ).resolve()
        if markdown_path == source_map_path:
            raise ValueError("Review Markdown and source map output paths must differ")
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        source_map_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(rendered.markdown, encoding="utf-8")
        source_map_path.write_text(source_map, encoding="utf-8")
    except (ProjectLoadError, ProjectPathError, ApplicationStageError) as error:
        _report_review_error(error)
    except (OSError, ValueError) as error:
        _report_review_error(error)

    console.print(
        json.dumps(
            {
                "status": review_document.status,
                "markdown": str(markdown_path),
                "sourceMap": str(source_map_path),
                "issues": [asdict(issue) for issue in review_document.issues],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        markup=False,
        soft_wrap=True,
    )
    if review_document.status == "blocked":
        raise typer.Exit(1)


@app.command()
def build(
    source: Path,
    output: Annotated[
        Path,
        typer.Option("-o", "--output"),
    ] = Path(DEFAULT_DOCX_PATH),
    report_json: Annotated[
        Path | None,
        typer.Option("--report-json", help="写入完整 BuildReport JSON"),
    ] = None,
) -> None:
    """通过安全的本地编译流水线生成 DOCX。"""
    project_input = _is_project_input(source)
    report_build_id = "cli-failure"
    try:
        _require_project_input(source)
        project = load_project(source)
        paths = resolve_project_paths(project)
        output_path = (
            paths.docx
            if output == Path(DEFAULT_DOCX_PATH)
            else (
                output
                if output.is_absolute()
                else (project.project_root / output).resolve()
            )
        )
        report_build_id = f"cli-{project.manifest.project.id}-{output_path.name}"
        result = ProjectApplicationService().build(
            _project_request(
                source,
                ProjectRequestIntent.BUILD,
                output=output_path,
            )
        )
    except (ProjectLoadError, ProjectPathError) as error:
        _report_project_error(error)
    except BuildValidationError as error:
        if project_input:
            _report_project_build_error(
                error,
                exit_code=1,
                build_id=report_build_id,
                report_json=report_json,
            )
        error_count = sum(issue.severity == "error" for issue in error.issues)
        console.print(
            f"[red]编译停止（{error.stage}）：存在 {error_count} 个错误。"
            "请先运行 validate。[/red]"
        )
        raise typer.Exit(1)
    except ApplicationStageError as error:
        if project_input:
            _report_project_build_error(
                error,
                exit_code=2,
                build_id=report_build_id,
                report_json=report_json,
            )
        console.print(f"[red]构建失败（{error.stage}）：{error}[/red]")
        raise typer.Exit(2) from None

    if project_input and report_json is not None:
        _emit_report(
            {
                "message": f"已生成 DOCX：{result.output_path}",
                "report": serialize_build_report(_project_success_report(project, result)),
            },
            report_json,
        )
    else:
        console.print(f"[green]✓ 已生成 DOCX：{result.output_path}[/green]")


def _print_template_issues(issues) -> None:
    table = RichTable()
    table.add_column("Severity", no_wrap=True)
    table.add_column("Code", no_wrap=True)
    table.add_column("Target", overflow="fold")
    table.add_column("Message", overflow="fold")
    for issue in issues:
        table.add_row(
            issue.severity,
            issue.code,
            issue.target or "",
            issue.message,
        )
    console.print(table)


@template_app.command("lint")
def template_lint(
    path: Path,
    level: Annotated[
        str | None,
        typer.Option("--level", help="只运行指定层：L1 / L2 / L3 / L4 / L5"),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="以 JSON 输出结构化诊断"),
    ] = False,
) -> None:
    """对 Template Package v2 目录执行 L1–L5 静态检查。"""
    if not path.is_dir():
        console.print(f"[red]读取失败：模板包目录不存在：{path}[/red]")
        raise typer.Exit(2)
    try:
        report = template_v2.lint_package(
            path, level=level.upper() if level else None
        )
    except ValueError as error:
        console.print(f"[red]参数错误：{error}[/red]")
        raise typer.Exit(2) from None

    if json_output:
        payload = {
            "path": str(report.path),
            "levels_run": list(report.levels_run),
            "issues": [asdict(issue) for issue in report.issues],
            "errors": report.errors,
            "warnings": report.warnings,
        }
        console.print_json(json.dumps(payload, ensure_ascii=False, default=str))
    elif not report.issues:
        console.print("[green]✓ 模板包检查通过[/green]")
    else:
        _print_template_issues(report.issues)

    if report.has_errors:
        raise typer.Exit(1)


@template_app.command("inspect")
def template_inspect(
    path: Path,
    resolved: Annotated[
        bool,
        typer.Option("--resolved", help="输出继承合并后的完整 template.yaml 与字段来源"),
    ] = False,
) -> None:
    """加载 Template Package v2 并输出结构与继承链（JSON，同 inspect 惯例）。"""
    if not path.is_dir():
        console.print(f"[red]读取失败：模板包目录不存在：{path}[/red]")
        raise typer.Exit(2)
    try:
        package = template_v2.load_package(path)
    except template_v2.PackageLoadError as error:
        console.print(f"[red]模板包加载失败：{error.path}[/red]")
        _print_template_issues(error.issues)
        raise typer.Exit(2) from None

    template = package.template
    payload = {
        "path": str(package.path),
        "format": "template-package-v2",
        "id": template.id,
        "version": template.version,
        "name": template.name,
        "language": template.language,
        "status": template.status,
        "reference_docx": str(package.reference_docx),
        "shell_docx": str(package.shell_docx) if package.shell_docx else None,
        "inheritance_chain": [asdict(entry) for entry in package.inheritance_chain],
    }
    if resolved:
        payload["resolved"] = package.resolved_data
        payload["section_sources"] = package.section_sources
    console.print_json(json.dumps(payload, ensure_ascii=False, default=str))


@template_app.command("pack")
def template_pack(
    path: Path,
    output: Annotated[Path, typer.Option("-o", "--output", help="输出 .tftpl 路径")],
) -> None:
    """把 Template Package v2 目录打成确定性 .tftpl（前置 lint L1+L2）。"""
    if not path.is_dir():
        console.print(f"[red]读取失败：模板包目录不存在：{path}[/red]")
        raise typer.Exit(2)
    try:
        result = template_v2.pack_package(path, output)
    except template_v2.PackError as error:
        console.print(f"[red]打包失败：{error.path}[/red]")
        _print_template_issues(error.issues)
        raise typer.Exit(1) from None
    console.print(f"[green]✓ 已生成 .tftpl：{result}[/green]")


@template_app.command("verify")
def template_verify(
    path: Path,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="以 JSON 输出结构化诊断"),
    ] = False,
) -> None:
    """校验 .tftpl：解包防护 + manifest 哈希对账 + L1–L3 全量。"""
    if not path.is_file():
        console.print(f"[red]读取失败：.tftpl 文件不存在：{path}[/red]")
        raise typer.Exit(2)
    report = template_v2.verify_package(path)
    if json_output:
        payload = {
            "path": str(report.path),
            "issues": [asdict(issue) for issue in report.issues],
            "errors": report.errors,
            "warnings": report.warnings,
            "package_id": report.package.template.id if report.package else None,
        }
        console.print_json(json.dumps(payload, ensure_ascii=False, default=str))
    elif report.has_errors:
        console.print(f"[red]校验失败：{report.path}[/red]")
        _print_template_issues(report.issues)
    else:
        console.print(f"[green]✓ .tftpl 校验通过：{report.path}[/green]")
        non_errors = [i for i in report.issues if i.severity != "error"]
        if non_errors:
            _print_template_issues(non_errors)
    if report.has_errors:
        raise typer.Exit(1)


@template_app.command("migrate")
def template_migrate(
    source: Path,
    output: Annotated[Path, typer.Option("-o", "--output", help="输出包目录")],
    force: Annotated[
        bool,
        typer.Option("--force", help="输出目录非空时仍覆盖写入"),
    ] = False,
) -> None:
    """把 v0.3 单 YAML 模板迁移为 Template Package v2 目录骨架。"""
    if not source.is_file():
        console.print(f"[red]读取失败：v0.3 模板不存在：{source}[/red]")
        raise typer.Exit(2)
    try:
        report = template_v2.migrate_template(source, output, force=force)
    except template_v2.MigrateError as error:
        console.print(f"[red]迁移失败：{error}[/red]")
        raise typer.Exit(2) from None
    except TemplateLoadError as error:
        console.print(f"[red]v0.3 模板无效：{error}[/red]")
        raise typer.Exit(2) from None

    summary = report.summary
    console.print(
        f"[green]✓ 已迁移到 {report.output}[/green]：migrated={summary['migrated']} "
        f"manual-required={summary['manual-required']} dropped={summary['dropped']}；"
        "台账见 migration-report.json"
    )
    manual = [e for e in report.entries if e.status == "manual-required"]
    if manual:
        table = RichTable()
        table.add_column("Field", no_wrap=True)
        table.add_column("Reason", overflow="fold")
        table.add_column("Suggestion", overflow="fold")
        for entry in manual:
            table.add_row(entry.field, entry.reason or "", entry.suggestion or "")
        console.print(table)
    if report.lint_report.has_errors:
        console.print("[red]迁移产物 lint 存在 error（§8.2：非零退出）[/red]")
        _print_template_issues(report.lint_report.issues)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
