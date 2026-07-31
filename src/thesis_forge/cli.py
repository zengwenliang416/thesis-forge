from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table as RichTable

from thesis_forge.application import (
    ApplicationStageError,
    BuildValidationError,
    build_service,
    inspect_service,
    validation_service,
)

app = typer.Typer(help="ThesisForge — academic thesis compiler")
console = Console(width=160)


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


def _localized_issue_message(issue) -> str:
    details = issue.details
    if issue.code == "required-metadata":
        return f"缺少必填元数据: {details.get('path', issue.target or '')}"
    if issue.code == "empty-document":
        return "论文正文为空"
    if issue.code == "invalid-id-prefix":
        return f"ID 前缀无效: {issue.target}，期望 {details.get('expected', '')}:"
    if issue.code == "duplicate-id":
        return f"重复 ID: {issue.target}"
    if issue.code == "missing-reference":
        return f"引用目标不存在: {issue.target}"
    if issue.code == "heading-level-jump":
        return (
            f"标题层级从 H{details.get('previous_level', '?')} "
            f"跳到 H{details.get('current_level', '?')}"
        )
    if issue.code == "resource-path-escape":
        kind = "图片" if details.get("resource_type") == "image" else "参考文献"
        return f"{kind}路径越出论文资源目录: {issue.target}"
    if issue.code == "missing-image":
        return f"图片不存在: {issue.target}"
    if issue.code == "missing-bibliography":
        if issue.target:
            return f"参考文献文件不存在: {issue.target}"
        return "文档包含引用，但未配置本地 bibliography 路径"
    if issue.code == "invalid-bibliography":
        return (
            f"参考文献数据无效: {issue.target}: "
            f"{details.get('problem', issue.message)}"
        )
    if issue.code == "missing-citation":
        return f"本地参考文献中不存在 citation key: {issue.target}"
    if issue.code == "missing-template":
        return f"找不到模板: {details.get('selector', issue.target or 'template')}"
    if issue.code == "ambiguous-template":
        return (
            f"模板 ID 不唯一: {details.get('template_id', issue.target or '')}: "
            f"{details.get('paths', '')}"
        )
    if issue.code == "invalid-template":
        return (
            f"模板无效: {details.get('path', '')}: "
            f"{details.get('field', issue.target or '')}: "
            f"{details.get('problem', '')}"
        )
    if issue.code == "missing-template-style":
        return f"模板未定义所需样式: {issue.target}"
    return issue.message


@app.command()
def inspect(source: Path) -> None:
    """解析 Markdown 并输出结构。"""
    try:
        doc = inspect_service(source).document
    except ApplicationStageError as error:
        _report_application_error(error, source=source)
    data = {
        "source": str(doc.source_path),
        "metadata": doc.metadata,
        "bibliography": asdict(doc.bibliography) if doc.bibliography else None,
        "blocks": [
            {"kind": block.__class__.__name__, **asdict(block)} for block in doc.blocks
        ],
        "inline_content": [
            {"kind": inline.__class__.__name__, **asdict(inline)}
            for inline in doc.inline_content
        ],
        "cross_references": [asdict(reference) for reference in doc.cross_references],
        "citations": [asdict(citation) for citation in doc.citations],
        "footnote_references": [asdict(reference) for reference in doc.footnote_references],
    }
    console.print_json(json.dumps(data, ensure_ascii=False, default=str))


@app.command()
def validate(
    source: Path,
    template: Annotated[
        Path | None,
        typer.Option("--template", help="显式学校模板 YAML 路径"),
    ] = None,
) -> None:
    """检查结构和引用问题。"""
    try:
        result = validation_service(source, template_path=template)
    except ApplicationStageError as error:
        _report_application_error(error, source=source)
    issues = result.issues

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
            _localized_issue_message(issue),
        )
    console.print(table)

    if any(i.severity == "error" for i in issues):
        raise typer.Exit(1)


@app.command()
def build(
    source: Path,
    output: Annotated[
        Path,
        typer.Option("-o", "--output"),
    ] = Path("output/thesis.docx"),
    template: Annotated[
        Path | None,
        typer.Option("--template", help="显式学校模板 YAML 路径"),
    ] = None,
) -> None:
    """通过安全的本地编译流水线生成 DOCX。"""
    try:
        result = build_service(
            source,
            output,
            template_path=template,
        )
    except BuildValidationError as error:
        error_count = sum(issue.severity == "error" for issue in error.issues)
        console.print(
            f"[red]编译停止（{error.stage}）：存在 {error_count} 个错误。"
            "请先运行 validate。[/red]"
        )
        raise typer.Exit(1)
    except ApplicationStageError as error:
        console.print(f"[red]构建失败（{error.stage}）：{error}[/red]")
        raise typer.Exit(2) from None

    console.print(f"[green]✓ 已生成 DOCX：{result.output_path}[/green]")


if __name__ == "__main__":
    app()
