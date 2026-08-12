import type {
  CSSProperties,
  PointerEvent as ReactPointerEvent,
  RefObject,
} from "react";
import type {
  PreviewMode,
  WorkspaceActions,
  WorkspaceState,
} from "../state/workspace";
import type {
  DiagnosticFilter,
  DiagnosticPresentation,
} from "../state/diagnostics";
import type {
  RuntimeCapabilities,
} from "../transport/WorkbenchTransport";
import type { RuntimeKind } from "../transport/dto";
import { OutputFeedback } from "./OutputFeedback";
import { ProductBar } from "./ProductBar";
import { StatusStrip } from "./StatusStrip";
import {
  DiagnosticsPanel,
  MarkdownEditor,
} from "./WorkbenchPanels";
import { DualPreviewPanel, OutlinePanel } from "./PreviewPanels";
import type { ContentSelection } from "../state/preview";

const panels = [
  { id: "outline", label: "大纲" },
  { id: "editor", label: "编辑" },
  { id: "preview", label: "预览" },
  { id: "diagnostics", label: "诊断" },
] as const;

interface WorkbenchShellProps {
  state: WorkspaceState;
  actions: WorkspaceActions;
  runtime: RuntimeKind;
  capabilities: RuntimeCapabilities;
  statusTitle: string;
  statusDetail: string;
  editorRef: RefObject<HTMLTextAreaElement | null>;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onChooseSource(): void;
  onFileSelected(file: File): void;
  onSave(): void;
  onValidate(): void;
  onBuild(): void;
  onCancel(): void;
  onRecover(): void;
  onTemplateSelected(templateId: string | null): void;
  onDiagnosticFilterChanged(filter: DiagnosticFilter): void;
  onDiagnosticActivated(diagnostic: DiagnosticPresentation): void;
  onContentActivated(selection: ContentSelection): void;
  onPreviewModeChanged(mode: PreviewMode): void;
  onSelectWpsPdf(): void;
  onEdit(text: string): void;
  onMobilePanelSelected(panel: WorkspaceState["mobilePanel"]): void;
  onPanelsResized(outlineWidth: number, previewWidth: number): void;
  onResizePointer(
    side: "outline" | "preview",
    event: ReactPointerEvent<HTMLDivElement>,
  ): void;
}

export function WorkbenchShell({
  state,
  actions,
  runtime,
  capabilities,
  statusTitle,
  statusDetail,
  editorRef,
  fileInputRef,
  onChooseSource,
  onFileSelected,
  onSave,
  onValidate,
  onBuild,
  onCancel,
  onRecover,
  onTemplateSelected,
  onDiagnosticFilterChanged,
  onDiagnosticActivated,
  onContentActivated,
  onPreviewModeChanged,
  onSelectWpsPdf,
  onEdit,
  onMobilePanelSelected,
  onPanelsResized,
  onResizePointer,
}: WorkbenchShellProps) {
  const layoutStyle = {
    "--outline-width": `${state.outlineWidth}px`,
    "--preview-width": `${state.previewWidth}px`,
  } as CSSProperties;

  return (
    <div
      className="app-shell"
      data-runtime={runtime}
      data-state={state.status}
      style={layoutStyle}
    >
      <ProductBar
        state={state}
        actions={actions}
        fileInputRef={fileInputRef}
        onChooseSource={onChooseSource}
        onFileSelected={onFileSelected}
        onSave={onSave}
        onValidate={onValidate}
        onBuild={onBuild}
        onCancel={onCancel}
      />
      <StatusStrip
        state={state}
        runtime={runtime}
        title={statusTitle}
        detail={statusDetail}
        onRecover={onRecover}
        onTemplateSelected={onTemplateSelected}
      />
      <nav className="mobile-tabs" role="tablist" aria-label="工作台面板">
        {panels.map((panel) => (
          <button
            key={panel.id}
            type="button"
            role="tab"
            aria-selected={state.mobilePanel === panel.id}
            onClick={() => onMobilePanelSelected(panel.id)}
          >
            {panel.label}
          </button>
        ))}
      </nav>
      <main className="workbench">
        <OutlinePanel state={state} onActivated={onContentActivated} />
        <PanelResizer
          side="outline"
          state={state}
          onPanelsResized={onPanelsResized}
          onResizePointer={onResizePointer}
        />
        <MarkdownEditor
          state={state}
          actions={actions}
          runtime={runtime}
          editorRef={editorRef}
          onEdit={onEdit}
        />
        <PanelResizer
          side="preview"
          state={state}
          onPanelsResized={onPanelsResized}
          onResizePointer={onResizePointer}
        />
        <section
          className="right-rail"
          data-mobile-active={
            state.mobilePanel === "preview" ||
            state.mobilePanel === "diagnostics"
          }
        >
          <DualPreviewPanel
            state={state}
            onActivated={onContentActivated}
            onModeChanged={onPreviewModeChanged}
            onBuild={onBuild}
            onSelectWpsPdf={onSelectWpsPdf}
          />
          <DiagnosticsPanel
            state={state}
            onFilterChanged={onDiagnosticFilterChanged}
            onActivated={onDiagnosticActivated}
          />
        </section>
      </main>
      <OutputFeedback
        runtime={runtime}
        capabilities={capabilities}
        state={state}
      />
    </div>
  );
}

interface PanelResizerProps {
  side: "outline" | "preview";
  state: WorkspaceState;
  onPanelsResized(outlineWidth: number, previewWidth: number): void;
  onResizePointer(
    side: "outline" | "preview",
    event: ReactPointerEvent<HTMLDivElement>,
  ): void;
}

function PanelResizer({
  side,
  state,
  onPanelsResized,
  onResizePointer,
}: PanelResizerProps) {
  const outline = side === "outline";
  const label = outline ? "调整大纲宽度" : "调整预览宽度";
  const value = outline ? state.outlineWidth : state.previewWidth;

  return (
    <div
      className="panel-resizer"
      role="separator"
      tabIndex={0}
      aria-label={label}
      aria-orientation="vertical"
      aria-valuemin={outline ? 210 : 340}
      aria-valuemax={outline ? 380 : 620}
      aria-valuenow={value}
      onPointerDown={(event) => onResizePointer(side, event)}
      onKeyDown={(event) => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
          return;
        }
        event.preventDefault();
        const delta = event.key === "ArrowRight" ? 16 : -16;
        onPanelsResized(
          outline ? state.outlineWidth + delta : state.outlineWidth,
          outline ? state.previewWidth : state.previewWidth + delta,
        );
      }}
    />
  );
}
