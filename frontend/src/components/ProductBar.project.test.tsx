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
    manifestPath: "/home/alice/thesis/docforge.yaml",
    name: "毕业论文",
  },
  source: {
    kind: "desktop" as const,
    name: "document.md",
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
    onTemplateSelected: () => undefined,
    ...overrides,
  };
  render(<ProductBar {...props} />);
  return props;
}

describe("ProductBar project opening", () => {
  it("presents the DocForge product and general document commands", () => {
    renderProductBar(createInitialWorkspaceState());

    expect(screen.getByText("DocForge")).toBeVisible();
    expect(screen.getByText("Markdown → Word 文档工坊")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    ).toBeEnabled();
    expect(screen.getByRole("button", { name: "检查文档" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "生成 DOCX" })).toBeDisabled();
    expect(screen.getByLabelText("Word 模板")).toBeDisabled();
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
        onTemplateSelected={() => undefined}
      />,
    );

    const input = container.querySelector('input[type="file"]');
    expect(input).not.toBeNull();
    expect(input).toHaveAttribute(
      "accept",
      ".yaml,.yml,.md,.markdown,text/yaml,text/markdown",
    );
    expect(input).toHaveAttribute("multiple");
  });

  it("shows the project fallback identity when nothing is loaded", () => {
    renderProductBar(createInitialWorkspaceState());

    expect(screen.getByText("尚未打开项目")).toBeVisible();
    expect(screen.getByText("文档已保存")).toBeVisible();
  });

  it("shows the project display name and active source when a project is loaded", () => {
    renderProductBar(projectState);

    expect(screen.getByText("毕业论文")).toBeVisible();
    expect(
      screen.getByText("活动源：document.md · 文档已保存"),
    ).toBeVisible();
  });

  it("keeps showing the source name when only a source is loaded", () => {
    renderProductBar({ ...projectState, project: null });

    expect(screen.getByText("document.md")).toBeVisible();
    expect(screen.getByText("文档已保存")).toBeVisible();
    expect(screen.queryByText(/活动源：/)).toBeNull();
  });

  it("keeps the dirty sync text alongside the project identity", () => {
    renderProductBar({ ...projectState, dirty: true });

    expect(screen.getByText("毕业论文")).toBeVisible();
    expect(
      screen.getByText("活动源：document.md · 有未保存修改"),
    ).toBeVisible();
  });

  it("routes the manifest and Markdown selection through one File[] callback", async () => {
    const user = userEvent.setup();
    const onFileSelected = vi.fn();
    const fileInputRef = createRef<HTMLInputElement>();
    renderProductBar(createInitialWorkspaceState(), {
      fileInputRef,
      onFileSelected,
    });

    const manifest = new File(["name: demo"], "docforge.yaml", {
      type: "text/yaml",
    });
    const source = new File(["# 绪论\n"], "document.MARKDOWN", {
      type: "text/markdown",
    });
    await user.upload(fileInputRef.current as HTMLInputElement, [
      manifest,
      source,
    ]);
    expect(onFileSelected).toHaveBeenCalledTimes(1);
    expect(onFileSelected).toHaveBeenCalledWith([manifest, source]);
  });

  it("routes the project open button through onChooseSource", async () => {
    const user = userEvent.setup();
    const onChooseSource = vi.fn();
    renderProductBar(createInitialWorkspaceState(), { onChooseSource });

    await user.click(
      screen.getByRole("button", { name: "打开 Markdown 或 DocForge 项目" }),
    );

    expect(onChooseSource).toHaveBeenCalledTimes(1);
  });

  it("keeps save/check/build disabled when actions disallow them", () => {
    renderProductBar(projectState);

    expect(screen.getByRole("button", { name: "保存文档" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "检查文档" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "生成 DOCX" })).toBeDisabled();
  });

  it("routes the existing template ID through the command bar callback", async () => {
    const user = userEvent.setup();
    const onTemplateSelected = vi.fn();
    renderProductBar(
      {
        ...projectState,
        source: {
          ...projectState.source!,
          reference: {
            kind: "desktop",
            path: "/home/alice/thesis/document.md",
            fileName: "document.md",
          },
        },
      },
      { onTemplateSelected },
    );

    await user.selectOptions(
      screen.getByLabelText("Word 模板"),
      "example-university-2026",
    );

    expect(onTemplateSelected).toHaveBeenCalledWith(
      "example-university-2026",
    );
  });

  it("shows the selected generic template in the command bar", () => {
    renderProductBar({
      ...projectState,
      templateId: "docforge-standard",
      source: {
        ...projectState.source!,
        reference: {
          kind: "desktop",
          path: "/home/alice/thesis/document.md",
          fileName: "document.md",
        },
      },
    });

    expect(screen.getByLabelText("Word 模板")).toHaveValue("docforge-standard");
    expect(screen.getByRole("option", { name: "DocForge 通用模板" })).toBeVisible();
  });
});
