import type { SerializedDiagnostic } from "../transport/dto";

export type DiagnosticFilter = "all" | SerializedDiagnostic["severity"];

export interface DiagnosticPresentation extends SerializedDiagnostic {
  id: string;
}

export interface DiagnosticSummary {
  all: number;
  error: number;
  warning: number;
  info: number;
}

const severityOrder = {
  error: 0,
  warning: 1,
  info: 2,
} satisfies Record<SerializedDiagnostic["severity"], number>;

function compareText(left: string, right: string) {
  if (left === right) {
    return 0;
  }
  return left < right ? -1 : 1;
}

function detail(
  diagnostic: SerializedDiagnostic,
  key: string,
  fallback = "",
) {
  return diagnostic.details[key] ?? fallback;
}

export function localizedDiagnosticMessage(
  diagnostic: SerializedDiagnostic,
): string {
  switch (diagnostic.code) {
    case "required-metadata":
      return `缺少必填元数据：${detail(
        diagnostic,
        "path",
        diagnostic.target ?? "",
      )}`;
    case "empty-document":
      return "论文正文为空";
    case "invalid-id-prefix":
      return `ID 前缀无效：${diagnostic.target ?? ""}，期望 ${detail(
        diagnostic,
        "expected",
      )}`;
    case "duplicate-id":
      return `重复 ID：${diagnostic.target ?? ""}`;
    case "missing-reference":
      return `引用目标不存在：${diagnostic.target ?? ""}`;
    case "heading-level-jump":
      return `标题层级从 H${detail(
        diagnostic,
        "previous_level",
        "?",
      )} 跳到 H${detail(diagnostic, "current_level", "?")}`;
    case "resource-path-escape":
      return `${
        detail(diagnostic, "resource_type") === "image" ? "图片" : "参考文献"
      }路径越出论文资源目录：${diagnostic.target ?? ""}`;
    case "missing-image":
      return `图片不存在：${diagnostic.target ?? ""}`;
    case "missing-bibliography":
      return diagnostic.target
        ? `参考文献文件不存在：${diagnostic.target}`
        : "文档包含引用，但未配置本地 bibliography 路径";
    case "invalid-bibliography":
      return `参考文献数据无效：${diagnostic.target ?? ""}：${detail(
        diagnostic,
        "problem",
        diagnostic.message,
      )}`;
    case "missing-citation":
      return `本地参考文献中不存在 citation key：${diagnostic.target ?? ""}`;
    case "missing-template":
      return `找不到模板：${detail(
        diagnostic,
        "selector",
        diagnostic.target ?? "template",
      )}`;
    case "ambiguous-template":
      return `模板 ID 不唯一：${detail(
        diagnostic,
        "template_id",
        diagnostic.target ?? "",
      )}：${detail(diagnostic, "paths")}`;
    case "invalid-template":
      return `模板无效：${detail(diagnostic, "path")}：${detail(
        diagnostic,
        "field",
        diagnostic.target ?? "",
      )}：${detail(diagnostic, "problem")}`;
    case "missing-template-style":
      return `模板未定义所需样式：${diagnostic.target ?? ""}`;
    default:
      return diagnostic.message;
  }
}

export function presentDiagnostics(
  diagnostics: SerializedDiagnostic[],
): DiagnosticPresentation[] {
  return diagnostics
    .map((diagnostic, index) => ({
      ...diagnostic,
      id: `${diagnostic.code}:${diagnostic.line ?? 0}:${
        diagnostic.target ?? ""
      }:${index}`,
      message: localizedDiagnosticMessage(diagnostic),
    }))
    .sort(
      (left, right) =>
        (left.line ?? -1) - (right.line ?? -1) ||
        severityOrder[left.severity] - severityOrder[right.severity] ||
        compareText(left.code, right.code) ||
        compareText(left.target ?? "", right.target ?? "") ||
        compareText(left.message, right.message),
    );
}

export function diagnosticSummary(
  diagnostics: DiagnosticPresentation[],
): DiagnosticSummary {
  const summary: DiagnosticSummary = {
    all: diagnostics.length,
    error: 0,
    warning: 0,
    info: 0,
  };
  for (const diagnostic of diagnostics) {
    summary[diagnostic.severity] += 1;
  }
  return summary;
}

export function selectVisibleDiagnostics(
  diagnostics: DiagnosticPresentation[],
  filter: DiagnosticFilter,
) {
  return filter === "all"
    ? diagnostics
    : diagnostics.filter((diagnostic) => diagnostic.severity === filter);
}

export function hasFatalDiagnostics(
  diagnostics: DiagnosticPresentation[],
) {
  return diagnostics.some((diagnostic) => diagnostic.severity === "error");
}
