import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { createInitialWorkspaceState } from "../state/workspace";
import { WorkbenchShell } from "./WorkbenchShell";

describe("WorkbenchShell project opening", () => {
  it("passes the browser File[] selection through unchanged", async () => {
    const user = userEvent.setup();
    const fileInputRef = createRef<HTMLInputElement>();
    const onFileSelected = vi.fn();

    render(
      <WorkbenchShell
        state={createInitialWorkspaceState()}
        actions={{
          canOpen: true,
          canEdit: false,
          canSave: false,
          canSaveAs: false,
          canDownload: false,
          canValidate: false,
          canBuild: false,
          canCancel: false,
        }}
        runtime="web"
        capabilities={{
          nativePaths: false,
          saveWorkspace: true,
          saveAs: false,
          download: true,
        }}
        statusTitle="title"
        statusDetail="detail"
        editorRef={createRef<HTMLTextAreaElement>()}
        fileInputRef={fileInputRef}
        onChooseSource={() => undefined}
        onFileSelected={onFileSelected}
        onSave={() => undefined}
        onValidate={() => undefined}
        onBuild={() => undefined}
        onCancel={() => undefined}
        onRecover={() => undefined}
        onTemplateSelected={() => undefined}
        onDiagnosticFilterChanged={() => undefined}
        onDiagnosticActivated={() => undefined}
        onContentActivated={() => undefined}
        onPreviewModeChanged={() => undefined}
        onRefreshFinalPreview={() => undefined}
        onSelectOfficePdf={() => undefined}
        onEdit={() => undefined}
        onMobilePanelSelected={() => undefined}
        onPanelsResized={() => undefined}
        onResizePointer={() => undefined}
      />,
    );

    const manifest = new File(["project: {}"], "thesisforge.yaml", {
      type: "text/yaml",
    });
    const source = new File(["# 绪论\n"], "thesis.md", {
      type: "text/markdown",
    });
    const files = [manifest, source];

    await user.upload(fileInputRef.current as HTMLInputElement, files);

    expect(onFileSelected).toHaveBeenCalledTimes(1);
    expect(onFileSelected).toHaveBeenCalledWith(files);
  });
});
