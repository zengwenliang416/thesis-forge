import {
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useEffectEvent,
  useReducer,
  useRef,
} from "react";
import {
  reduceWorkspaceState,
  selectWorkspaceActions,
  type WorkspaceSource,
  type WorkspaceState,
} from "../state/workspace";
import {
  diagnosticSummary,
  presentBuildReportDiagnostics,
  presentDiagnostics,
} from "../state/diagnostics";
import { lineSelectionRange } from "../state/editorNavigation";
import type { ContentSelection } from "../state/preview";
import {
  deriveDocxFileName,
  isMarkdownFileName,
  type OpenedProject,
  type ProjectIdentityRef,
  type WorkbenchTransport,
} from "../transport/WorkbenchTransport";
import type {
  BuildErrorKind,
  BuildEvent,
  BuildOutput,
  BuildReport,
} from "../transport/buildEvents";
import {
  PROTOCOL_VERSION,
  readSerializedPreviewResult,
  readSerializedDiagnostics,
  type CommandOperation,
  type CommandEnvelope,
  type OperationKind,
  type SourceRef,
} from "../transport/dto";
import { MANIFEST_FILENAME } from "../transport/constants";
import { WorkbenchShell } from "./WorkbenchShell";

interface WorkbenchAppProps {
  transport: WorkbenchTransport;
  initialState: WorkspaceState;
}

const statusCopy = {
  empty: [
    "当前工作区没有 Markdown 文档",
    "打开 Markdown 文件或 DocForge 项目开始制作 Word 文档。",
  ],
  loading: ["正在读取文档", "正在同步保存快照、文档结构和 Word 版式。"],
  populated: ["文档、模板与预览已同步", "Microsoft Word 版式与当前编辑内容同步。"],
  dirty: [
    "文档有未保存修改",
    "实时版式会自动更新；正式检查或生成 DOCX 前请先保存。",
  ],
  error: ["文档操作失败", "现有内容已保留，可恢复后重试。"],
  disabled: ["本机 Word 文档生成器尚未启用", "编辑和诊断仍可使用。"],
  permission: ["目标位置不可写", "请选择有权限的位置后重试。"],
  canceled: ["操作已取消", "过期结果不会覆盖当前文档。"],
} satisfies Record<WorkspaceState["status"], [string, string]>;

function reportMessage(report: BuildReport): string {
  if (report.outcome === "canceled") {
    return "构建已取消";
  }
  const primary =
    report.primaryDiagnosticId === null
      ? null
      : report.diagnostics.find(
          (diagnostic) => diagnostic.id === report.primaryDiagnosticId,
        );
  return (
    primary?.message ??
    report.diagnostics[0]?.message ??
    report.logs.at(-1)?.message ??
    "构建失败"
  );
}

function reportErrorKind(report: BuildReport): BuildErrorKind {
  if (report.outcome === "canceled") {
    return "canceled";
  }
  if (report.diagnostics.some((diagnostic) => diagnostic.category === "permission")) {
    return "permission";
  }
  switch (report.failedStage) {
    case "validate":
      return "validation";
    case "compile":
      return "compile";
    case "render":
      return "render";
    case "finalize":
    case "postflight":
    case "preview":
      return "finalize";
    default:
      return "transport";
  }
}

function reportOutput(
  report: BuildReport,
  source: NonNullable<WorkspaceState["source"]>["reference"],
): BuildOutput | null {
  if (report.outcome !== "succeeded" || !report.output || !source) {
    return null;
  }
  const fallback = deriveDocxFileName(source.fileName);
  const pathName = report.output.docxPath?.split(/[\\/]/).at(-1);
  return {
    kind: source.kind === "desktop" ? "desktop" : "web-download",
    name:
      pathName && pathName !== "." && pathName !== ".."
        ? pathName
        : fallback,
    ...(report.output.finalPreview
      ? { finalPreview: report.output.finalPreview }
      : {}),
  };
}

