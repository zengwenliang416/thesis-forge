import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WorkbenchApp } from "./WorkbenchApp";
import { createInitialWorkspaceState } from "../state/workspace";
import type {
  OpenedProject,
  WorkbenchTransport,
} from "../transport/WorkbenchTransport";
import type { BuildEvent, BuildReport } from "../transport/buildEvents";
import { PROTOCOL_VERSION, type CommandEnvelope } from "../transport/dto";
import previewFixture from "../../../tests/fixtures/preview-workbench-v1.json";

const previewResult = {
  ...previewFixture,
  diagnostics: [],
};

const projectAIdentity = {
  id: "thesis-alpha",
  root: "/Users/test/thesis-alpha",
  manifestPath: "/Users/test/thesis-alpha/thesisforge.yaml",
};

const projectBIdentity = {
  id: "thesis-beta",
  root: "/Users/test/thesis-beta",
  manifestPath: "/Users/test/thesis-beta/thesisforge.yaml",
};

const projectA: OpenedProject = {
  project: projectAIdentity,
  source: {
    kind: "desktop",
    path: "/Users/test/thesis-alpha/thesis.md",
    fileName: "thesis.md",
  },
  text: "# 绪论\n",
};

const webProject: OpenedProject = {
  project: projectAIdentity,
  source: {
    kind: "web-workspace",
    workspaceId: "b".repeat(32),
    fileName: "thesis.md",
  },
  text: "# 网页文稿\n",
};

const projectB: OpenedProject = {
  project: projectBIdentity,
  source: {
    kind: "desktop",
    path: "/Users/test/thesis-beta/draft.md",
    fileName: "draft.md",
  },
  text: "# 另一篇\n",
};

const warningDiagnostic = {
  severity: "warning" as const,
  code: "heading-level-jump",
  message: "标题层级从 H1 跳到 H3",
  line: 3,
  target: "H1->H3",
  details: { previous_level: 1, current_level: 3 },
};

const warningReportDiagnostic: BuildReport["diagnostics"][number] = {
  id: "diag-alpha-1",
  severity: "warning",
  category: "semantic",
  code: "TF-SEMANTIC-HEADING-001",
  stage: "validate",
  message: "标题层级从 H1 跳到 H3",
  source: {
    file: "thesis.md",
    startLine: 3,
    startColumn: 1,
    endLine: 3,
    endColumn: 8,
  },
  target: "H1->H3",
  suggestion: null,
  relatedLocations: [],
  details: {},
};

const finalPreviewMethods = {
  resolveFinalPreview: async () =>
    new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d]),
  pickFinalPreview: async () => null,
};

function desktopTransport(
  overrides: Partial<WorkbenchTransport>,
): WorkbenchTransport {
  return {
    ...finalPreviewMethods,
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
    ...overrides,
  };
}

function previewDispatch(result: Record<string, unknown> = previewResult) {
  return vi.fn().mockResolvedValue({
    protocol: PROTOCOL_VERSION,
    requestId: "preview-1",
    ok: true,
    result,
  });
}

function completedEvent(
  requestId: string,
  output: BuildReport["output"],
  intent: BuildReport["intent"] = "publish",
  diagnostics: BuildReport["diagnostics"] = [],
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
      diagnostics,
      logs: [],
      output,
    },
  };
}

