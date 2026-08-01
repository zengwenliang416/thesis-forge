from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thesis_forge.core.model import ValidationIssue


def localized_issue_message(issue: ValidationIssue) -> str:
    details = issue.details
    if issue.code == "required-metadata":
        return f"缺少必填元数据：{details.get('path', issue.target or '')}"
    if issue.code == "empty-document":
        return "论文正文为空"
    if issue.code == "invalid-id-prefix":
        return (
            f"ID 前缀无效：{issue.target or ''}，"
            f"期望 {details.get('expected', '')}"
        )
    if issue.code == "duplicate-id":
        return f"重复 ID：{issue.target or ''}"
    if issue.code == "missing-reference":
        return f"引用目标不存在：{issue.target or ''}"
    if issue.code == "heading-level-jump":
        return (
            f"标题层级从 H{details.get('previous_level', '?')} "
            f"跳到 H{details.get('current_level', '?')}"
        )
    if issue.code == "resource-path-escape":
        kind = "图片" if details.get("resource_type") == "image" else "参考文献"
        return f"{kind}路径越出论文资源目录：{issue.target or ''}"
    if issue.code == "missing-image":
        return f"图片不存在：{issue.target or ''}"
    if issue.code == "missing-bibliography":
        if issue.target:
            return f"参考文献文件不存在：{issue.target}"
        return "文档包含引用，但未配置本地 bibliography 路径"
    if issue.code == "invalid-bibliography":
        return (
            f"参考文献数据无效：{issue.target or ''}："
            f"{details.get('problem', issue.message)}"
        )
    if issue.code == "missing-citation":
        return f"本地参考文献中不存在 citation key：{issue.target or ''}"
    if issue.code == "missing-template":
        return f"找不到模板：{details.get('selector', issue.target or 'template')}"
    if issue.code == "ambiguous-template":
        return (
            f"模板 ID 不唯一：{details.get('template_id', issue.target or '')}："
            f"{details.get('paths', '')}"
        )
    if issue.code == "invalid-template":
        return (
            f"模板无效：{details.get('path', '')}："
            f"{details.get('field', issue.target or '')}："
            f"{details.get('problem', '')}"
        )
    if issue.code == "missing-template-style":
        return f"模板未定义所需样式：{issue.target or ''}"
    return issue.message
