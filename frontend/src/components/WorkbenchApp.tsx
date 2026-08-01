import {
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useReducer,
  useRef,
} from "react";
import {
  reduceWorkspaceState,
  selectWorkspaceActions,
  type WorkspaceState,
} from "../state/workspace";
import {
  diagnosticSummary,
  presentDiagnostics,
} from "../state/diagnostics";
import { lineSelectionRange } from "../state/editorNavigation";
import type { WorkbenchTransport } from "../transport/WorkbenchTransport";
import {
  PROTOCOL_VERSION,
  readSerializedDiagnostics,
  type CommandEnvelope,
  type OperationKind,
} from "../transport/dto";
import { WorkbenchShell } from "./WorkbenchShell";

interface WorkbenchAppProps {
  transport: WorkbenchTransport;
  initialState: WorkspaceState;
}

const statusCopy = {
  empty: ["当前工作区没有 Markdown 文稿", "选择一个 .md 文件开始论文编译。"],
  loading: ["正在读取工作区", "正在同步保存快照和结构化结果。"],
  populated: ["文稿、模板与预览已同步", "当前内容来自同一份已保存快照。"],
  dirty: ["文稿有未保存修改", "请先显式保存，再验证或构建 DOCX。"],
  error: ["工作台操作失败", "保留现有内容，可恢复后重试。"],
  disabled: ["本机 DOCX 构建器尚未启用", "编辑器仍可使用。"],
  permission: ["目标位置不可写", "请选择有权限的位置后重试。"],
  canceled: ["操作已取消", "过期结果不会覆盖当前工作区。"],
} satisfies Record<WorkspaceState["status"], [string, string]>;

