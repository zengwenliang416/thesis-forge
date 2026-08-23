import { AlertTriangle, Check, Clipboard, FileText, Terminal } from "lucide-react";
import { useState } from "react";
import type {
  BuildReport,
  BuildReportDiagnostic,
  BuildReportLog,
  BuildStage,
  BuildStageStatus,
} from "../transport/buildEvents";
import { PanelHeader } from "./PanelHeader";

type OutputView = "all" | "errors" | "warnings" | "logs";

const STAGES: readonly BuildStage[] = [
  "parse",
  "validate",
  "compile",
  "render",
  "finalize",
  "postflight",
  "preview",
];

const STAGE_LABELS: Record<BuildStage, string> = {
  parse: "解析",
  validate: "验证",
  compile: "编译",
  render: "渲染",
  finalize: "完成",
  postflight: "后处理",
  preview: "预览",
};

const STAGE_STATUS_LABELS: Record<BuildStageStatus, string> = {
  pending: "待处理",
  running: "进行中",
  succeeded: "已完成",
  failed: "失败",
  skipped: "已跳过",
};

const VIEW_LABELS: readonly [OutputView, string][] = [
  ["all", "全部"],
  ["errors", "错误"],
  ["warnings", "警告"],
  ["logs", "原始日志"],
];

const OUTCOME_LABELS: Record<BuildReport["outcome"], string> = {
  succeeded: "构建成功",
  failed: "构建失败",
  canceled: "构建已取消",
};

export interface BuildOutputPanelProps {
  report: BuildReport | null;
  onCopy?(text: string): void | Promise<void>;
}

function sourceLabel(
  source: BuildReportDiagnostic["source"],
): string {
  if (source === null) {
    return "未关联源码";
  }
  const column = source.startColumn === null ? "" : `:${source.startColumn}`;
  return `${source.file}:${source.startLine}${column}`;
}

function diagnosticText(diagnostic: BuildReportDiagnostic): string {
  const source = sourceLabel(diagnostic.source);
  const suggestion = diagnostic.suggestion
    ? `\n建议：${diagnostic.suggestion}`
    : "";
  return [
    `[${diagnostic.severity}] ${diagnostic.code}`,
    `阶段：${STAGE_LABELS[diagnostic.stage]}`,
    `消息：${diagnostic.message}`,
    `来源：${source}`,
    `目标：${diagnostic.target ?? "无"}`,
    suggestion,
  ]
    .filter(Boolean)
    .join("\n");
}

function logText(log: BuildReportLog): string {
  return `[${log.sequence}] ${STAGE_LABELS[log.stage]} · ${log.level}\n${log.message}`;
}

function severityLabel(severity: BuildReportDiagnostic["severity"]): string {
  return severity === "error"
    ? "错误"
    : severity === "warning"
      ? "警告"
      : "提示";
}

