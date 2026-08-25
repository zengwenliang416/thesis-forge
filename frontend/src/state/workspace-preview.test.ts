import fixture from "../../../tests/fixtures/preview-workbench-v1.json";
import {
  createInitialWorkspaceState,
  reduceWorkspaceState,
  type WorkspaceEvent,
  type WorkspaceState,
} from "./workspace";

describe("workspace preview state", () => {
  it("stores outline and preview only for the current operation", () => {
    let state: WorkspaceState = {
      ...createInitialWorkspaceState(),
      status: "loading",
      operation: { kind: "refresh", generation: 2 },
    };

    state = reduceWorkspaceState(
      state,
      {
        type: "presentationLoaded",
        operation: { kind: "refresh", generation: 1 },
        outline: fixture.outline,
        preview: fixture.preview,
      } as unknown as WorkspaceEvent,
    );
    expect(state.outline).toEqual([]);
    expect(state.preview.status).toBe("empty");

    state = reduceWorkspaceState(
      state,
      {
        type: "presentationLoaded",
        operation: { kind: "refresh", generation: 2 },
        outline: fixture.outline,
        preview: fixture.preview,
      } as unknown as WorkspaceEvent,
    );
    expect(state.outline).toEqual(fixture.outline);
    expect(state.preview).toEqual(fixture.preview);
  });

  it("shares one active selection across outline, preview, and editor line", () => {
    let state = {
      ...createInitialWorkspaceState(),
      status: "populated" as const,
      source: {
        kind: "desktop" as const,
        name: "thesis.md",
        writable: true,
      },
      outline: fixture.outline,
      preview: fixture.preview,
    } as WorkspaceState;

    state = reduceWorkspaceState(
      state,
      {
        type: "contentActivated",
        selectionId: "fig:arch",
        line: 12,
      } as unknown as WorkspaceEvent,
    );

    expect(state.activeSelectionId).toBe("fig:arch");
    expect(state.mobilePanel).toBe("editor");
  });

  it("keeps the last saved preview visible while the editor is dirty", () => {
    const state = reduceWorkspaceState(
      {
        ...createInitialWorkspaceState(),
        status: "populated",
        source: {
          kind: "desktop",
          name: "thesis.md",
          writable: true,
        },
        savedText: "# Saved\n",
        editorText: "# Saved\n",
        outline: fixture.outline,
        preview: fixture.preview,
      } as WorkspaceState,
      { type: "textEdited", text: "# Changed\n" },
    );

    expect(state.status).toBe("dirty");
    expect(state.outline).toEqual(fixture.outline);
    expect(state.preview).toEqual(fixture.preview);
  });

  it("marks a ready final preview stale on template change and clears it for a new source", () => {
    let state = {
      ...createInitialWorkspaceState(),
      status: "populated" as const,
      source: {
        kind: "desktop" as const,
        name: "thesis.md",
        writable: true,
      },
      finalPreview: {
        status: "ready" as const,
        descriptor: {
          engine: "microsoft-word" as const,
          label: "Microsoft Word PDF" as const,
          fileName: "thesis.pdf",
          authorizationId: "a".repeat(32),
        },
        bytes: new Uint8Array([37, 80, 68, 70, 45]),
        message: null,
        revision: 0,
        requestKey: null,
      },
    } as WorkspaceState;

    state = reduceWorkspaceState(state, {
      type: "templateSelected",
      templateId: "hut-master-2026",
    });
    expect(state.finalPreview.status).toBe("stale");
    expect(state.finalPreview.bytes).not.toBeNull();

    state = reduceWorkspaceState(state, {
      type: "sourceOpened",
      source: {
        kind: "desktop",
        name: "other.md",
        writable: true,
      },
      text: "# Other\n",
    });
    expect(state.finalPreview.status).toBe("empty");
    expect(state.finalPreview.bytes).toBeNull();
  });

  it("accepts only the current Office PDF selection request", () => {
    let state = reduceWorkspaceState(
      {
        ...createInitialWorkspaceState(),
        status: "populated",
        source: {
          kind: "desktop",
          name: "thesis.md",
          writable: true,
        },
      },
      { type: "finalPreviewSelectionStarted", requestKey: "selection:2" },
    );

    state = reduceWorkspaceState(state, {
      type: "finalPreviewSelected",
      requestKey: "selection:1",
      descriptor: {
        engine: "microsoft-word",
        label: "Microsoft Word PDF",
        fileName: "old.pdf",
        authorizationId: "b".repeat(32),
      },
      bytes: new Uint8Array([1]),
    });
    expect(state.finalPreview.status).toBe("empty");

    state = reduceWorkspaceState(state, {
      type: "finalPreviewSelected",
      requestKey: "selection:2",
      descriptor: {
        engine: "microsoft-word",
        label: "Microsoft Word PDF",
        fileName: "current.pdf",
        authorizationId: "c".repeat(32),
      },
      bytes: new Uint8Array([37, 80, 68, 70, 45]),
    });
    expect(state.finalPreview.status).toBe("ready");
    expect(state.finalPreview.descriptor?.fileName).toBe("current.pdf");
  });

  it("keeps an existing preview visible when replacement selection fails", () => {
    let state = reduceWorkspaceState(
      {
        ...createInitialWorkspaceState(),
        finalPreview: {
          status: "ready",
          descriptor: {
            engine: "microsoft-word",
            label: "Microsoft Word PDF",
            fileName: "current.pdf",
            authorizationId: "d".repeat(32),
          },
          bytes: new Uint8Array([37, 80, 68, 70, 45]),
          message: null,
          revision: 0,
          requestKey: null,
        },
      },
      { type: "finalPreviewSelectionStarted", requestKey: "selection:3" },
    );

    state = reduceWorkspaceState(state, {
      type: "finalPreviewSelectionFailed",
      requestKey: "selection:3",
      message: "文件已损坏",
    });

    expect(state.finalPreview.status).toBe("ready");
    expect(state.finalPreview.bytes).not.toBeNull();
    expect(state.finalPreview.message).toContain("文件已损坏");
  });
});
