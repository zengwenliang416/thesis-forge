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
      output: { kind: "desktop", name: "thesis.docx" },
    });
    expect(state.output).toEqual({ kind: "desktop", name: "thesis.docx" });
    expect(state.status).toBe("populated");
    expect(state.operation).toBeNull();

    const stale = reduceWorkspaceState(state, {
      type: "buildSucceeded",
      operation: { kind: "build", generation: 1 },
      output: { kind: "desktop", name: "stale.docx" },
    });
    expect(stale.output).toEqual({ kind: "desktop", name: "thesis.docx" });
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
