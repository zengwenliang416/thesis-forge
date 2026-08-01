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

  it("stores template and diagnostics while blocking only fatal builds", () => {
    let state: WorkspaceState = {
      ...createInitialWorkspaceState(),
      status: "populated" as const,
      source: {
        kind: "desktop" as const,
        name: "thesis.md",
        writable: true,
      },
    };

    state = reduceWorkspaceState(
      state,
      {
        type: "templateSelected",
        templateId: "bachelor-base",
      } as unknown as WorkspaceEvent,
    );
    state = reduceWorkspaceState(
      state,
      {
        type: "operationStarted",
        operation: { kind: "validate", generation: 1 },
      },
    );
    state = reduceWorkspaceState(
      state,
      {
        type: "diagnosticsLoaded",
        operation: { kind: "validate", generation: 1 },
        diagnostics: [
          {
            id: "missing-template:0:template:0",
            severity: "error",
            code: "missing-template",
            message: "找不到模板：template",
            line: null,
            target: "template",
            details: {},
          },
        ],
      },
    );
    state = reduceWorkspaceState(
      state,
      {
        type: "operationSucceeded",
        operation: { kind: "validate", generation: 1 },
      },
    );

    expect(state.templateId).toBe("bachelor-base");
    expect(state.diagnostics).toHaveLength(1);
    expect(selectWorkspaceActions(state).canBuild).toBe(false);

    state = reduceWorkspaceState(
      state,
      {
        type: "operationStarted",
        operation: { kind: "validate", generation: 2 },
      },
    );
    state = reduceWorkspaceState(
      state,
      {
        type: "diagnosticsLoaded",
        operation: { kind: "validate", generation: 2 },
        diagnostics: [
          {
            id: "heading-level-jump:8:H1->H3:0",
            severity: "warning",
            code: "heading-level-jump",
            message: "标题层级从 H1 跳到 H3",
            line: 8,
            target: "H1->H3",
            details: {},
          },
        ],
      },
    );
    state = reduceWorkspaceState(
      state,
      {
        type: "operationSucceeded",
        operation: { kind: "validate", generation: 2 },
      },
    );

    expect(selectWorkspaceActions(state).canBuild).toBe(true);
  });

  it("ignores diagnostics from an older validation generation", () => {
    let state: WorkspaceState = {
      ...createInitialWorkspaceState(),
      status: "loading" as const,
      operation: { kind: "validate" as const, generation: 2 },
    };

    state = reduceWorkspaceState(state, {
      type: "diagnosticsLoaded",
      operation: { kind: "validate", generation: 1 },
      diagnostics: [
        {
          id: "stale",
          severity: "error",
          code: "missing-template",
          message: "stale",
          line: null,
          target: "template",
          details: {},
        },
      ],
    });

    expect(state.diagnostics).toEqual([]);
    expect(state.operation).toEqual({ kind: "validate", generation: 2 });
  });
});
