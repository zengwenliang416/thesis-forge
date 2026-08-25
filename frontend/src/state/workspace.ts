import type { OperationKind, SourceKind, SourceRef } from "../transport/dto";
import type {
  BuildErrorKind,
  BuildOutput,
  BuildStage,
} from "../transport/buildEvents";
import type { FinalPreviewDescriptor } from "../transport/finalPreview";
import {
  hasFatalDiagnostics,
  type DiagnosticFilter,
  type DiagnosticPresentation,
} from "./diagnostics";
import {
  EMPTY_PREVIEW,
  type OutlineItem,
  type PreviewDocument,
} from "./preview";

export type WorkspaceStatus =
  | "empty"
  | "loading"
  | "populated"
  | "dirty"
  | "error"
  | "disabled"
  | "permission"
  | "canceled";

export interface OperationToken {
  kind: OperationKind;
  generation: number;
}

export interface WorkspaceSource {
  kind: SourceKind;
  name: string;
  writable: boolean;
  reference?: SourceRef;
}

export interface WorkspaceProject {
  id: string;
  root: string;
  manifestPath: string;
  name: string;
}

export type PreviewMode = "structure" | "final-layout" | "review";

export type FinalPreviewStatus =
  | "empty"
  | "building"
  | "ready"
  | "stale"
  | "unavailable"
  | "failed";

export interface FinalPreviewState {
  status: FinalPreviewStatus;
  descriptor: FinalPreviewDescriptor | null;
  bytes: Uint8Array | null;
  message: string | null;
  revision: number | null;
  requestKey: string | null;
}

export interface WorkspaceState {
  status: WorkspaceStatus;
  source: WorkspaceSource | null;
  project: WorkspaceProject | null;
  savedText: string;
  editorText: string;
  dirty: boolean;
  operation: OperationToken | null;
  errorMessage: string | null;
  templateId: string | null;
  diagnostics: DiagnosticPresentation[];
  diagnosticFilter: DiagnosticFilter;
  activeDiagnosticId: string | null;
  outline: OutlineItem[];
  preview: PreviewDocument;
  activeSelectionId: string | null;
  buildProgress: BuildStage[];
  buildErrorKind: BuildErrorKind | null;
  output: BuildOutput | null;
  contentRevision: number;
  previewMode: PreviewMode;
  finalPreview: FinalPreviewState;
  mobilePanel: "outline" | "editor" | "preview" | "diagnostics";
  outlineWidth: number;
  previewWidth: number;
}

export interface WorkspaceActions {
  canOpen: boolean;
  canEdit: boolean;
  canSave: boolean;
  canSaveAs: boolean;
  canDownload: boolean;
  canValidate: boolean;
  canBuild: boolean;
  canCancel: boolean;
}