export function WorkbenchApp({
  transport,
  initialState,
}: WorkbenchAppProps) {
  const [state, dispatch] = useReducer(reduceWorkspaceState, initialState);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const actions = selectWorkspaceActions(state);
  const [defaultStatusTitle, defaultStatusDetail] = statusCopy[state.status];
  const fatalDiagnosticCount = diagnosticSummary(state.diagnostics).error;
  const statusTitle =
    state.status === "populated" && fatalDiagnosticCount > 0
      ? "构建已禁用"
      : defaultStatusTitle;
  const statusDetail =
    state.status === "populated" && fatalDiagnosticCount > 0
      ? `存在 ${fatalDiagnosticCount} 个错误诊断，构建已禁用。`
      : defaultStatusDetail;
  const generationRef = useRef(0);

  const nextOperation = (kind: OperationKind) => {
    generationRef.current += 1;
    return {
      kind,
      generation: generationRef.current,
    };
  };

  const requestFor = (
    operation: OperationKind,
    generation: number,
    payload: CommandEnvelope["payload"],
  ): CommandEnvelope => ({
    protocol: PROTOCOL_VERSION,
    requestId: `${operation}-${generation}`,
    operation,
    payload,
  });

  const failOperation = (
    operation: { kind: OperationKind; generation: number },
    error: unknown,
  ) => {
    if (
      typeof error === "object" &&
      error !== null &&
      "kind" in error &&
      "message" in error
    ) {
      dispatch({
        type: "operationFailed",
        operation,
        message: String(error.message),
        permission: error.kind === "permission",
      });
      return;
    }
    dispatch({
      type: "operationFailed",
      operation,
      message: error instanceof Error ? error.message : String(error),
    });
  };

  const refreshSource = async (
    source: NonNullable<WorkspaceState["source"]>["reference"],
    templateId = state.templateId,
  ) => {
    if (!source) {
      return;
    }
    const operation = nextOperation("refresh");
    dispatch({ type: "operationStarted", operation });
    try {
      for (const kind of ["inspect", "validate"] as const) {
        const response = await transport.dispatch(
          requestFor(kind, operation.generation, {
            source,
            ...(kind === "validate" ? { templateId } : {}),
          }),
        );
        if (!response.ok) {
          failOperation(operation, response.error);
          return;
        }
        if (kind === "validate") {
          dispatch({
            type: "diagnosticsLoaded",
            operation,
            diagnostics: presentDiagnostics(
              readSerializedDiagnostics(response.result, true),
            ),
          });
        }
      }
      dispatch({ type: "operationSucceeded", operation });
    } catch (error) {
      failOperation(operation, error);
    }
  };

  const runOperation = async (
    kind: "validate" | "build",
    templateId = state.templateId,
  ) => {
    const source = state.source?.reference;
    if (!source) {
      return;
    }
    const operation = nextOperation(kind);
    const output =
      kind === "build" && source.kind === "desktop"
        ? {
            kind: "desktop" as const,
            path: source.path.replace(/\.md$/i, ".docx"),
            fileName: source.fileName.replace(/\.md$/i, ".docx"),
          }
        : kind === "build" && source.kind === "web-workspace"
          ? {
              kind: "web-download" as const,
              workspaceId: source.workspaceId,
              fileName: source.fileName.replace(/\.md$/i, ".docx"),
            }
          : undefined;
    const request = requestFor(kind, operation.generation, {
      source,
      templateId,
      ...(output ? { output } : {}),
    });
    dispatch({ type: "operationStarted", operation });
    try {
      const response = await transport.dispatch(request);
      if (response.ok) {
        if (kind === "validate") {
          dispatch({
            type: "diagnosticsLoaded",
            operation,
            diagnostics: presentDiagnostics(
              readSerializedDiagnostics(response.result, true),
            ),
          });
        }
        dispatch({ type: "operationSucceeded", operation });
      } else {
        dispatch({
          type: "operationFailed",
          operation,
          message: response.error.message,
          permission: response.error.kind === "permission",
        });
      }
    } catch (error) {
      failOperation(operation, error);
    }
  };

  const saveSource = async () => {
    const source = state.source?.reference;
    if (!source || !actions.canSave) {
      return;
    }
    const operation = nextOperation("save");
    dispatch({ type: "operationStarted", operation });
    try {
      const response = await transport.dispatch(
        requestFor("save", operation.generation, {
          source,
          text: state.editorText,
        }),
      );
      if (!response.ok) {
        failOperation(operation, response.error);
        return;
      }
      dispatch({ type: "saveSucceeded", operation });
      await refreshSource(source);
    } catch (error) {
      failOperation(operation, error);
    }
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (!(event.metaKey || event.ctrlKey)) {
        return;
      }
      const key = event.key.toLowerCase();
      if (key === "k") {
        event.preventDefault();
        editorRef.current?.focus();
      }
      if (key === "s") {
        event.preventDefault();
        if (actions.canSave) {
          void saveSource();
        }
      }
      if (key === "b") {
        event.preventDefault();
        if (actions.canBuild) {
          void runOperation("build");
        }
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [
    actions.canBuild,
    actions.canSave,
    state.editorText,
    state.source,
    transport,
  ]);

  const applyOpenedSource = async (
    opened: Awaited<ReturnType<WorkbenchTransport["openSource"]>>,
  ) => {
    if (!opened) {
      return;
    }
    dispatch({
      type: "sourceOpened",
      source: {
        kind: opened.source.kind,
        name: opened.source.fileName,
        writable:
          opened.source.kind === "desktop" ||
          (opened.source.kind === "web-workspace" &&
            transport.capabilities.saveWorkspace),
        reference: opened.source,
      },
      text: opened.text,
    });
    await refreshSource(opened.source, null);
  };

  const openFile = async (file: File) => {
    const operation = nextOperation("open");
    dispatch({ type: "operationStarted", operation });
    try {
      await applyOpenedSource(
        await transport.openSource({
          fileName: file.name,
          text: await file.text(),
        }),
      );
    } catch (error) {
      failOperation(operation, error);
    }
  };

  const chooseSource = async () => {
    if (transport.runtime === "tauri") {
      const operation = nextOperation("open");
      dispatch({ type: "operationStarted", operation });
      try {
        const opened = await transport.openSource();
        if (!opened) {
          dispatch({ type: "operationCanceled", operation });
          return;
        }
        await applyOpenedSource(opened);
      } catch (error) {
        failOperation(operation, error);
      }
    } else {
      fileInputRef.current?.click();
    }
  };

  const recoverWorkspace = () => {
    const source = state.source?.reference;
    if (source && !state.dirty) {
      void refreshSource(source);
      return;
    }
    dispatch({ type: "recovered" });
  };

  const selectTemplate = (templateId: string | null) => {
    const source = state.source?.reference;
    if (!source || state.dirty) {
      return;
    }
    dispatch({ type: "templateSelected", templateId });
    void runOperation("validate", templateId);
  };

  const activateDiagnostic = (
    diagnostic: WorkspaceState["diagnostics"][number],
  ) => {
    dispatch({
      type: "diagnosticActivated",
      diagnosticId: diagnostic.id,
      line: diagnostic.line,
    });
    if (diagnostic.line === null) {
      return;
    }
    const range = lineSelectionRange(state.editorText, diagnostic.line);
    if (!range) {
      return;
    }
    editorRef.current?.focus();
    editorRef.current?.setSelectionRange(range.start, range.end);
  };

  const resizeFromPointer = (
    side: "outline" | "preview",
    event: ReactPointerEvent<HTMLDivElement>,
  ) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    const startX = event.clientX;
    const startOutline = state.outlineWidth;
    const startPreview = state.previewWidth;
    const target = event.currentTarget;
    const move = (moveEvent: PointerEvent) => {
      const delta = moveEvent.clientX - startX;
      dispatch({
        type: "panelsResized",
        outlineWidth: side === "outline" ? startOutline + delta : startOutline,
        previewWidth: side === "preview" ? startPreview - delta : startPreview,
      });
    };
    const stop = () => {
      target.removeEventListener("pointermove", move);
      target.removeEventListener("pointerup", stop);
    };
    target.addEventListener("pointermove", move);
    target.addEventListener("pointerup", stop);
  };

  return (
    <WorkbenchShell
      state={state}
      actions={actions}
      runtime={transport.runtime}
      capabilities={transport.capabilities}
      statusTitle={statusTitle}
      statusDetail={statusDetail}
      editorRef={editorRef}
      fileInputRef={fileInputRef}
      onChooseSource={() => void chooseSource()}
      onFileSelected={(file) => void openFile(file)}
      onSave={() => void saveSource()}
      onValidate={() => void runOperation("validate")}
      onBuild={() => void runOperation("build")}
      onRecover={recoverWorkspace}
      onTemplateSelected={selectTemplate}
      onDiagnosticFilterChanged={(filter) =>
        dispatch({ type: "diagnosticFilterChanged", filter })
      }
      onDiagnosticActivated={activateDiagnostic}
      onEdit={(text) => dispatch({ type: "textEdited", text })}
      onMobilePanelSelected={(panel) =>
        dispatch({ type: "mobilePanelSelected", panel })
      }
      onPanelsResized={(outlineWidth, previewWidth) =>
        dispatch({ type: "panelsResized", outlineWidth, previewWidth })
      }
      onResizePointer={resizeFromPointer}
    />
  );
}
