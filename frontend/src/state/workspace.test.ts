import fixture from "../../../tests/fixtures/workspace-state-v1.json";
import {
  createInitialWorkspaceState,
  reduceWorkspaceState,
  selectWorkspaceActions,
  type WorkspaceEvent,
  type WorkspaceState,
} from "./workspace";

describe("workspace state parity", () => {
  it("matches the shared desktop source lifecycle fixture", () => {
    let state = createInitialWorkspaceState();

    for (const step of fixture.cases[0].steps) {
      state = reduceWorkspaceState(state, step.event as WorkspaceEvent);
      expect({
        status: state.status,
        sourceKind: state.source?.kind ?? null,
        sourceName: state.source?.name ?? null,
        savedText: state.savedText,
        editorText: state.editorText,
        dirty: state.dirty,
        operation: state.operation?.kind ?? null,
        actions: selectWorkspaceActions(state),
      }).toEqual(step.expected);
    }
  });

  it("ignores stale operation completions", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "inspect", generation: 2 },
    });
    state = reduceWorkspaceState(state, {
      type: "operationFailed",
      operation: { kind: "inspect", generation: 1 },
      message: "stale",
    });

    expect(state.status).toBe("loading");
    expect(state.errorMessage).toBeNull();
  });

  it("keeps dirty save actions available after a permission failure", () => {
    let state: WorkspaceState = {
      ...createInitialWorkspaceState(),
      status: "dirty" as const,
      source: {
        kind: "desktop" as const,
        name: "thesis.md",
        writable: true,
      },
      savedText: "# Saved\n",
      editorText: "# Changed\n",
      dirty: true,
      operation: { kind: "save" as const, generation: 1 },
    };

    state = reduceWorkspaceState(state, {
      type: "operationFailed",
      operation: { kind: "save", generation: 1 },
      message: "read only",
      permission: true,
    });

    expect(state.status).toBe("permission");
    expect(state.editorText).toBe("# Changed\n");
    expect(selectWorkspaceActions(state)).toMatchObject({
      canOpen: true,
      canEdit: true,
      canSave: true,
      canValidate: false,
      canBuild: false,
    });
  });
});
