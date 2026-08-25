import type { RefObject } from "react";
import type {
  WorkspaceActions,
  WorkspaceState,
} from "../state/workspace";
import {
  diagnosticSummary,
  selectVisibleDiagnostics,
  type DiagnosticFilter,
  type DiagnosticPresentation,
} from "../state/diagnostics";
import type { RuntimeKind } from "../transport/dto";

interface MarkdownEditorProps {
  state: WorkspaceState;
  actions: WorkspaceActions;
  runtime: RuntimeKind;
  editorRef: RefObject<HTMLTextAreaElement | null>;
  onEdit(text: string): void;
}

export function MarkdownEditor({
  state,
  actions,
  runtime,
  editorRef,
  onEdit,
}: MarkdownEditorProps) {
  return (
    <section
      className="panel editor-panel"
      role="region"
      aria-label="Markdown 编辑器"
      data-mobile-active={state.mobilePanel === "editor"}
    >
      <div className="editor-tab">
        <div>
          <strong>{state.source?.name ?? "未命名.md"}</strong>
          <span aria-hidden="true">×</span>
          <span aria-hidden="true">＋</span>
        </div>
        <span>{state.dirty ? "未保存" : "已保存"}</span>
      </div>
      <textarea
        ref={editorRef}
        aria-label="Markdown 文档内容"
        value={state.editorText}
        readOnly={!actions.canEdit}
        placeholder="打开 Markdown 文档后在此编辑。"
        spellCheck={false}
        onChange={(event) =>
          actions.canEdit ? onEdit(event.currentTarget.value) : undefined
        }
      />
      <div className="editor-status">
        <span>Markdown</span>
        <span>{state.editorText.split("\n").length} 行</span>
        <span>{runtime === "tauri" ? "本地模式" : "Web 模式"}</span>
      </div>
    </section>
  );
}

const filterLabels: Array<[DiagnosticFilter, string]> = [
  ["all", "全部"],
  ["error", "错误"],
  ["warning", "警告"],
  ["info", "提示"],
];

export function DiagnosticsPanel({
  state,
  onFilterChanged,
  onActivated,
}: {
  state: WorkspaceState;
  onFilterChanged(filter: DiagnosticFilter): void;
  onActivated(diagnostic: DiagnosticPresentation): void;
}) {
  const summary = diagnosticSummary(state.diagnostics);
  const visible = selectVisibleDiagnostics(
    state.diagnostics,
    state.diagnosticFilter,
  );
  return (
    <section
      className="panel diagnostics-panel"
      role="region"
      aria-label="诊断结果"
      data-mobile-active={state.mobilePanel === "diagnostics"}
    >
      <div className="diagnostics-toolbar">
        <div className="diagnostics-tabs">
          <strong>诊断 ({summary.all})</strong>
          <span>全部消息 ({summary.all})</span>
        </div>
        <div className="diagnostic-filters" aria-label="诊断筛选">
          {filterLabels.map(([filter, label]) => (
            <button
              key={filter}
              type="button"
              aria-pressed={state.diagnosticFilter === filter}
              disabled={!state.source}
              onClick={() => onFilterChanged(filter)}
            >
              {label} {summary[filter]}
            </button>
          ))}
        </div>
      </div>
      <div className="diagnostics-content">
        {state.diagnostics.length === 0 ? (
          <div className="diagnostics-empty">
            <strong>尚无诊断</strong>
            <span>保存文档后运行检查，问题会显示 code、行号和 target。</span>
          </div>
        ) : (
          <div className="diagnostic-list">
            {visible.map((diagnostic) => (
              <button
                key={diagnostic.id}
                type="button"
                className="diagnostic-row"
                data-severity={diagnostic.severity}
                aria-pressed={state.activeDiagnosticId === diagnostic.id}
                aria-label={`${
                  diagnostic.line === null
                    ? "无行号"
                    : `第 ${diagnostic.line} 行`
                } ${diagnostic.code} ${diagnostic.message}`}
                onClick={() => onActivated(diagnostic)}
              >
                <span className="diagnostic-severity">
                  {diagnostic.severity === "error"
                    ? "错误"
                    : diagnostic.severity === "warning"
                      ? "警告"
                      : "提示"}
                </span>
                <span className="diagnostic-location">
                  {diagnostic.line === null
                    ? "无行号"
                    : `行 ${diagnostic.line}`}
                </span>
                <strong>{diagnostic.message}</strong>
                <span className="diagnostic-detail">
                  <code>{diagnostic.code}</code>
                  {diagnostic.target ? ` · ${diagnostic.target}` : ""}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