describe("WorkbenchApp project flow", () => {
  it("opens a desktop project and refreshes with the typed project identity", async () => {
    const user = userEvent.setup();
    const dispatch = previewDispatch();
    render(
      <WorkbenchApp
        transport={desktopTransport({
          openProject: async () => projectA,
          dispatch,
        })}
        initialState={createInitialWorkspaceState()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );

    expect(await screen.findByText("thesis-alpha")).toBeVisible();
    expect(
      screen.getByText("活动源：thesis.md · 文档已保存"),
    ).toBeVisible();
    expect(dispatch).toHaveBeenCalledTimes(1);
    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: projectA.source,
          templateId: null,
          project: projectAIdentity,
        },
      }),
    );
  });

  it("ends canceled without an error when the project picker is dismissed", async () => {
    const user = userEvent.setup();
    render(
      <WorkbenchApp
        transport={desktopTransport({ openProject: async () => null })}
        initialState={createInitialWorkspaceState()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );

    expect(await screen.findByText("操作已取消")).toBeVisible();
    expect(screen.queryByText("文档操作失败")).toBeNull();
    expect(screen.getByText("尚未打开项目")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    ).toBeEnabled();
  });

  it("surfaces project picker failures through the existing failure path", async () => {
    const user = userEvent.setup();
    render(
      <WorkbenchApp
        transport={desktopTransport({
          openProject: async () => {
            throw new Error("无法读取 ThesisForge 项目");
          },
        })}
        initialState={createInitialWorkspaceState()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );

    expect(await screen.findByText("无法读取 ThesisForge 项目")).toBeVisible();
    expect(screen.getByText("文档操作失败")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    ).toBeEnabled();
  });

  it("fails explicitly when the desktop runtime lacks openProject", async () => {
    const user = userEvent.setup();
    render(
      <WorkbenchApp
        transport={desktopTransport({})}
        initialState={createInitialWorkspaceState()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );

    expect(
      await screen.findByText("当前运行时不支持打开 Markdown 或 DocForge 项目。"),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    ).toBeEnabled();
  });

  it("sends the project identity with validate requests", async () => {
    const user = userEvent.setup();
    const dispatch = previewDispatch();
    render(
      <WorkbenchApp
        transport={desktopTransport({
          openProject: async () => projectA,
          dispatch,
        })}
        initialState={createInitialWorkspaceState()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );
    await screen.findByText("文档、模板与预览已同步");

    await user.click(screen.getByRole("button", { name: "检查文档" }));

    expect(dispatch).toHaveBeenCalledTimes(2);
    expect(dispatch).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: projectA.source,
          templateId: null,
          project: projectAIdentity,
        },
      }),
    );
  });

  it("sends the project identity with publish build requests", async () => {
    const user = userEvent.setup();
    const requests: CommandEnvelope[] = [];
    render(
      <WorkbenchApp
        transport={desktopTransport({
          openProject: async () => projectA,
          dispatch: previewDispatch(),
          runBuild: async (request, onEvent) => {
            requests.push(request);
            onEvent(completedEvent(request.requestId, null));
          },
        })}
        initialState={createInitialWorkspaceState()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );
    await screen.findByText("文档、模板与预览已同步");

    await user.click(screen.getByRole("button", { name: "生成 DOCX" }));

    expect(requests).toHaveLength(1);
    expect(requests[0]?.operation).toBe("build");
    expect(requests[0]?.payload).toEqual({
      source: projectA.source,
      templateId: null,
      project: projectAIdentity,
      intent: "publish",
      output: {
        kind: "desktop",
        path: "/Users/test/thesis-alpha/thesis.docx",
        fileName: "thesis.docx",
      },
    });
  });

  it("sends the project identity and editor snapshot with save requests", async () => {
    const user = userEvent.setup();
    const dispatch = vi
      .fn()
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-1",
        ok: true,
        result: previewResult,
      })
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "save-2",
        ok: true,
        result: {},
      })
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-3",
        ok: true,
        result: previewResult,
      });
    render(
      <WorkbenchApp
        transport={desktopTransport({
          openProject: async () => projectA,
          dispatch,
        })}
        initialState={createInitialWorkspaceState()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );
    await screen.findByText("文档、模板与预览已同步");

    await user.type(
      screen.getByRole("textbox", { name: "Markdown 文档内容" }),
      "新增内容",
    );
    await user.click(screen.getByRole("button", { name: "保存文档" }));

    expect(dispatch).toHaveBeenCalledTimes(3);
    expect(dispatch).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        operation: "save",
        payload: {
          source: projectA.source,
          text: "# 绪论\n新增内容",
          project: projectAIdentity,
        },
      }),
    );
    expect(dispatch).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: projectA.source,
          templateId: null,
          project: projectAIdentity,
        },
      }),
    );
    expect(await screen.findByText("文档、模板与预览已同步")).toBeVisible();
  });

  it("sends the project identity and editor snapshot with live-preview requests", async () => {
    const user = userEvent.setup();
    const requests: CommandEnvelope[] = [];
    render(
      <WorkbenchApp
        transport={desktopTransport({
          openProject: async () => projectA,
          dispatch: previewDispatch(),
          runBuild: async (request, onEvent) => {
            requests.push(request);
            onEvent(completedEvent(request.requestId, null, "live-preview"));
          },
          prepareLivePreviewOutput: async () => ({
            kind: "desktop",
            path: "/tmp/thesis-alpha.live.docx",
            fileName: "thesis-alpha.live.docx",
          }),
          discardLivePreviewOutput: async () => undefined,
        })}
        initialState={createInitialWorkspaceState()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );
    await screen.findByText("文档、模板与预览已同步");

    await user.click(screen.getByRole("button", { name: "立即刷新预览" }));

    expect(
      await screen.findByText("Microsoft Word PDF 未生成"),
    ).toBeVisible();
    expect(requests).toHaveLength(1);
    expect(requests[0]?.operation).toBe("build");
    expect(requests[0]?.payload).toEqual({
      source: projectA.source,
      output: {
        kind: "desktop",
        path: "/tmp/thesis-alpha.live.docx",
        fileName: "thesis-alpha.live.docx",
      },
      templateId: null,
      text: "# 绪论\n",
      intent: "live-preview",
      project: projectAIdentity,
    });
  });

  it("clears diagnostics, output and final preview when switching projects", async () => {
    vi.stubGlobal(
      "URL",
      Object.assign(URL, {
        createObjectURL: vi.fn(() => "blob:project-preview"),
        revokeObjectURL: vi.fn(),
      }),
    );
    try {
      const user = userEvent.setup();
      const dispatch = vi
        .fn()
        .mockResolvedValueOnce({
          protocol: PROTOCOL_VERSION,
          requestId: "preview-1",
          ok: true,
          result: { ...previewFixture, diagnostics: [warningDiagnostic] },
        })
        .mockResolvedValueOnce({
          protocol: PROTOCOL_VERSION,
          requestId: "preview-2",
          ok: true,
          result: previewResult,
        });
      const openProject = vi
        .fn()
        .mockResolvedValueOnce(projectA)
        .mockResolvedValueOnce(projectB);
      render(
        <WorkbenchApp
          transport={desktopTransport({
            openProject,
            dispatch,
            runBuild: async (request, onEvent) => {
              onEvent(
                completedEvent(
                  request.requestId,
                  {
                    docxPath: "/Users/test/thesis-alpha/thesis.docx",
                    pdfPath: "/Users/test/thesis-alpha/thesis.pdf",
                    previewStale: false,
                    successfulBuildId: request.requestId,
                    finalPreview: {
                      engine: "libreoffice",
                      label: "LibreOffice PDF",
                      fileName: "thesis.preview.pdf",
                      authorizationId: "a".repeat(32),
                    },
                  },
                  "publish",
                  [warningReportDiagnostic],
                ),
              );
            },
          })}
          initialState={createInitialWorkspaceState()}
        />,
      );

      await user.click(
        screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
      );
      expect(await screen.findByText("thesis-alpha")).toBeVisible();
      expect(await screen.findByText("标题层级从 H1 跳到 H3")).toBeVisible();

      await user.click(screen.getByRole("button", { name: "生成 DOCX" }));
      expect(await screen.findByText("thesis.docx")).toBeVisible();
      expect(await screen.findByText("当前 Word 预览")).toBeVisible();
      expect(screen.getByText("LibreOffice PDF")).toBeVisible();
      expect(screen.getByText("标题层级从 H1 跳到 H3")).toBeVisible();

      await user.click(
        screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
      );

      expect(await screen.findByText("thesis-beta")).toBeVisible();
      expect(
        screen.getByText("活动源：draft.md · 文档已保存"),
      ).toBeVisible();
      expect(screen.queryByText("thesis-alpha")).toBeNull();
      expect(screen.queryByText("标题层级从 H1 跳到 H3")).toBeNull();
      expect(screen.getByText("尚无诊断")).toBeVisible();
      expect(screen.queryByText("thesis.docx")).toBeNull();
      expect(screen.getByText("准备生成 DOCX · 桌面")).toBeVisible();
      expect(screen.queryByText("LibreOffice PDF")).toBeNull();
      expect(screen.queryByText("当前 Word 预览")).toBeNull();
      expect(screen.getByText("未生成")).toBeVisible();
      expect(dispatch).toHaveBeenLastCalledWith(
        expect.objectContaining({
          operation: "preview",
          payload: {
            source: projectB.source,
            templateId: null,
            project: projectBIdentity,
          },
        }),
      );
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("opens a manifest-backed Web project from exactly one manifest and Markdown file", async () => {
    const user = userEvent.setup();
    const dispatch = previewDispatch();
    const openProject = vi.fn().mockResolvedValue(webProject);
    const openSource = vi.fn().mockResolvedValue(null);
    const webTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "web",
      capabilities: {
        nativePaths: false,
        saveWorkspace: true,
        saveAs: false,
        download: true,
      },
      openSource,
      openProject,
      dispatch,
    };
    const { container } = render(
      <WorkbenchApp
        transport={webTransport}
        initialState={createInitialWorkspaceState()}
      />,
    );
    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();

    const manifest = new File(
      ["schema: thesisforge.project.v2\n"],
      "thesisforge.yaml",
      { type: "text/yaml" },
    );
    const source = new File(["# 网页文稿\n"], "thesis.md", {
      type: "text/markdown",
    });
    await user.upload(input as HTMLInputElement, [manifest, source]);

    expect(await screen.findByText("文档、模板与预览已同步")).toBeVisible();
    expect(screen.getByText("thesis-alpha")).toBeVisible();
    expect(
      screen.getByText("活动源：thesis.md · 文档已保存"),
    ).toBeVisible();
    expect(openSource).not.toHaveBeenCalled();
    expect(openProject).toHaveBeenCalledTimes(1);
    expect(openProject).toHaveBeenCalledWith({
      manifest: {
        fileName: "thesisforge.yaml",
        text: "schema: thesisforge.project.v2\n",
      },
      source: {
        fileName: "thesis.md",
        text: "# 网页文稿\n",
      },
    });
    expect(dispatch).toHaveBeenCalledTimes(1);
    expect(dispatch).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: {
            kind: "web-workspace",
            workspaceId: "b".repeat(32),
            fileName: "thesis.md",
          },
          templateId: null,
          project: projectAIdentity,
        },
      }),
    );
  });

  it("rejects incomplete browser selections without an openSource fallback", async () => {
    const user = userEvent.setup();
    const openProject = vi.fn().mockResolvedValue(webProject);
    const openSource = vi.fn().mockResolvedValue(null);
    const webTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "web",
      capabilities: {
        nativePaths: false,
        saveWorkspace: true,
        saveAs: false,
        download: true,
      },
      openSource,
      openProject,
      dispatch: previewDispatch(),
    };
    const { container } = render(
      <WorkbenchApp
        transport={webTransport}
        initialState={createInitialWorkspaceState()}
      />,
    );
    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();

    await user.upload(
      input as HTMLInputElement,
      new File(["# 独立文稿\n"], "thesis.md", { type: "text/markdown" }),
    );

    expect(
      await screen.findByText("请选择一个 thesisforge.yaml 和一个 Markdown 文件。"),
    ).toBeVisible();
    expect(openProject).not.toHaveBeenCalled();
    expect(openSource).not.toHaveBeenCalled();
  });
});
