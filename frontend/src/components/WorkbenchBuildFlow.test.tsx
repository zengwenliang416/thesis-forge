import { render, screen } from "@testing-library/react";
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
    runBuild,
  };
}

describe("Workbench build flow", () => {
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
});
