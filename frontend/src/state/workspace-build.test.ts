import {
  createInitialWorkspaceState,
  reduceWorkspaceState,
  selectWorkspaceActions,
  type WorkspaceState,
} from "./workspace";

const build = { kind: "build" as const, generation: 2 };

function populated(): WorkspaceState {
  return {
    ...createInitialWorkspaceState(),
    status: "populated",
    source: {
      kind: "desktop",
      name: "thesis.md",
      writable: true,
    },
  };
}

describe("workspace build lifecycle", () => {
  it("stores ordered progress and replaces output only on current success", () => {
    let state = reduceWorkspaceState(populated(), {
      type: "operationStarted",
      operation: build,
    });
    state = reduceWorkspaceState(state, {
      type: "buildProgressed",
      operation: build,
      stage: "parse",
    });
    state = reduceWorkspaceState(state, {
      type: "buildProgressed",
      operation: build,
      stage: "validate",
    });
    state = reduceWorkspaceState(state, {
      type: "buildProgressed",
      operation: build,
      stage: "parse",
    });

    expect(state.buildProgress).toEqual(["parse", "validate"]);

    state = reduceWorkspaceState(state, {
      type: "buildSucceeded",
      operation: build,
      output: {
        kind: "desktop",
        name: "thesis.docx",
        finalPreview: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "thesis.preview.pdf",
        },
      },
    });
    expect(state.output?.name).toBe("thesis.docx");
    expect(state.finalPreview.status).toBe("building");
    expect(state.status).toBe("populated");
    expect(state.operation).toBeNull();

    const stale = reduceWorkspaceState(state, {
      type: "buildSucceeded",
      operation: { kind: "build", generation: 1 },
      output: { kind: "desktop", name: "stale.docx" },
    });
    expect(stale.output?.name).toBe("thesis.docx");
  });

  it("binds resolved PDF bytes to the current build revision only", () => {
    let state = reduceWorkspaceState(populated(), {
      type: "operationStarted",
      operation: build,
    });
    state = reduceWorkspaceState(state, {
      type: "buildSucceeded",
      operation: build,
      output: {
        kind: "desktop",
        name: "thesis.docx",
        finalPreview: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "thesis.preview.pdf",
        },
      },
    });
    state = reduceWorkspaceState(state, {
      type: "finalPreviewResolved",
      requestKey: "build:2",
      bytes: new Uint8Array([37, 80, 68, 70, 45]),
    });

    expect(state.finalPreview.status).toBe("ready");
    expect(state.finalPreview.descriptor?.label).toBe("LibreOffice PDF");

    state = reduceWorkspaceState(state, {
      type: "textEdited",
      text: "# Changed\n",
    });
    expect(state.finalPreview.status).toBe("stale");

    state = reduceWorkspaceState(state, {
      type: "finalPreviewResolved",
      requestKey: "build:2",
      bytes: new Uint8Array([1]),
    });
    expect(state.finalPreview.status).toBe("stale");
    expect(state.finalPreview.bytes).toEqual(
      new Uint8Array([37, 80, 68, 70, 45]),
    );
  });

  it("reports automatic PDF unavailability without losing DOCX output", () => {
    let state = reduceWorkspaceState(populated(), {
      type: "operationStarted",
      operation: build,
    });
    state = reduceWorkspaceState(state, {
      type: "buildSucceeded",
      operation: build,
      output: { kind: "desktop", name: "thesis.docx" },
    });

    expect(state.output?.name).toBe("thesis.docx");
    expect(state.finalPreview.status).toBe("unavailable");
    expect(state.finalPreview.message).toContain("DOCX 已生成");
  });

  it("preserves prior output across cancel/error and enables retry", () => {
    let state: WorkspaceState = {
      ...populated(),
      output: { kind: "desktop", name: "previous.docx" },
    };
    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: build,
    });
    state = reduceWorkspaceState(state, {
      type: "operationCanceled",
      operation: build,
    });

    expect(state.status).toBe("canceled");
    expect(state.output).toEqual({ kind: "desktop", name: "previous.docx" });
    expect(selectWorkspaceActions(state).canBuild).toBe(true);

    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "build", generation: 3 },
    });
    state = reduceWorkspaceState(state, {
      type: "buildFailed",
      operation: { kind: "build", generation: 3 },
      kind: "render",
      message: "渲染失败",
    });
    expect(state.output).toEqual({ kind: "desktop", name: "previous.docx" });
    expect(state.buildErrorKind).toBe("render");
    expect(selectWorkspaceActions(state).canBuild).toBe(true);
  });
});
