import type { OperationKind, SourceKind, SourceRef } from "../transport/dto";

export type WorkspaceStatus =
  | "empty"
  | "loading"
  | "populated"
  | "dirty"
  | "error"
  | "disabled"
  | "permission"
  | "canceled";

export interface OperationToken {
  kind: OperationKind;
  generation: number;
}

export interface WorkspaceSource {
  kind: SourceKind;
  name: string;
  writable: boolean;
  reference?: SourceRef;
}

export interface WorkspaceState {
  status: WorkspaceStatus;
  source: WorkspaceSource | null;
  savedText: string;
  editorText: string;
  dirty: boolean;
  operation: OperationToken | null;
  errorMessage: string | null;
  mobilePanel: "outline" | "editor" | "preview" | "diagnostics";
  outlineWidth: number;
  previewWidth: number;
}

export interface WorkspaceActions {
  canOpen: boolean;
  canEdit: boolean;
  canSave: boolean;
  canSaveAs: boolean;
  canDownload: boolean;
  canValidate: boolean;
  canBuild: boolean;
  canCancel: boolean;
}

export type WorkspaceEvent =
  | { type: "sourceOpened"; source: WorkspaceSource; text: string }
  | { type: "textEdited"; text: string }
  | { type: "operationStarted"; operation: OperationToken }
  | { type: "saveSucceeded"; operation: OperationToken }
  | { type: "operationSucceeded"; operation: OperationToken }
  | {
      type: "operationFailed";
      operation: OperationToken;
      message: string;
      permission?: boolean;
    }
  | { type: "operationCanceled"; operation: OperationToken }
  | { type: "recovered" }
  | {
      type: "mobilePanelSelected";
      panel: WorkspaceState["mobilePanel"];
    }
  | {
      type: "panelsResized";
      outlineWidth: number;
      previewWidth: number;
    };

export function createInitialWorkspaceState(): WorkspaceState {
  return {
    status: "empty",
    source: null,
    savedText: "",
    editorText: "",
    dirty: false,
    operation: null,
    errorMessage: null,
    mobilePanel: "editor",
    outlineWidth: 260,
    previewWidth: 430,
  };
}

function isCurrent(state: WorkspaceState, operation: OperationToken) {
  return (
    state.operation?.kind === operation.kind &&
    state.operation.generation === operation.generation
  );
}

export function reduceWorkspaceState(
  state: WorkspaceState,
  event: WorkspaceEvent,
): WorkspaceState {
  switch (event.type) {
    case "sourceOpened":
      return {
        ...state,
        status: "populated",
        source: event.source,
        savedText: event.text,
        editorText: event.text,
        dirty: false,
        operation: null,
        errorMessage: null,
      };
    case "textEdited": {
      const dirty = event.text !== state.savedText;
      return {
        ...state,
        status: dirty ? "dirty" : "populated",
        editorText: event.text,
        dirty,
        operation: null,
        errorMessage: null,
      };
    }
    case "operationStarted":
      return {
        ...state,
        status: "loading",
        operation: event.operation,
        errorMessage: null,
      };
    case "saveSucceeded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: "populated",
        savedText: state.editorText,
        dirty: false,
        operation: null,
        errorMessage: null,
      };
    case "operationSucceeded":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: state.dirty ? "dirty" : state.source ? "populated" : "empty",
        operation: null,
        errorMessage: null,
      };
    case "operationFailed":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: event.permission ? "permission" : "error",
        operation: null,
        errorMessage: event.message,
      };
    case "operationCanceled":
      if (!isCurrent(state, event.operation)) {
        return state;
      }
      return {
        ...state,
        status: "canceled",
        operation: null,
        errorMessage: null,
      };
    case "recovered":
      return {
        ...state,
        status: state.dirty ? "dirty" : state.source ? "populated" : "empty",
        operation: null,
        errorMessage: null,
      };
    case "mobilePanelSelected":
      return { ...state, mobilePanel: event.panel };
    case "panelsResized":
      return {
        ...state,
        outlineWidth: Math.min(380, Math.max(210, event.outlineWidth)),
        previewWidth: Math.min(620, Math.max(340, event.previewWidth)),
      };
  }
}

const NONE: WorkspaceActions = {
  canOpen: false,
  canEdit: false,
  canSave: false,
  canSaveAs: false,
  canDownload: false,
  canValidate: false,
  canBuild: false,
  canCancel: false,
};

export function selectWorkspaceActions(state: WorkspaceState): WorkspaceActions {
  if (state.status === "loading") {
    return {
      ...NONE,
      canCancel:
        state.operation?.kind !== "save" &&
        state.operation?.kind !== "download" &&
        state.operation?.kind !== "refresh",
    };
  }
  if (state.status === "empty") {
    return { ...NONE, canOpen: true };
  }
  if (state.status === "dirty") {
    return {
      ...NONE,
      canOpen: true,
      canEdit: true,
      canSave: state.source?.writable ?? false,
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind === "web-upload",
    };
  }
  if (state.status === "populated") {
    return {
      ...NONE,
      canOpen: true,
      canEdit: true,
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind.startsWith("web-") ?? false,
      canValidate: true,
      canBuild: true,
    };
  }
  if (
    state.status === "error" ||
    state.status === "permission" ||
    state.status === "canceled"
  ) {
    return {
      ...NONE,
      canOpen: true,
      canEdit: state.source !== null,
      canSave: state.dirty && (state.source?.writable ?? false),
      canSaveAs: state.source?.kind === "desktop",
      canDownload: state.source?.kind === "web-upload",
    };
  }
  return NONE;
}
