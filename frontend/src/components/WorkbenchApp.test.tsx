import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WorkbenchApp } from "./WorkbenchApp";
import { createInitialWorkspaceState } from "../state/workspace";
import type { WorkbenchTransport } from "../transport/WorkbenchTransport";
import { PROTOCOL_VERSION } from "../transport/dto";
import previewFixture from "../../../tests/fixtures/preview-workbench-v1.json";

const previewResult = {
  ...previewFixture,
  diagnostics: [],
};

const finalPreviewMethods = {
  resolveFinalPreview: async () =>
    new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d]),
  pickFinalPreview: async () => null,
};

const transport: WorkbenchTransport = {
  ...finalPreviewMethods,
  runtime: "web",
  capabilities: {
    nativePaths: false,
    saveWorkspace: true,
    saveAs: false,
    download: true,
  },
  openSource: async () => null,
  dispatch: async () => {
    throw new Error("not used by shell tests");
  },
};

describe("WorkbenchApp", () => {
  it("renders the approved zh-CN workbench regions and empty state", () => {
    render(
      <WorkbenchApp
        transport={transport}
        initialState={createInitialWorkspaceState()}
      />,
    );

    expect(screen.getByText("ThesisForge")).toBeVisible();
    expect(screen.getByRole("button", { name: "打开 Markdown 文稿" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "保存文稿" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "验证论文" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
    expect(screen.getByRole("complementary", { name: "论文大纲" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Markdown 编辑器" })).toBeVisible();
    expect(
      screen.getByRole("region", { name: "论文最终版式预览" }),
    ).toBeVisible();
    expect(screen.getByRole("region", { name: "诊断结果" })).toBeVisible();
    expect(screen.getByLabelText("学校模板")).toBeDisabled();
    expect(screen.getByRole("status", { name: "构建进度" })).toBeVisible();
    expect(screen.getByRole("status", { name: "输出结果" })).toBeVisible();
    expect(screen.getByText("当前工作区没有 Markdown 文稿")).toBeVisible();
  });

  it("supports focus shortcuts without calling a runtime adapter directly", async () => {
    const user = userEvent.setup();
    render(
      <WorkbenchApp
        transport={transport}
        initialState={createInitialWorkspaceState()}
      />,
    );

    await user.keyboard("{Control>}k{/Control}");
    expect(screen.getByRole("textbox", { name: "Markdown 文稿内容" })).toHaveFocus();

    await user.keyboard("{Control>}b{/Control}");
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
  });

  it("switches one visible panel at the mobile breakpoint", async () => {
    const user = userEvent.setup();
    window.matchMedia = (query) =>
      ({
        matches: query.includes("max-width"),
        media: query,
        onchange: null,
        addListener: () => undefined,
        removeListener: () => undefined,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        dispatchEvent: () => true,
      }) as MediaQueryList;

    render(
      <WorkbenchApp
        transport={transport}
        initialState={createInitialWorkspaceState()}
      />,
    );
    await user.click(screen.getByRole("tab", { name: "诊断" }));

    expect(screen.getByRole("tab", { name: "诊断" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("region", { name: "诊断结果" })).toHaveAttribute(
      "data-mobile-active",
      "true",
    );
  });

  it("lets keyboard users resize desktop panels", async () => {
    const user = userEvent.setup();
    render(
      <WorkbenchApp
        transport={transport}
        initialState={createInitialWorkspaceState()}
      />,
    );
    const separator = screen.getByRole("separator", { name: "调整大纲宽度" });

    separator.focus();
    expect(separator).toHaveFocus();
    expect(separator).toHaveAttribute("aria-valuenow", "260");
    await user.keyboard("{ArrowRight}");

    expect(separator).toHaveAttribute("aria-valuenow", "276");
  });

  it("routes build intent through WorkbenchTransport", async () => {
    const user = userEvent.setup();
    const dispatch = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "build-1",
      ok: true,
      result: { output: { kind: "desktop", name: "thesis.docx" } },
    });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => null,
      dispatch,
    };
    const initialState = {
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
      templateId: "bachelor-base",
    };

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.click(screen.getByRole("button", { name: "构建 DOCX" }));

    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        protocol: PROTOCOL_VERSION,
        operation: "build",
        payload: expect.objectContaining({
          source: initialState.source.reference,
          templateId: "bachelor-base",
        }),
      }),
    );
  });

  it("saves dirty desktop text and refreshes the saved snapshot", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi
      .fn()
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "save-1",
        ok: true,
        result: { source: { kind: "desktop", name: "thesis.md" } },
      })
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-2",
        ok: true,
        result: previewResult,
      });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => null,
      dispatch: dispatchCommand,
    };
    const initialState = {
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

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.type(
      screen.getByRole("textbox", { name: "Markdown 文稿内容" }),
      "新增内容",
    );
    await user.click(screen.getByRole("button", { name: "保存文稿" }));

    expect(dispatchCommand).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        operation: "save",
        payload: {
          source: initialState.source.reference,
          text: "# 绪论\n新增内容",
        },
      }),
    );
    expect(dispatchCommand).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ operation: "preview" }),
    );
    expect(screen.getByText("文稿、模板与预览已同步")).toBeVisible();
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeEnabled();
  });

  it("routes Ctrl+S through the same explicit save flow", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "request-1",
      ok: true,
      result: {},
    });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => null,
      dispatch: dispatchCommand,
    };
    const initialState = {
      ...createInitialWorkspaceState(),
      status: "dirty" as const,
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
      savedText: "# Saved\n",
      editorText: "# Changed\n",
      dirty: true,
    };

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.keyboard("{Control>}s{/Control}");

    expect(dispatchCommand).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: "save",
        payload: expect.objectContaining({ text: "# Changed\n" }),
      }),
    );
  });

  it("keeps dirty text recoverable when save fails", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "save-1",
      ok: false,
      error: {
        kind: "permission",
        message: "目标文件不可写",
      },
    });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => null,
      dispatch: dispatchCommand,
    };
    const initialState = {
      ...createInitialWorkspaceState(),
      status: "dirty" as const,
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
      savedText: "# Saved\n",
      editorText: "# Changed\n",
      dirty: true,
    };

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.click(screen.getByRole("button", { name: "保存文稿" }));

    expect(screen.getByText("目标文件不可写")).toBeVisible();
    expect(screen.getByRole("button", { name: "保存文稿" })).toBeEnabled();
    expect(screen.getByRole("textbox", { name: "Markdown 文稿内容" })).toHaveValue(
      "# Changed\n",
    );
  });

  it("reports source-picker failures without losing the open action", async () => {
    const user = userEvent.setup();
    const failingTransport: WorkbenchTransport = {
      ...transport,
      runtime: "tauri",
      openSource: async () => {
        throw new Error("无法读取 Markdown 文稿");
      },
    };

    render(
      <WorkbenchApp
        transport={failingTransport}
        initialState={createInitialWorkspaceState()}
      />,
    );
    await user.click(screen.getByRole("button", { name: "打开 Markdown 文稿" }));

    expect(screen.getByText("无法读取 Markdown 文稿")).toBeVisible();
    expect(screen.getByRole("button", { name: "打开 Markdown 文稿" })).toBeEnabled();
  });

  it("keeps Web build output inside the opaque workspace", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "build-1",
      ok: true,
      result: {},
    });
    const webTransport: WorkbenchTransport = {
      ...transport,
      dispatch: dispatchCommand,
    };
    const initialState = {
      ...createInitialWorkspaceState(),
      status: "populated" as const,
      source: {
        kind: "web-workspace" as const,
        name: "thesis.md",
        writable: true,
        reference: {
          kind: "web-workspace" as const,
          workspaceId: "a".repeat(32),
          fileName: "thesis.md",
        },
      },
      savedText: "# 绪论\n",
      editorText: "# 绪论\n",
    };

    render(
      <WorkbenchApp
        transport={webTransport}
        initialState={initialState}
      />,
    );
    await user.click(screen.getByRole("button", { name: "构建 DOCX" }));

    expect(dispatchCommand).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: "build",
        payload: expect.objectContaining({
          output: {
            kind: "web-download",
            workspaceId: "a".repeat(32),
            fileName: "thesis.docx",
          },
        }),
      }),
    );
  });

  it("retries refresh before re-enabling build after a post-save failure", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi
      .fn()
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "save-1",
        ok: true,
        result: {},
      })
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-2",
        ok: false,
        error: { kind: "transport", message: "inspection unavailable" },
      })
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-3",
        ok: true,
        result: previewResult,
      });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => null,
      dispatch: dispatchCommand,
    };
    const initialState = {
      ...createInitialWorkspaceState(),
      status: "dirty" as const,
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
      savedText: "# Saved\n",
      editorText: "# Changed\n",
      dirty: true,
    };

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.click(screen.getByRole("button", { name: "保存文稿" }));
    expect(await screen.findByText("inspection unavailable")).toBeVisible();
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "恢复工作区" }));

    expect(dispatchCommand).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({ operation: "preview" }),
    );
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeEnabled();
  });

  it("revalidates the saved source with the selected school template", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "preview-1",
      ok: true,
      result: previewResult,
    });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => null,
      dispatch: dispatchCommand,
    };
    const initialState = {
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

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.selectOptions(
      screen.getByLabelText("学校模板"),
      "example-university-2026",
    );

    expect(dispatchCommand).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: initialState.source.reference,
          templateId: "example-university-2026",
        },
      }),
    );
  });

  it("filters diagnostics and activates a source-linked editor line", async () => {
    const user = userEvent.setup();
    const initialState = {
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
      savedText: "# 第一行\n第二行\n第三行\n",
      editorText: "# 第一行\n第二行\n第三行\n",
      diagnostics: [
        {
          id: "missing-reference:2:fig:missing:0",
          severity: "error" as const,
          code: "missing-reference",
          message: "引用目标不存在：fig:missing",
          line: 2,
          target: "fig:missing",
          details: {},
        },
        {
          id: "heading-level-jump:3:H1->H3:1",
          severity: "warning" as const,
          code: "heading-level-jump",
          message: "标题层级从 H1 跳到 H3",
          line: 3,
          target: "H1->H3",
          details: {},
        },
      ],
      diagnosticFilter: "all" as const,
      activeDiagnosticId: null,
    };

    render(<WorkbenchApp transport={transport} initialState={initialState} />);

    expect(screen.getByRole("button", { name: "全部 2" })).toBeVisible();
    expect(screen.getByRole("button", { name: "错误 1" })).toBeVisible();
    expect(screen.getByRole("button", { name: "警告 1" })).toBeVisible();
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
    expect(screen.getByText("存在 1 个错误诊断，构建已禁用。")).toBeVisible();

    await user.click(screen.getByRole("button", { name: "警告 1" }));
    expect(screen.queryByText("引用目标不存在：fig:missing")).not.toBeInTheDocument();
    expect(screen.getByText("标题层级从 H1 跳到 H3")).toBeVisible();

    const diagnostic = screen.getByRole("button", { name: /第 3 行/ });
    diagnostic.focus();
    await user.keyboard("{Enter}");
    const editor = screen.getByRole("textbox", {
      name: "Markdown 文稿内容",
    }) as HTMLTextAreaElement;
    expect(editor).toHaveFocus();
    expect(editor.selectionStart).toBe(10);
    expect(editor.selectionEnd).toBe(13);
  });

  it("activates a source-linked diagnostic with a pointer click", async () => {
    const user = userEvent.setup();
    const initialState = {
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
      savedText: "# 第一行\n第二行\n第三行\n",
      editorText: "# 第一行\n第二行\n第三行\n",
      diagnostics: [
        {
          id: "heading-level-jump:3:H1->H3:0",
          severity: "warning" as const,
          code: "heading-level-jump",
          message: "标题层级从 H1 跳到 H3",
          line: 3,
          target: "H1->H3",
          details: {},
        },
      ],
    };

    render(<WorkbenchApp transport={transport} initialState={initialState} />);
    await user.click(screen.getByRole("button", { name: /第 3 行/ }));

    const editor = screen.getByRole("textbox", {
      name: "Markdown 文稿内容",
    }) as HTMLTextAreaElement;
    expect(editor).toHaveFocus();
    expect(editor.selectionStart).toBe(10);
    expect(editor.selectionEnd).toBe(13);
  });

  it("renders disabled diagnostic filters until a source is open", () => {
    render(
      <WorkbenchApp
        transport={transport}
        initialState={createInitialWorkspaceState()}
      />,
    );

    for (const name of ["全部 0", "错误 0", "警告 0", "提示 0"]) {
      expect(screen.getByRole("button", { name })).toBeDisabled();
    }
  });

  it("activates a no-line diagnostic without moving editor focus", async () => {
    const user = userEvent.setup();
    const initialState = {
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
      diagnostics: [
        {
          id: "missing-template:0:template:0",
          severity: "error" as const,
          code: "missing-template",
          message: "找不到模板：template",
          line: null,
          target: "template",
          details: {},
        },
      ],
      diagnosticFilter: "all" as const,
      activeDiagnosticId: null,
    };

    render(<WorkbenchApp transport={transport} initialState={initialState} />);
    const diagnostic = screen.getByRole("button", { name: /无行号/ });
    diagnostic.focus();
    await user.keyboard("{Enter}");

    expect(diagnostic).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("textbox", { name: "Markdown 文稿内容" }),
    ).not.toHaveFocus();
  });

  it("does not carry an old explicit template into a newly opened source", async () => {
    const user = userEvent.setup();
    const dispatchCommand = vi
      .fn()
      .mockResolvedValueOnce({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-1",
        ok: true,
        result: previewResult,
      });
    const desktopTransport: WorkbenchTransport = {
      ...finalPreviewMethods,
      runtime: "tauri",
      capabilities: {
        nativePaths: true,
        saveWorkspace: false,
        saveAs: true,
        download: false,
      },
      openSource: async () => ({
        source: {
          kind: "desktop",
          path: "/Users/test/new.md",
          fileName: "new.md",
        },
        text: "# 新文稿\n",
      }),
      dispatch: dispatchCommand,
    };
    const initialState = {
      ...createInitialWorkspaceState(),
      status: "populated" as const,
      source: {
        kind: "desktop" as const,
        name: "old.md",
        writable: true,
        reference: {
          kind: "desktop" as const,
          path: "/Users/test/old.md",
          fileName: "old.md",
        },
      },
      savedText: "# 旧文稿\n",
      editorText: "# 旧文稿\n",
      templateId: "bachelor-base",
    };

    render(
      <WorkbenchApp
        transport={desktopTransport}
        initialState={initialState}
      />,
    );
    await user.click(screen.getByRole("button", { name: "打开 Markdown 文稿" }));

    expect(dispatchCommand).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: {
            kind: "desktop",
            path: "/Users/test/new.md",
            fileName: "new.md",
          },
          templateId: null,
        },
      }),
    );
    expect(screen.getByLabelText("学校模板")).toHaveValue("");
  });
});
