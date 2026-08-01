import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import fixture from "../../../tests/fixtures/preview-workbench-v1.json";
import { createInitialWorkspaceState } from "../state/workspace";
import type { WorkspaceState } from "../state/workspace";
import type { SerializedPreviewResult } from "../transport/dto";
import { OutlinePanel, PaperPreview } from "./PreviewPanels";

const presentation = fixture as unknown as SerializedPreviewResult;
const readyState: WorkspaceState = {
  ...createInitialWorkspaceState(),
  status: "populated" as const,
  source: {
    kind: "desktop" as const,
    name: "thesis.md",
    writable: true,
  },
  outline: presentation.outline,
  preview: presentation.preview,
  activeSelectionId: null,
};

describe("renderer-neutral preview panels", () => {
  it("renders semantic outline, typed blocks, markers, and pagination disclaimer", () => {
    render(
      <>
        <OutlinePanel state={readyState} onActivated={() => undefined} />
        <PaperPreview state={readyState} onActivated={() => undefined} />
      </>,
    );

    const outline = screen.getByRole("complementary", { name: "论文大纲" });
    expect(
      within(outline).getByRole("button", { name: /绪论.*第 8 行/ }),
    ).toBeVisible();
    expect(screen.getByText("系统结构见")).toBeVisible();
    expect(screen.getAllByText("图 1-1")).toHaveLength(2);
    expect(screen.getByText("系统架构")).toBeVisible();
    expect(screen.getByText("custom-widget")).toBeVisible();
    expect(screen.getByText("暂不支持此结构类型")).toBeVisible();
    expect(screen.getByText("结构预览不代表 Word 最终分页。")).toBeVisible();
    expect(screen.getAllByLabelText("warning heading-level-jump")).not.toHaveLength(0);
  });

  it("activates the same selection from outline and preview by keyboard or pointer", async () => {
    const user = userEvent.setup();
    const activated = vi.fn();
    render(
      <>
        <OutlinePanel state={readyState} onActivated={activated} />
        <PaperPreview state={readyState} onActivated={activated} />
      </>,
    );

    const outlineHeading = within(
      screen.getByRole("complementary", { name: "论文大纲" }),
    ).getByRole("button", { name: /绪论.*第 8 行/ });
    outlineHeading.focus();
    await user.keyboard("{Enter}");
    await user.click(screen.getByRole("button", { name: /系统架构.*第 12 行/ }));

    expect(activated).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({ selectionId: "chap:intro", line: 8 }),
    );
    expect(activated).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ selectionId: "fig:arch", line: 12 }),
    );
  });

  it("renders explicit empty and validation-blocked states", () => {
    const { rerender } = render(
      <PaperPreview
        state={createInitialWorkspaceState()}
        onActivated={() => undefined}
      />,
    );
    expect(screen.getByText("等待载入论文")).toBeVisible();

    rerender(
      <PaperPreview
        state={{
          ...readyState,
          preview: {
            status: "blocked",
            message: "存在 2 个错误诊断，无法生成结构预览。",
            disclaimer: "结构预览不代表 Word 最终分页。",
            blocks: [],
          },
        }}
        onActivated={() => undefined}
      />,
    );
    expect(
      screen.getByText("存在 2 个错误诊断，无法生成结构预览。"),
    ).toBeVisible();
    expect(screen.getByText("结构预览不代表 Word 最终分页。")).toBeVisible();
  });
});