// The command payload carries exactly the {id, root, manifestPath} identity;
// WorkspaceProject adds a display name that must never leak into payloads.
function projectRef(project: ProjectIdentityRef): ProjectIdentityRef {
  return {
    id: project.id,
    root: project.root,
    manifestPath: project.manifestPath,
  };
}

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
  const previewSelectionGenerationRef = useRef(0);
  const buildAbortRef = useRef<AbortController | null>(null);
  const livePreviewAbortRef = useRef<AbortController | null>(null);
  const livePreviewDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const livePreviewAttemptedRevisionRef = useRef<number | null>(null);
  const livePreviewGenerationRef = useRef(0);

  const nextOperation = (kind: OperationKind) => {
    generationRef.current += 1;
    return {
      kind,
      generation: generationRef.current,
    };
  };

  const requestFor = (
    operation: CommandOperation,
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
    project: ProjectIdentityRef | null = state.project,
  ) => {
    if (!source) {
      return;
    }
    const operation = nextOperation("refresh");
    dispatch({ type: "operationStarted", operation });
    try {
      const response = await transport.dispatch(
        requestFor("preview", operation.generation, {
          source,
          templateId,
          ...(project ? { project: projectRef(project) } : {}),
        }),
      );
      if (!response.ok) {
        failOperation(operation, response.error);
        return;
      }
      const presentation = readSerializedPreviewResult(response.result, true);
      if (!presentation) {
        throw new Error("无效的 DocForge transport 响应");
      }
      dispatch({
        type: "diagnosticsLoaded",
        operation,
        diagnostics: presentDiagnostics(
          readSerializedDiagnostics(response.result, true),
        ),
      });
      dispatch({
        type: "presentationLoaded",
        operation,
        outline: presentation.outline,
        preview: presentation.preview,
      });
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
    if (kind === "build") {
      if (livePreviewDebounceRef.current) {
        clearTimeout(livePreviewDebounceRef.current);
        livePreviewDebounceRef.current = null;
      }
      livePreviewAbortRef.current?.abort();
      livePreviewAttemptedRevisionRef.current = state.contentRevision;
    }
    const operation = nextOperation(kind);
    const output =
      kind === "build" && source.kind === "desktop"
        ? {
            kind: "desktop" as const,
            path: deriveDocxFileName(source.path),
            fileName: deriveDocxFileName(source.fileName),
          }
        : kind === "build" && source.kind === "web-workspace"
          ? {
              kind: "web-download" as const,
              workspaceId: source.workspaceId,
              fileName: deriveDocxFileName(source.fileName),
            }
          : undefined;
    const command: CommandOperation = kind === "validate" ? "preview" : kind;
    const request = requestFor(command, operation.generation, {
      source,
      templateId,
      ...(state.project ? { project: projectRef(state.project) } : {}),
      ...(kind === "build" ? { intent: "publish" as const } : {}),
      ...(output ? { output } : {}),
    });
    dispatch({ type: "operationStarted", operation });
    try {
      if (kind === "build" && transport.runBuild) {
        const controller = new AbortController();
        buildAbortRef.current = controller;
        let terminal = false;
        await transport.runBuild(
          request,
          (event: BuildEvent) => {
            if (event.type === "progress") {
              dispatch({
                type: "buildProgressed",
                operation,
                stage: event.stage,
              });
              return;
            }
            terminal = true;
            const report = event.report;
            dispatch({
              type: "diagnosticsLoaded",
              operation,
              diagnostics: presentBuildReportDiagnostics(report.diagnostics),
            });
            if (report.outcome === "canceled") {
              dispatch({ type: "operationCanceled", operation });
              return;
            }
            if (report.outcome === "succeeded") {
              const output = reportOutput(report, source);
              if (output) {
                dispatch({
                  type: "buildSucceeded",
                  operation,
                  output,
                });
                if (output.finalPreview) {
                  const requestKey = `build:${operation.generation}`;
                  void transport
                    .resolveFinalPreview(output.finalPreview)
                    .then((bytes) =>
                      dispatch({
                        type: "finalPreviewResolved",
                        requestKey,
                        bytes,
                        descriptor: output.finalPreview,
                      }),
                    )
                    .catch((error: unknown) =>
                      dispatch({
                        type: "finalPreviewResolutionFailed",
                        requestKey,
                        message:
                          error instanceof Error
                            ? error.message
                            : "最终版式 PDF 读取失败。",
                      }),
                    );
                }
              } else {
                dispatch({ type: "operationSucceeded", operation });
              }
              return;
            }
            dispatch({
              type: "buildFailed",
              operation,
              kind: reportErrorKind(report),
              message: reportMessage(report),
            });
          },
          controller.signal,
        );
        if (!terminal && !controller.signal.aborted) {
          dispatch({
            type: "buildFailed",
            operation,
            kind: "transport",
            message: "构建事件流未返回终态",
          });
        }
        if (buildAbortRef.current === controller) {
          buildAbortRef.current = null;
        }
        return;
      }
      const response = await transport.dispatch(request);
      if (response.ok) {
        if (kind === "validate") {
          const presentation = readSerializedPreviewResult(response.result, true);
          if (!presentation) {
            throw new Error("无效的 DocForge transport 响应");
          }
          dispatch({
            type: "diagnosticsLoaded",
            operation,
            diagnostics: presentDiagnostics(
              readSerializedDiagnostics(response.result, true),
            ),
          });
          dispatch({
            type: "presentationLoaded",
            operation,
            outline: presentation.outline,
            preview: presentation.preview,
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

  const runLivePreview = async ({
    source,
    text,
    templateId,
    revision,
  }: {
    source: NonNullable<WorkspaceState["source"]>["reference"];
    text: string;
    templateId: string | null;
    revision: number;
  }) => {
    if (
      !source ||
      !transport.runBuild ||
      !transport.prepareLivePreviewOutput
    ) {
      return;
    }

    livePreviewAbortRef.current?.abort();
    const controller = new AbortController();
    livePreviewAbortRef.current = controller;
    livePreviewGenerationRef.current += 1;
    const requestKey = `live-preview:${livePreviewGenerationRef.current}:${revision}`;
    let output: CommandEnvelope["payload"]["output"];
    dispatch({ type: "livePreviewStarted", requestKey, revision });

    try {
      output = await transport.prepareLivePreviewOutput(source);
      if (controller.signal.aborted) {
        return;
      }
      const request = requestFor("build", revision, {
        source,
        output,
        templateId,
        text,
        intent: "live-preview",
        ...(state.project ? { project: projectRef(state.project) } : {}),
      });
      request.requestId = requestKey;
      let terminal = false;
      let resolution: Promise<void> | null = null;

      await transport.runBuild(
        request,
        (event: BuildEvent) => {
          if (event.type === "progress") {
            return;
          }
          terminal = true;
          const report = event.report;
          dispatch({
            type: "livePreviewDiagnosticsLoaded",
            requestKey,
            revision,
            diagnostics: presentBuildReportDiagnostics(report.diagnostics),
          });
          if (report.outcome === "succeeded") {
            const descriptor = report.output?.finalPreview ?? null;
            dispatch({
              type: "livePreviewBuildSucceeded",
              requestKey,
              revision,
              descriptor,
            });
            if (!descriptor) {
              return;
            }
            resolution = transport
              .resolveFinalPreview(descriptor)
              .then((bytes) => {
                if (!controller.signal.aborted) {
                  dispatch({
                    type: "finalPreviewResolved",
                    requestKey,
                    bytes,
                    descriptor,
                  });
                }
              })
              .catch((error: unknown) => {
                if (!controller.signal.aborted) {
                  dispatch({
                    type: "finalPreviewResolutionFailed",
                    requestKey,
                    message:
                      error instanceof Error
                        ? error.message
                        : "实时预览 PDF 读取失败。",
                  });
                }
            });
            return;
          }
          if (report.outcome === "canceled") {
            dispatch({
              type: "livePreviewCanceled",
              requestKey,
              revision,
            });
            return;
          }
          if (!controller.signal.aborted) {
            dispatch({
              type: "livePreviewFailed",
              requestKey,
              revision,
              message: reportMessage(report),
            });
          }
        },
        controller.signal,
      );
      await resolution;
      if (!terminal && !controller.signal.aborted) {
        dispatch({
          type: "livePreviewFailed",
          requestKey,
          revision,
          message: "实时预览构建未返回终态",
        });
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        dispatch({
          type: "livePreviewFailed",
          requestKey,
          revision,
          message: error instanceof Error ? error.message : String(error),
        });
      }
    } finally {
      if (output && transport.discardLivePreviewOutput) {
        try {
          await transport.discardLivePreviewOutput(output);
        } catch {
          // Cleanup is best-effort; the runtime still validates every preview path.
        }
      }
      if (livePreviewAbortRef.current === controller) {
        livePreviewAbortRef.current = null;
      }
    }
  };
  const startLivePreviewFromEffect = useEffectEvent(runLivePreview);

  useEffect(() => {
    const source = state.source?.reference;
    if (
      !source ||
      state.operation !== null ||
      !transport.runBuild ||
      !transport.prepareLivePreviewOutput ||
      livePreviewAttemptedRevisionRef.current === state.contentRevision
    ) {
      return;
    }

    livePreviewAbortRef.current?.abort();
    livePreviewDebounceRef.current = setTimeout(() => {
      livePreviewDebounceRef.current = null;
      livePreviewAttemptedRevisionRef.current = state.contentRevision;
      void startLivePreviewFromEffect({
        source,
        text: state.editorText,
        templateId: state.templateId,
        revision: state.contentRevision,
      });
    }, 900);

    return () => {
      if (livePreviewDebounceRef.current) {
        clearTimeout(livePreviewDebounceRef.current);
        livePreviewDebounceRef.current = null;
      }
    };
  }, [
    state.contentRevision,
    state.editorText,
    state.operation,
    state.source,
    state.templateId,
    transport,
  ]);

  useEffect(
    () => () => {
      livePreviewAbortRef.current?.abort();
    },
    [],
  );

  const refreshLivePreview = () => {
    const source = state.source?.reference;
    if (
      !source ||
      !transport.runBuild ||
      !transport.prepareLivePreviewOutput
    ) {
      return;
    }
    if (livePreviewDebounceRef.current) {
      clearTimeout(livePreviewDebounceRef.current);
      livePreviewDebounceRef.current = null;
    }
    livePreviewAttemptedRevisionRef.current = state.contentRevision;
    void runLivePreview({
      source,
      text: state.editorText,
      templateId: state.templateId,
      revision: state.contentRevision,
    });
  };

  const cancelBuild = () => {
    if (state.operation?.kind !== "build") {
      return;
    }
    const operation = state.operation;
    buildAbortRef.current?.abort();
    dispatch({ type: "operationCanceled", operation });
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
          ...(state.project ? { project: projectRef(state.project) } : {}),
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

  const toWorkspaceSource = (source: SourceRef): WorkspaceSource => ({
    kind: source.kind,
    name: source.fileName,
    writable:
      source.kind === "desktop" ||
      (source.kind === "web-workspace" && transport.capabilities.saveWorkspace),
    reference: source,
  });

  const applyOpenedProject = async (opened: OpenedProject) => {
    dispatch({
      type: "projectOpened",
      project: {
        id: opened.project.id,
        root: opened.project.root,
        manifestPath: opened.project.manifestPath,
        name: opened.project.id,
      },
      source: toWorkspaceSource(opened.source),
      text: opened.text,
    });
    // The projectOpened dispatch has not re-rendered yet, so hand the fresh
    // identity to the refresh instead of reading stale closure state.
    await refreshSource(opened.source, null, opened.project);
  };

  const openFile = async (files: File[]) => {
    const operation = nextOperation("open");
    dispatch({ type: "operationStarted", operation });
    try {
      if (!transport.openProject) {
        throw new Error("当前运行时不支持打开 Markdown 或 DocForge 项目。");
      }
      const manifestFiles = files.filter(
        (file) => file.name === MANIFEST_FILENAME,
      );
      const sourceFiles = files.filter((file) =>
        isMarkdownFileName(file.name),
      );
      if (
        files.length !== 2 ||
        manifestFiles.length !== 1 ||
        sourceFiles.length !== 1
      ) {
        throw new Error(
          `请选择一个 ${MANIFEST_FILENAME} 和一个 Markdown 文件。`,
        );
      }
      const opened = await transport.openProject({
        manifest: {
          fileName: manifestFiles[0].name,
          text: await manifestFiles[0].text(),
        },
        source: {
          fileName: sourceFiles[0].name,
          text: await sourceFiles[0].text(),
        },
      });
      if (!opened) {
        dispatch({ type: "operationCanceled", operation });
        return;
      }
      await applyOpenedProject(opened);
    } catch (error) {
      failOperation(operation, error);
    }
  };

  const chooseSource = async () => {
    if (transport.runtime === "tauri") {
      const operation = nextOperation("open");
      dispatch({ type: "operationStarted", operation });
      try {
        if (!transport.openProject) {
          throw new Error("当前运行时不支持打开 Markdown 或 DocForge 项目。");
        }
        const opened = await transport.openProject();
        if (!opened) {
          dispatch({ type: "operationCanceled", operation });
          return;
        }
        await applyOpenedProject(opened);
      } catch (error) {
        failOperation(operation, error);
      }
    } else {
      fileInputRef.current?.click();
    }
  };

  const chooseOfficePdf = async () => {
    if (livePreviewDebounceRef.current) {
      clearTimeout(livePreviewDebounceRef.current);
      livePreviewDebounceRef.current = null;
    }
    livePreviewAbortRef.current?.abort();
    livePreviewAttemptedRevisionRef.current = state.contentRevision;
    previewSelectionGenerationRef.current += 1;
    const requestKey = `selection:${previewSelectionGenerationRef.current}`;
    dispatch({ type: "finalPreviewSelectionStarted", requestKey });
    if (!transport.pickFinalPreview) {
      dispatch({
        type: "finalPreviewSelectionFailed",
        requestKey,
        message: "当前运行时不支持选择本地 Office PDF。",
      });
      return;
    }
    try {
      const selected = await transport.pickFinalPreview();
      if (!selected) {
        dispatch({ type: "finalPreviewSelectionCanceled", requestKey });
        return;
      }
      dispatch({
        type: "finalPreviewSelected",
        requestKey,
        descriptor: selected.descriptor,
        bytes: selected.bytes,
      });
    } catch (error) {
      dispatch({
        type: "finalPreviewSelectionFailed",
        requestKey,
        message:
          error instanceof Error ? error.message : "Office PDF 读取失败。",
      });
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
    focusEditorLine(diagnostic.line);
  };

  const focusEditorLine = (line: number) => {
    const range = lineSelectionRange(state.editorText, line);
    if (!range) {
      return;
    }
    editorRef.current?.focus();
    editorRef.current?.setSelectionRange(range.start, range.end);
  };

  const activateContent = (selection: ContentSelection) => {
    dispatch({
      type: "contentActivated",
      selectionId: selection.selectionId,
      line: selection.line,
    });
    if (selection.line !== null) {
      focusEditorLine(selection.line);
    }
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
      onFileSelected={(files) => void openFile(files)}
      onSave={() => void saveSource()}
      onValidate={() => void runOperation("validate")}
      onBuild={() => void runOperation("build")}
      onCancel={cancelBuild}
      onRecover={recoverWorkspace}
      onTemplateSelected={selectTemplate}
      onDiagnosticFilterChanged={(filter) =>
        dispatch({ type: "diagnosticFilterChanged", filter })
      }
      onDiagnosticActivated={activateDiagnostic}
      onContentActivated={activateContent}
      onPreviewModeChanged={(mode) =>
        dispatch({ type: "previewModeSelected", mode })
      }
      onRefreshFinalPreview={refreshLivePreview}
      onSelectOfficePdf={() => void chooseOfficePdf()}
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
