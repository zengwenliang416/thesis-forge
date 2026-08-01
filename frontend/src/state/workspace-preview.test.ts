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
});
