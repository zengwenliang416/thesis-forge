import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  createInitialWorkspaceState,
  reduceWorkspaceState,
  type WorkspaceState,
} from "../state/workspace";
import { presentBuildReportDiagnostics } from "../state/diagnostics";
import type { WorkbenchTransport } from "../transport/WorkbenchTransport";
import { PROTOCOL_VERSION, type CommandEnvelope } from "../transport/dto";
import type { BuildEvent, BuildReport } from "../transport/buildEvents";
import { WorkbenchApp } from "./WorkbenchApp";

function initialState() {
  return {
    ...createInitialWorkspaceState(),
    status: "populated" as const,
    source: {
      kind: "desktop" as const,
      name: "thesis.md",
      writable: true,
      reference: {
        kind: "desktop" as const,
        path: "/Users/test/thesis.md",
        fileName: "thesis.md",
      },
    },
    savedText: "# 绪论\n",
    editorText: "# 绪论\n",
  };
}

function transport(
  runBuild: (
    request: CommandEnvelope,
    onEvent: (event: BuildEvent) => void,
    signal: AbortSignal,
  ) => Promise<void>,
  overrides: Partial<WorkbenchTransport> = {},
): WorkbenchTransport {
  return {
    runtime: "tauri",
    capabilities: {
      nativePaths: true,
      saveWorkspace: false,
      saveAs: true,
      download: false,
    },
    openSource: async () => null,
    dispatch: async () => {
      throw new Error("unexpected dispatch");
    },
    resolveFinalPreview: async () =>
      new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d]),
    pickFinalPreview: async () => null,
    runBuild,
    ...overrides,
  };
}

function completedEvent(
  requestId: string,
  output: BuildReport["output"],
  intent: BuildReport["intent"] = "publish",
  overrides: Partial<BuildReport> = {},
): BuildEvent {
  return {
    protocol: PROTOCOL_VERSION,
    requestId,
    type: "completed",
    report: {
      schemaVersion: "thesisforge.build-report.v2",
      buildId: requestId,
      intent,
      outcome: "succeeded",
      stages: [{ name: "parse", status: "succeeded" }],
      failedStage: null,
      primaryDiagnosticId: null,
      diagnostics: [],
      logs: [],
      output,
      ...overrides,
    },
  };
}