export type WorkspaceEvent =
  | { type: "sourceOpened"; source: WorkspaceSource; text: string }
  | {
      type: "projectOpened";
      project: WorkspaceProject;
      source: WorkspaceSource;
      text: string;
    }
  | { type: "textEdited"; text: string }
  | { type: "templateSelected"; templateId: string | null }
  | {
      type: "diagnosticsLoaded";
      operation: OperationToken;
      diagnostics: DiagnosticPresentation[];
    }
  | {
      type: "presentationLoaded";
      operation: OperationToken;
      outline: OutlineItem[];
      preview: PreviewDocument;
    }
  | { type: "diagnosticFilterChanged"; filter: DiagnosticFilter }
  | {
      type: "diagnosticActivated";
      diagnosticId: string;
      line: number | null;
    }
  | {
      type: "contentActivated";
      selectionId: string;
      line: number | null;
    }
  | { type: "operationStarted"; operation: OperationToken }
  | { type: "saveSucceeded"; operation: OperationToken }
  | { type: "operationSucceeded"; operation: OperationToken }
  | {
      type: "operationFailed";
      operation: OperationToken;
      message: string;
      permission?: boolean;
    }
  | { type: "operationCanceled"; operation: OperationToken }
  | {
      type: "buildProgressed";
      operation: OperationToken;
      stage: BuildStage;
    }
  | {
      type: "buildSucceeded";
      operation: OperationToken;
      output: BuildOutput;
    }
  | {
      type: "finalPreviewResolved";
      requestKey: string;
      bytes: Uint8Array;
      descriptor?: FinalPreviewDescriptor;
    }
  | {
      type: "finalPreviewResolutionFailed";
      requestKey: string;
      message: string;
    }
  | {
      type: "livePreviewStarted";
      requestKey: string;
      revision: number;
    }
  | {
      type: "livePreviewDiagnosticsLoaded";
      requestKey: string;
      revision: number;
      diagnostics: DiagnosticPresentation[];
    }
  | {
      type: "livePreviewBuildSucceeded";
      requestKey: string;
      revision: number;
      descriptor: FinalPreviewDescriptor | null;
    }
  | {
      type: "livePreviewCanceled";
      requestKey: string;
      revision: number;
    }
  | {
      type: "livePreviewFailed";
      requestKey: string;
      revision: number;
      message: string;
    }
  | {
      type: "finalPreviewSelectionStarted";
      requestKey: string;
    }
  | {
      type: "finalPreviewSelectionCanceled";
      requestKey: string;
    }
  | {
      type: "finalPreviewSelected";
      requestKey: string;
      descriptor: FinalPreviewDescriptor;
      bytes: Uint8Array;
    }
  | {
      type: "finalPreviewSelectionFailed";
      requestKey: string;
      message: string;
    }
  | { type: "previewModeSelected"; mode: PreviewMode }
  | {
      type: "buildFailed";
      operation: OperationToken;
      kind: BuildErrorKind;
      message: string;
    }
  | { type: "recovered" }
  | {
      type: "mobilePanelSelected";
      panel: WorkspaceState["mobilePanel"];
    }
  | {
      type: "panelsResized";
      outlineWidth: number;
      previewWidth: number;
    };

export function createInitialWorkspaceState(): WorkspaceState {
  return {
    status: "empty",
    source: null,
    project: null,
    savedText: "",
    editorText: "",
    dirty: false,
    operation: null,
    errorMessage: null,
    templateId: null,
    diagnostics: [],
    diagnosticFilter: "all",
    activeDiagnosticId: null,
    outline: [],
    preview: EMPTY_PREVIEW,
    activeSelectionId: null,
    buildProgress: [],
    buildErrorKind: null,
    output: null,
    contentRevision: 0,
    previewMode: "final-layout",
    finalPreview: {
      status: "empty",
      descriptor: null,
      bytes: null,
      message: null,
      revision: null,
      requestKey: null,
    },
    mobilePanel: "editor",
    outlineWidth: 260,
    previewWidth: 430,
  };
}

function isCurrent(state: WorkspaceState, operation: OperationToken) {
  return (
    state.operation?.kind === operation.kind &&
    state.operation.generation === operation.generation
  );
}

function staleFinalPreview(
  preview: FinalPreviewState,
): FinalPreviewState {
  if (
    preview.status !== "ready" &&
    preview.status !== "building" &&
    preview.status !== "stale"
  ) {
    return preview;
  }
  return {
    ...preview,
    status: "stale",
    message: "文稿或模板已改变，请重新构建或选择新的 Office PDF。",
    requestKey: null,
  };
}

