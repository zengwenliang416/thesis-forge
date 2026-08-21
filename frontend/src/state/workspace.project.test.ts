import {
  createInitialWorkspaceState,
  reduceWorkspaceState,
  selectWorkspaceActions,
  type WorkspaceProject,
  type WorkspaceSource,
} from "./workspace";

const project: WorkspaceProject = {
  id: "proj-1",
  root: "/home/user/thesis",
  manifestPath: "/home/user/thesis/thesisforge.yaml",
  name: "学士学位论文",
};

const desktopSource: WorkspaceSource = {
  kind: "desktop",
  name: "thesis.md",
  writable: true,
};

const readOnlySource: WorkspaceSource = {
  kind: "desktop",
  name: "thesis.md",
  writable: false,
};

describe("workspace project state", () => {
  it("starts without a project", () => {
    expect(createInitialWorkspaceState().project).toBeNull();
  });

  it("populates project identity and resets stale session state on projectOpened", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "sourceOpened",
      source: desktopSource,
      text: "# Stale\n",
    });
    state = reduceWorkspaceState(state, {
      type: "templateSelected",
      templateId: "bachelor-base",
    });
    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "validate", generation: 1 },
    });
    state = reduceWorkspaceState(state, {
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
    });
    state = reduceWorkspaceState(state, {
      type: "operationSucceeded",
      operation: { kind: "validate", generation: 1 },
    });
    const revisionBefore = state.contentRevision;

    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });

    expect(state.project).toEqual(project);
    expect(state.source).toEqual(desktopSource);
    expect(state.savedText).toBe("# 论文\n");
    expect(state.editorText).toBe("# 论文\n");
    expect(state.status).toBe("populated");
    expect(state.dirty).toBe(false);
    expect(state.diagnostics).toEqual([]);
    expect(state.output).toBeNull();
    expect(state.templateId).toBeNull();
    expect(state.contentRevision).toBe(revisionBefore + 1);
  });

  it("derives populated permissions from the loaded project state", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });

    expect(selectWorkspaceActions(state)).toMatchObject({
      canOpen: true,
      canEdit: true,
      canSave: false,
      canSaveAs: true,
      canValidate: true,
      canBuild: true,
    });
  });

  it("enables save and blocks build once the project text is dirty", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });
    state = reduceWorkspaceState(state, {
      type: "textEdited",
      text: "# 论文\n\n修改。\n",
    });

    expect(state.status).toBe("dirty");
    expect(selectWorkspaceActions(state)).toMatchObject({
      canSave: true,
      canSaveAs: true,
      canBuild: false,
    });
  });

  it("keeps save disabled for a read-only project source", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: readOnlySource,
      text: "# 论文\n",
    });
    state = reduceWorkspaceState(state, {
      type: "textEdited",
      text: "# 论文\n\n修改。\n",
    });

    expect(state.status).toBe("dirty");
    expect(selectWorkspaceActions(state).canSave).toBe(false);
  });

  it("blocks build only while the project has fatal diagnostics", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });
    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "validate", generation: 1 },
    });
    state = reduceWorkspaceState(state, {
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
    });
    state = reduceWorkspaceState(state, {
      type: "operationSucceeded",
      operation: { kind: "validate", generation: 1 },
    });

    expect(state.project).toEqual(project);
    expect(selectWorkspaceActions(state).canBuild).toBe(false);

    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "validate", generation: 2 },
    });
    state = reduceWorkspaceState(state, {
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
    });
    state = reduceWorkspaceState(state, {
      type: "operationSucceeded",
      operation: { kind: "validate", generation: 2 },
    });

    expect(selectWorkspaceActions(state).canBuild).toBe(true);
  });

  it("retains project identity after a successful save", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });
    state = reduceWorkspaceState(state, {
      type: "textEdited",
      text: "# 论文\n\n修改。\n",
    });
    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "save", generation: 1 },
    });
    state = reduceWorkspaceState(state, {
      type: "saveSucceeded",
      operation: { kind: "save", generation: 1 },
    });

    expect(state.status).toBe("populated");
    expect(state.dirty).toBe(false);
    expect(state.project).toEqual(project);
  });

  it("clears project identity when a bare source is opened", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });
    state = reduceWorkspaceState(state, {
      type: "sourceOpened",
      source: desktopSource,
      text: "# 其他文稿\n",
    });

    expect(state.project).toBeNull();
    expect(state.source).toEqual(desktopSource);
    expect(state.status).toBe("populated");
  });

  it("keeps project identity and editor text after a permission failure", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });
    state = reduceWorkspaceState(state, {
      type: "textEdited",
      text: "# 论文\n\n修改。\n",
    });
    state = reduceWorkspaceState(state, {
      type: "operationStarted",
      operation: { kind: "save", generation: 1 },
    });
    state = reduceWorkspaceState(state, {
      type: "operationFailed",
      operation: { kind: "save", generation: 1 },
      message: "read only",
      permission: true,
    });

    expect(state.status).toBe("permission");
    expect(state.project).toEqual(project);
    expect(state.editorText).toBe("# 论文\n\n修改。\n");
    expect(selectWorkspaceActions(state).canEdit).toBe(true);
  });

  it("exposes the project name as display identity", () => {
    let state = createInitialWorkspaceState();
    state = reduceWorkspaceState(state, {
      type: "projectOpened",
      project,
      source: desktopSource,
      text: "# 论文\n",
    });

    expect(state.project?.name).toBe("学士学位论文");
  });
});