describe("Workbench build flow", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "URL",
      Object.assign(URL, {
        createObjectURL: vi.fn(() => "blob:built-preview"),
        revokeObjectURL: vi.fn(),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows ordered progress and the successful output", async () => {
    const user = userEvent.setup();
    render(
      <WorkbenchApp
        transport={transport(async (request, onEvent) => {
          for (const stage of ["parse", "validate", "compile", "render", "finalize"] as const) {
            onEvent({
              protocol: PROTOCOL_VERSION,
              requestId: request.requestId,
              type: "progress",
              stage,
            });
          }
          onEvent(
            completedEvent(request.requestId, {
              docxPath: "thesis.docx",
              pdfPath: null,
              previewStale: false,
              successfulBuildId: request.requestId,
            }),
          );
        })}
        initialState={initialState()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "生成 DOCX" }));

    expect(await screen.findByText("thesis.docx")).toBeVisible();
    expect(screen.getByText("构建完成")).toBeVisible();
    expect(screen.getByLabelText("构建进度")).toHaveTextContent(
      "解析验证编译渲染完成",
    );
  });

  it("cancels the active build, preserves output, and exposes retry", async () => {
    const user = userEvent.setup();
    const pending: {
      resolve: (() => void) | null;
      signal: AbortSignal | null;
    } = { resolve: null, signal: null };
    const prior = {
      ...initialState(),
      output: { kind: "desktop" as const, name: "previous.docx" },
    };
    render(
      <WorkbenchApp
        transport={transport(
          async (_request, _onEvent, signal) =>
            new Promise<void>((resolve) => {
              pending.signal = signal;
              pending.resolve = resolve;
            }),
        )}
        initialState={prior}
      />,
    );

    await user.click(screen.getByRole("button", { name: "生成 DOCX" }));
    expect(screen.getByRole("button", { name: "取消构建" })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: "取消构建" }));

    expect(pending.signal?.aborted).toBe(true);
    expect(screen.getByText("操作已取消")).toBeVisible();
    expect(screen.getByText("previous.docx")).toBeVisible();
    expect(screen.getByRole("button", { name: "生成 DOCX" })).toBeEnabled();
    pending.resolve?.();
  });

  it("resolves the current build PDF and renders the final-layout viewer", async () => {
    const user = userEvent.setup();
    const descriptor = {
      engine: "libreoffice" as const,
      label: "LibreOffice PDF" as const,
      fileName: "thesis.preview.pdf",
      authorizationId: "b".repeat(32),
    };
    const resolveFinalPreview = vi
      .fn()
      .mockResolvedValue(new TextEncoder().encode("%PDF-1.7\n"));
    render(
      <WorkbenchApp
        transport={transport(
          async (request, onEvent) => {
            onEvent(
              completedEvent(request.requestId, {
                docxPath: "thesis.docx",
                pdfPath: "thesis.preview.pdf",
                previewStale: false,
                successfulBuildId: request.requestId,
                finalPreview: descriptor,
              }),
            );
          },
          { resolveFinalPreview },
        )}
        initialState={initialState()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "生成 DOCX" }));
    expect(await screen.findByText("LibreOffice PDF")).toBeVisible();
    expect(screen.getByTitle("最终版式 PDF")).toHaveAttribute(
      "src",
      "blob:built-preview",
    );
    expect(resolveFinalPreview).toHaveBeenCalledWith(descriptor);
  });

  it("imports a selected Office PDF without calling a runtime API from the component", async () => {
    const user = userEvent.setup();
    const pickFinalPreview = vi.fn().mockResolvedValue({
      descriptor: {
        engine: "microsoft-word",
        label: "Microsoft Word PDF",
        fileName: "word-export.pdf",
        authorizationId: "c".repeat(32),
      },
      bytes: new TextEncoder().encode("%PDF-1.7\n"),
    });
    render(
      <WorkbenchApp
        transport={transport(async () => undefined, { pickFinalPreview })}
        initialState={initialState()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "选择 Word PDF" }));

    expect(await screen.findByText("Microsoft Word PDF")).toBeVisible();
    expect(screen.getByText("当前 Word 预览")).toBeVisible();
    expect(screen.getByTitle("最终版式 PDF")).toBeVisible();
    expect(pickFinalPreview).toHaveBeenCalledOnce();
  });

  it("keeps the existing PDF visible when selecting a replacement fails", async () => {
    const user = userEvent.setup();
    const pickFinalPreview = vi.fn().mockRejectedValue(new Error("文件已损坏"));
    render(
      <WorkbenchApp
        transport={transport(async () => undefined, { pickFinalPreview })}
        initialState={{
          ...initialState(),
          previewMode: "final-layout",
          finalPreview: {
            status: "ready",
            descriptor: {
              engine: "microsoft-word",
              label: "Microsoft Word PDF",
              fileName: "existing.pdf",
              authorizationId: "d".repeat(32),
            },
            bytes: new TextEncoder().encode("%PDF-1.7\n"),
            message: null,
            revision: 0,
            requestKey: null,
          },
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: "选择 Word PDF" }));

    expect(await screen.findByText(/选择新的 Office PDF 失败/)).toBeVisible();
    expect(screen.getByTitle("最终版式 PDF")).toBeVisible();
    expect(screen.getByText("当前 Word 预览")).toBeVisible();
  });

  it("stores live-preview diagnostics and marks the previous PDF stale on failure", () => {
    let state: WorkspaceState = {
      ...initialState(),
      finalPreview: {
        status: "ready",
        descriptor: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "previous.preview.pdf",
        },
        bytes: new Uint8Array([37, 80, 68, 70, 45]),
        message: null,
        revision: 0,
        requestKey: null,
      },
    };
    const requestKey = "live-preview:1:0";
    const diagnostics = presentBuildReportDiagnostics([
      {
        id: "diag-live-1",
        severity: "error",
        category: "docx",
        code: "TF-DOCX-RENDER-001",
        stage: "render",
        message: "Figure rendering failed.",
        source: {
          file: "thesis.md",
          startLine: 12,
          startColumn: 1,
          endLine: 12,
          endColumn: 20,
        },
        target: "fig:model",
        suggestion: null,
        relatedLocations: [],
        details: { retryable: false, note: null, attempts: 2 },
      },
    ]);

    state = reduceWorkspaceState(state, {
      type: "livePreviewStarted",
      requestKey,
      revision: 0,
    });
    state = reduceWorkspaceState(state, {
      type: "livePreviewDiagnosticsLoaded",
      requestKey,
      revision: 0,
      diagnostics,
    });
    state = reduceWorkspaceState(state, {
      type: "livePreviewFailed",
      requestKey,
      revision: 0,
      message: "Figure rendering failed.",
    });

    expect(state.diagnostics[0]).toMatchObject({
      code: "TF-DOCX-RENDER-001",
      line: 12,
      target: "fig:model",
      details: { retryable: false, note: null, attempts: 2 },
    });
    expect(state.finalPreview.status).toBe("stale");
    expect(state.finalPreview.bytes).not.toBeNull();
    expect(state.finalPreview.requestKey).toBeNull();
  });

  it("ends a canceled live-preview without leaving it building", () => {
    let state: WorkspaceState = {
      ...initialState(),
      finalPreview: {
        status: "ready",
        descriptor: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "previous.preview.pdf",
        },
        bytes: new Uint8Array([37, 80, 68, 70, 45]),
        message: null,
        revision: 0,
        requestKey: null,
      },
    };
    const requestKey = "live-preview:2:0";

    state = reduceWorkspaceState(state, {
      type: "livePreviewStarted",
      requestKey,
      revision: 0,
    });
    state = reduceWorkspaceState(state, {
      type: "livePreviewCanceled",
      requestKey,
      revision: 0,
    });

    expect(state.finalPreview.status).toBe("stale");
    expect(state.finalPreview.bytes).not.toBeNull();
    expect(state.finalPreview.requestKey).toBeNull();
  });

  it("shows live-preview report diagnostics and keeps the prior PDF stale", async () => {
    const user = userEvent.setup();
    const emptyPreview = {
      status: "unavailable" as const,
      descriptor: null,
      bytes: null,
      message: null,
      revision: 0,
      requestKey: null,
    };
    render(
      <WorkbenchApp
        transport={transport(
          async (request, onEvent) => {
            onEvent(
              completedEvent(
                request.requestId,
                {
                  docxPath: null,
                  pdfPath: null,
                  previewStale: true,
                  successfulBuildId: "previous-build",
                },
                "live-preview",
                {
                  outcome: "failed",
                  failedStage: "render",
                  primaryDiagnosticId: "diag-live-1",
                  diagnostics: [
                    {
                      id: "diag-live-1",
                      severity: "error",
                      category: "docx",
                      code: "TF-DOCX-RENDER-001",
                      stage: "render",
                      message: "Figure rendering failed.",
                      source: {
                        file: "thesis.md",
                        startLine: 12,
                        startColumn: 1,
                        endLine: 12,
                        endColumn: 20,
                      },
                      target: "fig:model",
                      suggestion: null,
                      relatedLocations: [],
                      details: { retryable: false, note: null, attempts: 2 },
                    },
                  ],
                },
              ),
            );
          },
          {
            prepareLivePreviewOutput: async () => ({
              kind: "desktop",
              path: "/tmp/live-failure.docx",
              fileName: "live-failure.docx",
            }),
            discardLivePreviewOutput: async () => undefined,
          },
        )}
        initialState={{ ...initialState(), finalPreview: emptyPreview }}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "立即刷新预览" }),
    );

    expect(await screen.findByText("Figure rendering failed.")).toBeVisible();
    expect(screen.getByText("最终预览加载失败")).toBeVisible();
    expect(screen.getByRole("region", { name: "诊断结果" })).toHaveTextContent(
      "fig:model",
    );
  });

  it("ends a canceled live-preview report and keeps the prior PDF stale", async () => {
    const user = userEvent.setup();
    const emptyPreview = {
      status: "unavailable" as const,
      descriptor: null,
      bytes: null,
      message: null,
      revision: 0,
      requestKey: null,
    };
    render(
      <WorkbenchApp
        transport={transport(
          async (request, onEvent) => {
            onEvent(
              completedEvent(
                request.requestId,
                null,
                "live-preview",
                { outcome: "canceled" },
              ),
            );
          },
          {
            prepareLivePreviewOutput: async () => ({
              kind: "desktop",
              path: "/tmp/live-canceled.docx",
              fileName: "live-canceled.docx",
            }),
            discardLivePreviewOutput: async () => undefined,
          },
        )}
        initialState={{ ...initialState(), finalPreview: emptyPreview }}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "立即刷新预览" }),
    );

    expect(await screen.findByText("实时预览已取消。")).toBeVisible();
    expect(screen.getByText("Microsoft Word PDF 未生成")).toBeVisible();
  });

  it("debounces editor snapshots into disposable live PDF builds", async () => {
    vi.useFakeTimers();
    const requests: CommandEnvelope[] = [];
    const abortSignals: AbortSignal[] = [];
    const discardedOutputs: CommandEnvelope["payload"]["output"][] = [];
    const descriptor = {
      engine: "libreoffice" as const,
      label: "LibreOffice PDF" as const,
      fileName: "live.preview.pdf",
      authorizationId: "e".repeat(32),
    };
    const liveTransport = transport(
      async (request, onEvent, signal) => {
        requests.push(request);
        abortSignals.push(signal);
        onEvent(
          completedEvent(
            request.requestId,
            {
              docxPath: "live.docx",
              pdfPath: "live.preview.pdf",
              previewStale: false,
              successfulBuildId: request.requestId,
              finalPreview: descriptor,
            },
            "live-preview",
          ),
        );
        if (requests.length === 1) {
          await new Promise<void>((resolve) => {
            signal.addEventListener("abort", () => resolve(), { once: true });
          });
        }
      },
      {
        prepareLivePreviewOutput: async () => ({
          kind: "desktop",
          path: "/tmp/live.docx",
          fileName: "live.docx",
        }),
        discardLivePreviewOutput: async (output) => {
          discardedOutputs.push(output);
        },
      },
    );
    try {
      render(
        <WorkbenchApp
          transport={liveTransport}
          initialState={initialState()}
        />,
      );

      expect(requests).toHaveLength(0);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(900);
      });
      expect(requests).toHaveLength(1);
      expect(requests[0].payload).toMatchObject({
        intent: "live-preview",
        text: "# 绪论\n",
      });
      expect(screen.getByText("当前 Word 预览")).toBeVisible();

      fireEvent.change(
        screen.getByRole("textbox", { name: "Markdown 文档内容" }),
        { target: { value: "# 绪论\n新增" } },
      );
      await act(async () => {
        await vi.advanceTimersByTimeAsync(899);
      });
      expect(requests).toHaveLength(1);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1);
      });
      expect(requests).toHaveLength(2);
      expect(requests[1].payload.text).toBe("# 绪论\n新增");
      expect(abortSignals[0].aborted).toBe(true);
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(discardedOutputs).toHaveLength(2);
    } finally {
      vi.useRealTimers();
    }
  });
});