export function reduceWorkspaceState(
  state: WorkspaceState,
  event: WorkspaceEvent,
): WorkspaceState {
  switch (event.type) {
    case "sourceOpened":
    case "projectOpened":
      return {
        ...state,
        status: "populated",
        source: event.source,
        project: event.type === "projectOpened" ? event.project : null,
        savedText: event.text,
        editorText: event.text,
        dirty: false,
        operation: null,
        errorMessage: null,
        templateId: null,
        diagnostics: [],
        diagnosticFilter: "all",
        activeDiagnosticId: null,
        outline: [],
        preview: EMPTY_PREVIEW,
        activeSelectionId: null,
        buildProgress: [],
        buildErrorKind: null,
        output: null,
        contentRevision: state.contentRevision + 1,
        previewMode: "final-layout",
        finalPreview: {
          status: "empty",
          descriptor: null,
          bytes: null,
          message: null,
          revision: null,
          requestKey: null,
        },
      };
    case "textEdited": {
      const dirty = event.text !== state.savedText;
      const changed = event.text !== state.editorText;
      return {
        ...state,
        status: dirty ? "dirty" : "populated",
        editorText: event.text,
        dirty,
        operation: null,
        errorMessage: null,
        contentRevision: changed
          ? state.contentRevision + 1
          : state.contentRevision,
        finalPreview: changed
          ? staleFinalPreview(state.finalPreview)
          : state.finalPreview,
      };
    }
    case "templateSelected": {
      const changed = event.templateId !== state.templateId;
      return {
        ...state,
        templateId: event.templateId,
        diagnostics: [],
        diagnosticFilter: "all",
        activeDiagnosticId: null,
        contentRevision: changed
          ? state.contentRevision + 1
          : state.contentRevision,
        finalPreview: changed
          ? staleFinalPreview(state.finalPreview)
          : state.finalPreview,
      };
    }
    case "diagnosticsLoaded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        diagnostics: event.diagnostics,
        activeDiagnosticId: null,
      };
    case "presentationLoaded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        outline: event.outline,
        preview: event.preview,
        activeSelectionId: null,
      };
    case "diagnosticFilterChanged":
      return { ...state, diagnosticFilter: event.filter };
    case "diagnosticActivated":
      return {
        ...state,
        activeDiagnosticId: event.diagnosticId,
        mobilePanel: event.line === null ? state.mobilePanel : "editor",
      };
    case "contentActivated":
      return {
        ...state,
        activeSelectionId: event.selectionId,
        mobilePanel: event.line === null ? state.mobilePanel : "editor",
      };
    case "operationStarted":
      {
        const replacesLivePreview =
          event.operation.kind === "build" &&
          state.finalPreview.status === "building" &&
          state.finalPreview.requestKey?.startsWith("live-preview:");
      return {
        ...state,
        status: "loading",
        operation: event.operation,
        errorMessage: null,
        buildProgress:
          event.operation.kind === "build" ? [] : state.buildProgress,
        buildErrorKind:
          event.operation.kind === "build" ? null : state.buildErrorKind,
        previewMode:
          event.operation.kind === "build"
            ? "final-layout"
            : state.previewMode,
        finalPreview: replacesLivePreview
          ? state.finalPreview.bytes
            ? {
                ...state.finalPreview,
                status: "stale",
                message:
                  "正式 DOCX 构建已开始，当前仍显示上一版实时预览。",
                requestKey: null,
              }
            : {
                status: "empty",
                descriptor: null,
                bytes: null,
                message: null,
                revision: null,
                requestKey: null,
              }
          : state.finalPreview,
      };
      }
    case "buildProgressed": {
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      const order: BuildStage[] = [
        "parse",
        "validate",
        "compile",
        "render",
        "finalize",
      ];
      const current = state.buildProgress.at(-1);
      if (
        current !== undefined &&
        order.indexOf(event.stage) <= order.indexOf(current)
      ) {
        return state;
      }
      return {
        ...state,
        buildProgress: [...state.buildProgress, event.stage],
      };
    }
    case "buildSucceeded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      {
        const descriptor = event.output.finalPreview ?? null;
        const requestKey = `build:${event.operation.generation}`;
        return {
          ...state,
          status: state.dirty ? "dirty" : state.source ? "populated" : "empty",
          operation: null,
          errorMessage: null,
          buildErrorKind: null,
          output: event.output,
          previewMode: "final-layout",
          finalPreview: descriptor
            ? {
                status: "building",
                descriptor,
                bytes: null,
                message: "正在读取最终版式 PDF。",
                revision: state.contentRevision,
                requestKey,
              }
            : {
                status: "unavailable",
                descriptor: null,
                bytes: null,
                message:
                  "DOCX 已生成，但 Microsoft Word 未生成 PDF 预览。请重新构建，或选择 Word 导出的 PDF。",
                revision: state.contentRevision,
                requestKey: null,
              },
        };
      }
    case "finalPreviewResolved":
      if (
        state.finalPreview.status !== "building" ||
        state.finalPreview.requestKey !== event.requestKey ||
        state.finalPreview.revision !== state.contentRevision
      ) {
        return state;
      }
      return {
        ...state,
        finalPreview: {
          ...state.finalPreview,
          status: "ready",
          descriptor: event.descriptor ?? state.finalPreview.descriptor,
          bytes: event.bytes,
          message: null,
          requestKey: null,
        },
      };
    case "livePreviewStarted":
      if (event.revision !== state.contentRevision) {
        return state;
      }
      return {
        ...state,
        finalPreview: {
          ...state.finalPreview,
          status: "building",
          message: "正在根据当前编辑内容更新实时预览。",
          revision: event.revision,
          requestKey: event.requestKey,
        },
      };
    case "livePreviewDiagnosticsLoaded":
      if (
        state.finalPreview.requestKey !== event.requestKey ||
        event.revision !== state.contentRevision
      ) {
        return state;
      }
      return {
        ...state,
        diagnostics: event.diagnostics,
        activeDiagnosticId: null,
      };
    case "livePreviewBuildSucceeded":
      if (
        state.finalPreview.requestKey !== event.requestKey ||
        event.revision !== state.contentRevision
      ) {
        return state;
      }
      if (!event.descriptor) {
        return {
          ...state,
          finalPreview: state.finalPreview.bytes
            ? {
                ...state.finalPreview,
                status: "stale",
                message:
                  "Microsoft Word 实时 PDF 暂不可用，仍显示上一次预览。",
                requestKey: null,
              }
            : {
                status: "unavailable",
                descriptor: null,
                bytes: null,
                message:
                  "Microsoft Word 未生成实时 PDF。请检查 macOS“自动化”权限后重试。",
                revision: event.revision,
                requestKey: null,
              },
        };
      }
      return {
        ...state,
        finalPreview: {
          ...state.finalPreview,
          status: "building",
          message: "正在载入最新 PDF 页面。",
          revision: event.revision,
          requestKey: event.requestKey,
        },
      };
    case "livePreviewCanceled":
      if (
        state.finalPreview.requestKey !== event.requestKey ||
        event.revision !== state.contentRevision
      ) {
        return state;
      }
      return {
        ...state,
        finalPreview: state.finalPreview.bytes
          ? {
              ...state.finalPreview,
              status: "stale",
              message: "实时预览已取消，仍显示上一版预览。",
              requestKey: null,
            }
          : {
              ...state.finalPreview,
              status: "unavailable",
              message: "实时预览已取消。",
              requestKey: null,
            },
      };
    case "livePreviewFailed":
      if (
        state.finalPreview.requestKey !== event.requestKey ||
        event.revision !== state.contentRevision
      ) {
        return state;
      }
      return {
        ...state,
        finalPreview: state.finalPreview.bytes
          ? {
              ...state.finalPreview,
              status: "stale",
              message: `实时预览更新失败：${event.message}`,
              requestKey: null,
            }
          : {
              ...state.finalPreview,
              status: "failed",
              bytes: null,
              message: `实时预览更新失败：${event.message}`,
              revision: event.revision,
              requestKey: null,
            },
      };
    case "finalPreviewResolutionFailed":
      if (
        state.finalPreview.status !== "building" ||
        state.finalPreview.requestKey !== event.requestKey ||
        state.finalPreview.revision !== state.contentRevision
      ) {
        return state;
      }
      return {
        ...state,
        finalPreview:
          event.requestKey.startsWith("live-preview:") &&
          state.finalPreview.bytes
            ? {
                ...state.finalPreview,
                status: "stale",
                message: `实时预览更新失败：${event.message}`,
                requestKey: null,
              }
            : {
                ...state.finalPreview,
                status: "failed",
                bytes: null,
                message: event.message,
                requestKey: null,
              },
      };
    case "finalPreviewSelectionStarted":
      return {
        ...state,
        previewMode: "final-layout",
        finalPreview: {
          ...state.finalPreview,
          revision: state.contentRevision,
          requestKey: event.requestKey,
        },
      };
    case "finalPreviewSelectionCanceled":
      if (state.finalPreview.requestKey !== event.requestKey) {
        return state;
      }
      return {
        ...state,
        finalPreview: {
          ...state.finalPreview,
          requestKey: null,
        },
      };
    case "finalPreviewSelected":
      if (
        state.finalPreview.requestKey !== event.requestKey ||
        state.finalPreview.revision !== state.contentRevision
      ) {
        return state;
      }
      return {
        ...state,
        previewMode: "final-layout",
        finalPreview: {
          status: "ready",
          descriptor: event.descriptor,
          bytes: event.bytes,
          message: null,
          revision: state.contentRevision,
          requestKey: null,
        },
      };
    case "finalPreviewSelectionFailed":
      if (state.finalPreview.requestKey !== event.requestKey) {
        return state;
      }
      if (
        state.finalPreview.bytes &&
        (state.finalPreview.status === "ready" ||
          state.finalPreview.status === "stale")
      ) {
        return {
          ...state,
          finalPreview: {
            ...state.finalPreview,
            message:
              state.finalPreview.status === "stale"
                ? `文稿或模板已改变；选择新的 Office PDF 失败：${event.message}`
                : `选择新的 Office PDF 失败：${event.message}`,
            requestKey: null,
          },
        };
      }
      return {
        ...state,
        finalPreview: {
          ...state.finalPreview,
          status: "failed",
          message: event.message,
          requestKey: null,
        },
      };
    case "previewModeSelected":
      return { ...state, previewMode: event.mode };
    case "buildFailed":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: event.kind === "permission" ? "permission" : "error",
        operation: null,
        errorMessage: event.message,
        buildErrorKind: event.kind,
      };
    case "saveSucceeded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: "populated",
        savedText: state.editorText,
        dirty: false,
        operation: null,
        errorMessage: null,
        buildErrorKind: null,
      };
    case "operationSucceeded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: state.dirty ? "dirty" : state.source ? "populated" : "empty",
        operation: null,
        errorMessage: null,
      };
    case "operationFailed":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: event.permission ? "permission" : "error",
        operation: null,
        errorMessage: event.message,
      };
    case "operationCanceled":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: "canceled",
        operation: null,
        errorMessage: null,
      };
    case "recovered":
      return {
        ...state,
        status: state.dirty ? "dirty" : state.source ? "populated" : "empty",
        operation: null,
        errorMessage: null,
      };
    case "mobilePanelSelected":
      return { ...state, mobilePanel: event.panel };
    case "panelsResized":
      return {
        ...state,
        outlineWidth: Math.min(380, Math.max(210, event.outlineWidth)),
        previewWidth: Math.min(620, Math.max(340, event.previewWidth)),
      };
  }
}

