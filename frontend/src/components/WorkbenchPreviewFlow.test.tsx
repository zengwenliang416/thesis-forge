import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import fixture from "../../../tests/fixtures/preview-workbench-v1.json";
import { createInitialWorkspaceState } from "../state/workspace";
import type { WorkbenchTransport } from "../transport/WorkbenchTransport";
import { PROTOCOL_VERSION } from "../transport/dto";
import type { SerializedPreviewResult } from "../transport/dto";
import { WorkbenchApp } from "./WorkbenchApp";

function desktopTransport(
  dispatch: WorkbenchTransport["dispatch"],
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
    dispatch,
  };
}

describe("Workbench preview flow", () => {
  const presentation = fixture as unknown as SerializedPreviewResult;

  it("refreshes outline, diagnostics, and preview through one preview operation", async () => {
    const user = userEvent.setup();
    const dispatch = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "preview-1",
      ok: true,
      result: {
        ...fixture,
        diagnostics: [],
      },
    });
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
      savedText: "# 绪论 {#chap:intro}\n",
      editorText: "# 绪论 {#chap:intro}\n",
    };

    render(
      <WorkbenchApp
        transport={desktopTransport(dispatch)}
        initialState={initialState}
      />,
    );
    await user.click(screen.getByRole("button", { name: "验证论文" }));

    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: "preview",
        payload: {
          source: initialState.source.reference,
          templateId: null,
        },
      }),
    );
    const outline = await screen.findByRole("complementary", {
      name: "论文大纲",
    });
    expect(
      within(outline).getByRole("button", { name: /绪论.*第 8 行/ }),
    ).toBeVisible();
    expect(screen.getByText("系统架构")).toBeVisible();
  });

  it("updates preview with the selected template and focuses selected source lines", async () => {
    const user = userEvent.setup();
    const dispatch = vi.fn().mockResolvedValue({
      protocol: PROTOCOL_VERSION,
      requestId: "preview-1",
      ok: true,
      result: {
        ...fixture,
        diagnostics: [],
      },
    });
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
      savedText: Array.from({ length: 14 }, (_, index) => `第${index + 1}行`).join(
        "\n",
      ),
      editorText: Array.from(
        { length: 14 },
        (_, index) => `第${index + 1}行`,
      ).join("\n"),
      outline: presentation.outline,
      preview: presentation.preview,
      activeSelectionId: null,
    };

    render(
      <WorkbenchApp
        transport={desktopTransport(dispatch)}
        initialState={initialState}
      />,
    );
    await user.selectOptions(
      screen.getByLabelText("学校模板"),
      "example-university-2026",
    );
    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: "preview",
        payload: expect.objectContaining({
          templateId: "example-university-2026",
        }),
      }),
    );

    await user.click(screen.getByRole("button", { name: /系统架构.*第 12 行/ }));
    const editor = screen.getByRole("textbox", {
      name: "Markdown 文稿内容",
    }) as HTMLTextAreaElement;
    await waitFor(() => expect(editor).toHaveFocus());
    expect(editor.value.slice(editor.selectionStart, editor.selectionEnd)).toBe(
      "第12行",
    );
  });
});
