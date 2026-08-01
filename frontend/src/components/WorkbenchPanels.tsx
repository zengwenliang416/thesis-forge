import {
  AlertTriangle,
  BookOpen,
  Braces,
  FileText,
  PanelRight,
} from "lucide-react";
import type { ReactNode, RefObject } from "react";
import type {
  WorkspaceActions,
  WorkspaceState,
} from "../state/workspace";
import type { RuntimeKind } from "../transport/dto";

export function OutlinePanel({ state }: { state: WorkspaceState }) {
  return (
    <aside
      className="panel outline-panel"
      aria-label="论文大纲"
      data-mobile-active={state.mobilePanel === "outline"}
    >
      <PanelHeader icon={<BookOpen />} kicker="THESIS DOCUMENT" title="论文大纲" />
      <div className="outline-empty">
        <div className="outline-root">
          <FileText aria-hidden="true" />
          <span>{state.source?.name ?? "等待载入文稿"}</span>
        </div>
        <p>打开并保存 Markdown 后，将从 Python inspection result 显示稳定结构。</p>
      </div>
      <div className="panel-footer">
        <span>协议</span>
        <code>workbench.v1</code>
      </div>
    </aside>
  );
}

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
      <PanelHeader icon={<Braces />} kicker="SOURCE" title="Markdown 编辑器" />
      <div className="editor-tab">
        <span>{state.source?.name ?? "未命名.md"}</span>
        <span>{state.dirty ? "未保存" : "UTF-8 · LF"}</span>
      </div>
      <textarea
        ref={editorRef}
        aria-label="Markdown 文稿内容"
        value={state.editorText}
        readOnly={!actions.canEdit}
        placeholder="打开 Markdown 文稿后在此编辑。"
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

export function PaperPreview({ state }: { state: WorkspaceState }) {
  return (
    <section
      className="panel preview-panel"
      role="region"
      aria-label="论文结构预览"
      data-mobile-active={state.mobilePanel === "preview"}
    >
      <PanelHeader
        icon={<PanelRight />}
        kicker="RENDER PLAN"
        title="论文结构预览"
      />
      <div className="paper-stage">
        <article className="paper">
          <span className="paper-running-head">本科毕业论文</span>
          <h1>{state.source ? "论文结构预览" : "等待载入论文"}</h1>
          <p>
            {state.source
              ? "这里将消费 renderer-neutral preview DTO，不解析 DOCX 或 OOXML。"
              : "打开文稿后，预览与大纲将来自同一保存快照。"}
          </p>
          <div className="paper-rule" />
          <p className="paper-note">结构预览不代表 Word 最终分页。</p>
        </article>
      </div>
    </section>
  );
}

export function DiagnosticsPanel({ state }: { state: WorkspaceState }) {
  return (
    <section
      className="panel diagnostics-panel"
      role="region"
      aria-label="诊断结果"
      data-mobile-active={state.mobilePanel === "diagnostics"}
    >
      <PanelHeader
        icon={<AlertTriangle />}
        kicker="VALIDATION"
        title="诊断结果"
      />
      <div className="diagnostics-empty">
        <span className="diagnostic-count">0</span>
        <div>
          <strong>尚无诊断</strong>
          <p>保存文稿后运行验证，问题会显示 code、行号和 target。</p>
        </div>
      </div>
    </section>
  );
}

function PanelHeader({
  icon,
  kicker,
  title,
}: {
  icon: ReactNode;
  kicker: string;
  title: string;
}) {
  return (
    <header className="panel-header">
      <div className="panel-icon" aria-hidden="true">
        {icon}
      </div>
      <div>
        <span>{kicker}</span>
        <h2>{title}</h2>
      </div>
    </header>
  );
}