const NONE: WorkspaceActions = {
  canOpen: false,
  canEdit: false,
  canSave: false,
  canSaveAs: false,
  canDownload: false,
  canValidate: false,
  canBuild: false,
  canCancel: false,
};

export function selectWorkspaceActions(state: WorkspaceState): WorkspaceActions {
  if (state.status === "loading") {
    return {
      ...NONE,
      canCancel:
        state.operation?.kind !== "save" &&
        state.operation?.kind !== "download" &&
        state.operation?.kind !== "refresh",
    };
  }
  if (state.status === "empty") {
    return { ...NONE, canOpen: true };
  }
  if (state.status === "dirty") {
    return {
      ...NONE,
      canOpen: true,
      canEdit: true,
      canSave: state.source?.writable ?? false,
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind === "web-upload",
    };
  }
  if (state.status === "populated") {
    return {
      ...NONE,
      canOpen: true,
      canEdit: true,
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind.startsWith("web-") ?? false,
      canValidate: true,
      canBuild: !hasFatalDiagnostics(state.diagnostics),
    };
  }
  if (state.status === "error" || state.status === "canceled") {
    return {
      ...NONE,
      canOpen: true,
      canEdit: state.source !== null,
      canSave: state.dirty && (state.source?.writable ?? false),
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind === "web-upload",
      canBuild:
        state.source !== null &&
        !state.dirty &&
        !hasFatalDiagnostics(state.diagnostics) &&
        (state.status === "canceled" || state.buildErrorKind !== null),
    };
  }
  if (state.status === "permission") {
    return {
      ...NONE,
      canOpen: true,
      canEdit: state.source !== null,
      canSave: state.dirty && (state.source?.writable ?? false),
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind === "web-upload",
    };
  }
  return NONE;
}