export function BuildOutputPanel({
  report,
  onCopy,
}: BuildOutputPanelProps) {
  const [view, setView] = useState<OutputView>("all");
  const [selectedLogSequence, setSelectedLogSequence] = useState<number | null>(
    null,
  );
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  async function copyText(key: string, text: string) {
    try {
      if (onCopy) {
        await onCopy(text);
      } else if (
        typeof navigator !== "undefined" &&
        navigator.clipboard !== undefined
      ) {
        await navigator.clipboard.writeText(text);
      } else {
        return;
      }
      setCopiedKey(key);
    } catch {
      setCopiedKey(null);
    }
  }

  if (report === null) {
    return (
      <section
        className="panel build-output-panel"
        role="region"
        aria-label="构建输出"
      >
        <PanelHeader
          icon={<FileText />}
          kicker="BUILD REPORT"
          title="构建输出"
        />
        <div className="diagnostics-empty">
          <span className="diagnostic-count">—</span>
          <div>
            <strong>尚无构建报告</strong>
            <p>运行构建后，这里会显示阶段、诊断和原始日志。</p>
          </div>
        </div>
      </section>
    );
  }

  const stageByName = new Map(report.stages.map((stage) => [stage.name, stage]));
  const primaryDiagnostic =
    report.diagnostics.find(
      (diagnostic) => diagnostic.id === report.primaryDiagnosticId,
    ) ?? null;
  const visiblePrimary =
    primaryDiagnostic !== null &&
    (view === "all" ||
      (view === "errors" && primaryDiagnostic.severity === "error") ||
      (view === "warnings" && primaryDiagnostic.severity === "warning"));
  const visibleDiagnostics = report.diagnostics.filter((diagnostic) => {
    if (view === "errors") {
      return diagnostic.severity === "error";
    }
    if (view === "warnings") {
      return diagnostic.severity === "warning";
    }
    return view !== "logs";
  });
  const diagnosticList = visiblePrimary
    ? visibleDiagnostics.filter(
        (diagnostic) => diagnostic.id !== primaryDiagnostic?.id,
      )
    : visibleDiagnostics;
  const selectedLog =
    report.logs.find((log) => log.sequence === selectedLogSequence) ?? null;
  const errorCount = report.diagnostics.filter(
    (diagnostic) => diagnostic.severity === "error",
  ).length;
  const warningCount = report.diagnostics.filter(
    (diagnostic) => diagnostic.severity === "warning",
  ).length;

  return (
    <section
      className="panel build-output-panel"
      role="region"
      aria-label="构建输出"
      data-active-view={view}
    >
      <PanelHeader
        icon={<FileText />}
        kicker="BUILD REPORT"
        title="构建输出"
      />
      <div className="diagnostics-content">
        <div
          className="diagnostic-filters"
          role="tablist"
          aria-label="构建输出视图"
        >
          {VIEW_LABELS.map(([value, label]) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={view === value}
              onClick={() => setView(value)}
            >
              {label}
              {value === "errors"
                ? ` ${errorCount}`
                : value === "warnings"
                  ? ` ${warningCount}`
                  : ""}
            </button>
          ))}
        </div>

        <div className="build-report-summary">
          <div>
            <strong>{OUTCOME_LABELS[report.outcome]}</strong>
            <span>{report.intent === "publish" ? "手动构建" : "实时预览"}</span>
          </div>
          <code>{report.buildId}</code>
          {report.output?.previewStale ? (
            <span role="status">上一次成功预览 · 已过期</span>
          ) : null}
        </div>

        <div className="build-stage-summary" aria-label="构建阶段">
          {STAGES.map((stageName) => {
            const stage = stageByName.get(stageName);
            const status = stage?.status ?? "pending";
            return (
              <div
                key={stageName}
                className="build-stage"
                data-stage-status={status}
                aria-label={`${STAGE_LABELS[stageName]}：${STAGE_STATUS_LABELS[status]}`}
              >
                <span>{STAGE_LABELS[stageName]}</span>
                <strong>{STAGE_STATUS_LABELS[status]}</strong>
              </div>
            );
          })}
        </div>

        {view === "logs" ? (
          <div className="build-log-list" aria-label="原始构建日志">
            <div className="panel-footer">
              <span>共 {report.logs.length} 条日志</span>
              <button
                type="button"
                className="button"
                disabled={report.logs.length === 0}
                onClick={() =>
                  void copyText(
                    "all-logs",
                    report.logs.map(logText).join("\n\n"),
                  )
                }
              >
                <Clipboard aria-hidden="true" />
                {copiedKey === "all-logs" ? "已复制" : "复制全部日志"}
              </button>
            </div>
            {report.logs.length === 0 ? (
              <div className="diagnostics-empty">
                <Terminal aria-hidden="true" />
                <span>暂无原始日志</span>
              </div>
            ) : (
              report.logs.map((log) => (
                <div
                  key={log.sequence}
                  className="build-log-row"
                  data-selected={selectedLogSequence === log.sequence}
                >
                  <button
                    type="button"
                    className="diagnostic-row"
                    aria-pressed={selectedLogSequence === log.sequence}
                    aria-label={`选择第 ${log.sequence} 条日志`}
                    onClick={() => setSelectedLogSequence(log.sequence)}
                  >
                    <span>{STAGE_LABELS[log.stage]}</span>
                    <strong>{log.message}</strong>
                    <code>{log.level}</code>
                  </button>
                  <button
                    type="button"
                    className="button"
                    aria-label={`复制第 ${log.sequence} 条日志`}
                    onClick={() => void copyText(`log-${log.sequence}`, logText(log))}
                  >
                    {copiedKey === `log-${log.sequence}` ? (
                      <Check aria-hidden="true" />
                    ) : (
                      <Clipboard aria-hidden="true" />
                    )}
                  </button>
                </div>
              ))
            )}
            {selectedLog ? (
              <pre className="build-log-detail">{logText(selectedLog)}</pre>
            ) : null}
          </div>
        ) : (
          <>
            {visiblePrimary ? (
              <details
                className="primary-diagnostic"
                open
                data-severity={primaryDiagnostic.severity}
              >
                <summary>
                  <AlertTriangle aria-hidden="true" />
                  <span>主诊断</span>
                  <code>{primaryDiagnostic.code}</code>
                </summary>
                <dl>
                  <div>
                    <dt>阶段</dt>
                    <dd>{STAGE_LABELS[primaryDiagnostic.stage]}</dd>
                  </div>
                  <div>
                    <dt>消息</dt>
                    <dd>{primaryDiagnostic.message}</dd>
                  </div>
                  <div>
                    <dt>来源</dt>
                    <dd>{sourceLabel(primaryDiagnostic.source)}</dd>
                  </div>
                  <div>
                    <dt>建议</dt>
                    <dd>{primaryDiagnostic.suggestion ?? "无"}</dd>
                  </div>
                </dl>
                <button
                  type="button"
                  className="button"
                  onClick={() =>
                    void copyText(
                      "primary-diagnostic",
                      diagnosticText(primaryDiagnostic),
                    )
                  }
                >
                  {copiedKey === "primary-diagnostic" ? (
                    <Check aria-hidden="true" />
                  ) : (
                    <Clipboard aria-hidden="true" />
                  )}
                  {copiedKey === "primary-diagnostic" ? "已复制" : "复制诊断"}
                </button>
              </details>
            ) : null}

            {diagnosticList.length === 0 ? (
              <div className="diagnostics-empty">
                <span className="diagnostic-count">0</span>
                <div>
                  <strong>当前视图没有诊断</strong>
                  <p>切换到全部、错误或警告查看其他构建信息。</p>
                </div>
              </div>
            ) : (
              <div className="diagnostic-list">
                {diagnosticList.map((diagnostic) => (
                  <article
                    key={diagnostic.id}
                    className="diagnostic-row"
                    data-severity={diagnostic.severity}
                  >
                    <span className="diagnostic-severity">
                      {severityLabel(diagnostic.severity)}
                    </span>
                    <strong>{diagnostic.message}</strong>
                    <code>{diagnostic.code}</code>
                    <span>
                      {STAGE_LABELS[diagnostic.stage]} ·{" "}
                      {sourceLabel(diagnostic.source)}
                    </span>
                  </article>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
