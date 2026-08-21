import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { createInitialWorkspaceState } from "../state/workspace";
import type { WorkspaceActions, WorkspaceState } from "../state/workspace";
import { ProductBar } from "./ProductBar";

const noActions: WorkspaceActions = {
  canOpen: true,
  canEdit: false,
  canSave: false,
  canSaveAs: false,
  canDownload: false,
  canValidate: false,
  canBuild: false,
  canCancel: false,
};

const projectState: WorkspaceState = {
  ...createInitialWorkspaceState(),
  status: "populated" as const,
  project: {
    id: "proj-1",
    root: "/home/alice/thesis",
    manifestPath: "/home/alice/thesis/thesisforge.yaml",
    name: "毕业论文",
  },
  source: {
    kind: "desktop" as const,
    name: "thesis.md",
    writable: true,
  },
};

function renderProductBar(
  state: WorkspaceState,
  overrides: Partial<Parameters<typeof ProductBar>[0]> = {},
) {
  const props = {
    state,
    actions: noActions,
    fileInputRef: createRef<HTMLInputElement>(),
    onChooseSource: () => undefined,
    onFileSelected: () => undefined,
    onSave: () => undefined,
    onValidate: () => undefined,
    onBuild: () => undefined,
    onCancel: () => undefined,
    ...overrides,
  };
  render(<ProductBar {...props} />);
  return props;
}

describe("ProductBar project opening", () => {
  it("exposes the open action under the project accessible name", () => {
    renderProductBar(createInitialWorkspaceState());

    expect(
      screen.getByRole("button", { name: "打开 ThesisForge 项目" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "打开 Markdown 文稿" }),
    ).toBeNull();
  });

  it("targets project manifests in the hidden file input", () => {
    const { container } = render(
      <ProductBar
        state={createInitialWorkspaceState()}
        actions={noActions}
        fileInputRef={createRef<HTMLInputElement>()}
        onChooseSource={() => undefined}
        onFileSelected={() => undefined}
        onSave={() => undefined}
        onValidate={() => undefined}
        onBuild={() => undefined}
        onCancel={() => undefined}
      />,
    );

    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();
    expect(input).toHaveAttribute("accept", ".yaml,.yml,text/yaml");
    expect(input?.getAttribute("accept")).not.toContain(".md");
    expect(input?.getAttribute("accept")).not.toContain("markdown");
  });

  it("shows the project fallback identity when nothing is loaded", () => {
    renderProductBar(createInitialWorkspaceState());

    expect(screen.getByText("尚未打开项目")).toBeVisible();
    expect(screen.getByText("保存快照已同步")).toBeVisible();
  });

  it("shows the project display name and active source when a project is loaded", () => {
    renderProductBar(projectState);

    expect(screen.getByText("毕业论文")).toBeVisible();
    expect(
      screen.getByText("活动源：thesis.md · 保存快照已同步"),
    ).toBeVisible();
  });

  it("keeps showing the source name when only a source is loaded", () => {
    renderProductBar({ ...projectState, project: null });

    expect(screen.getByText("thesis.md")).toBeVisible();
    expect(screen.getByText("保存快照已同步")).toBeVisible();
    expect(screen.queryByText(/活动源：/)).toBeNull();
  });

  it("keeps the dirty sync text alongside the project identity", () => {
    renderProductBar({ ...projectState, dirty: true });

    expect(screen.getByText("毕业论文")).toBeVisible();
    expect(
      screen.getByText("活动源：thesis.md · 有未保存修改"),
    ).toBeVisible();
  });

  it("routes manifest selection through onFileSelected and the open button through onChooseSource", async () => {
    const user = userEvent.setup();
    const onFileSelected = vi.fn();
    const onChooseSource = vi.fn();
    const fileInputRef = createRef<HTMLInputElement>();
    renderProductBar(createInitialWorkspaceState(), {
      fileInputRef,
      onFileSelected,
      onChooseSource,
    });

    const manifest = new File(["name: demo"], "thesisforge.yaml", {
      type: "text/yaml",
    });
    await user.upload(fileInputRef.current as HTMLInputElement, manifest);
    expect(onFileSelected).toHaveBeenCalledTimes(1);
    expect(onFileSelected).toHaveBeenCalledWith(manifest);

    await user.click(
      screen.getByRole("button", { name: "打开 ThesisForge 项目" }),
    );
    expect(onChooseSource).toHaveBeenCalledTimes(1);
  });

  it("keeps save/validate/build disabled when actions disallow them", () => {
    renderProductBar(projectState);

    expect(screen.getByRole("button", { name: "保存文稿" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "验证论文" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
  });
});
