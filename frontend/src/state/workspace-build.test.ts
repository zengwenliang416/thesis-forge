import {
  createInitialWorkspaceState,
  reduceWorkspaceState,
  selectWorkspaceActions,
  type WorkspaceState,
} from "./workspace";
import {
  DEFAULT_DOCX_FILENAME,
  DEFAULT_SOURCE_FILENAME,
} from "../transport/constants";

const build = { kind: "build" as const, generation: 2 };

function populated(): WorkspaceState {
  return {
    ...createInitialWorkspaceState(),
    status: "populated",
    source: {
      kind: "desktop",
      name: DEFAULT_SOURCE_FILENAME,
      writable: true,
    },
  };
}

describe("workspace build lifecycle", () => {
  it("defaults to live layout and switches there when a publish build starts", () => {
    let state: WorkspaceState = {
      ...populated(),
      previewMode: "structure" as const,
    };

    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: build,
    });

    expect(state.previewMode).toBe("final-layout");
  });

  it("keeps the previous PDF visible while refreshing and rejects stale results", () => {
    let state: WorkspaceState = {
      ...populated(),
      contentRevision: 4,
      finalPreview: {
        status: "ready",
        descriptor: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "previous.preview.pdf",
        },
        bytes: new Uint8Array([37, 80, 68, 70, 45]),
        message: null,
        revision: 3,
        requestKey: null,
      },
    };

    state = reduceWorkspaceState(state, {
      type: "livePreviewStarted",
      requestKey: "live-preview:2:4",
      revision: 4,
    });
    expect(state.finalPreview.status).toBe("building");
    expect(state.finalPreview.bytes).not.toBeNull();

    state = reduceWorkspaceState(state, {
      type: "livePreviewBuildSucceeded",
      requestKey: "live-preview:1:3",
      revision: 3,
      descriptor: {
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "stale.preview.pdf",
      },
    });
    expect(state.finalPreview.descriptor?.fileName).toBe(
      "previous.preview.pdf",
    );

    state = reduceWorkspaceState(state, {
      type: "livePreviewBuildSucceeded",
      requestKey: "live-preview:2:4",
      revision: 4,
      descriptor: {
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "current.preview.pdf",
      },
    });
    state = reduceWorkspaceState(state, {
      type: "finalPreviewResolved",
      requestKey: "live-preview:2:4",
      bytes: new Uint8Array([37, 80, 68, 70, 45, 49]),
      descriptor: {
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "current.preview.pdf",
      },
    });

    expect(state.finalPreview.status).toBe("ready");
    expect(state.finalPreview.descriptor?.fileName).toBe(
      "current.preview.pdf",
    );
  });

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
        name: DEFAULT_DOCX_FILENAME,
        finalPreview: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "document.preview.pdf",
        },
      },
    });
    expect(state.output?.name).toBe(DEFAULT_DOCX_FILENAME);
    expect(state.finalPreview.status).toBe("building");
    expect(state.status).toBe("populated");
    expect(state.operation).toBeNull();

    const stale = reduceWorkspaceState(state, {
      type: "buildSucceeded",
      operation: { kind: "build", generation: 1 },
      output: { kind: "desktop", name: "stale.docx" },
    });
    expect(stale.output?.name).toBe(DEFAULT_DOCX_FILENAME);
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
        name: DEFAULT_DOCX_FILENAME,
        finalPreview: {
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "document.preview.pdf",
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
      output: { kind: "desktop", name: DEFAULT_DOCX_FILENAME },
    });

    expect(state.output?.name).toBe(DEFAULT_DOCX_FILENAME);
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
