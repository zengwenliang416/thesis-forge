import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createInitialWorkspaceState } from "../state/workspace";
import type { WorkbenchTransport } from "../transport/WorkbenchTransport";
import { PROTOCOL_VERSION, type CommandEnvelope } from "../transport/dto";
import type { BuildEvent } from "../transport/buildEvents";
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
          onEvent({
            protocol: PROTOCOL_VERSION,
            requestId: request.requestId,
            type: "success",
            result: {
              output: { kind: "desktop", name: "thesis.docx" },
              diagnostics: [],
            },
          });
        })}
        initialState={initialState()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "构建 DOCX" }));

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

    await user.click(screen.getByRole("button", { name: "构建 DOCX" }));
    expect(screen.getByRole("button", { name: "取消构建" })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: "取消构建" }));

    expect(pending.signal?.aborted).toBe(true);
    expect(screen.getByText("操作已取消")).toBeVisible();
    expect(screen.getByText("previous.docx")).toBeVisible();
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeEnabled();
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
            onEvent({
              protocol: PROTOCOL_VERSION,
              requestId: request.requestId,
              type: "success",
              result: {
                output: {
                  kind: "desktop",
                  name: "thesis.docx",
                  finalPreview: descriptor,
                },
                diagnostics: [],
              },
            });
          },
          { resolveFinalPreview },
        )}
        initialState={initialState()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "构建 DOCX" }));
    expect(await screen.findByText("LibreOffice PDF")).toBeVisible();
    expect(screen.getByTitle("最终版式 PDF")).toHaveAttribute(
      "src",
      "blob:built-preview",
    );
    expect(resolveFinalPreview).toHaveBeenCalledWith(descriptor);
  });

  it("imports a selected WPS PDF without calling a runtime API from the component", async () => {
    const user = userEvent.setup();
    const pickFinalPreview = vi.fn().mockResolvedValue({
      descriptor: {
        engine: "wps",
        label: "WPS PDF",
        fileName: "wps-export.pdf",
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

    await user.click(screen.getByRole("button", { name: "选择 WPS PDF" }));

    expect(await screen.findByText("WPS PDF")).toBeVisible();
    expect(screen.getByText("WPS 对照稿")).toBeVisible();
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
              engine: "wps",
              label: "WPS PDF",
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

    await user.click(screen.getByRole("button", { name: "选择 WPS PDF" }));

    expect(await screen.findByText(/选择新的 WPS PDF 失败/)).toBeVisible();
    expect(screen.getByTitle("最终版式 PDF")).toBeVisible();
    expect(screen.getByText("WPS 对照稿")).toBeVisible();
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
        onEvent({
          protocol: PROTOCOL_VERSION,
          requestId: request.requestId,
          type: "success",
          result: {
            output: {
              kind: "desktop",
              name: "live.docx",
              finalPreview: descriptor,
            },
            diagnostics: [],
          },
        });
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
      expect(screen.getByText("当前实时预览")).toBeVisible();

      fireEvent.change(
        screen.getByRole("textbox", { name: "Markdown 文稿内容" }),
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
