import type {
  CommandEnvelope,
  CommandOutputRef,
  CommandResponse,
  RuntimeKind,
  SourceRef,
} from "./dto";
import type { BuildEvent } from "./buildEvents";
import type {
  FinalPreviewDescriptor,
  ResolvedFinalPreview,
} from "./finalPreview";

export interface RuntimeCapabilities {
  nativePaths: boolean;
  saveWorkspace: boolean;
  saveAs: boolean;
  download: boolean;
}

export interface OpenSourceInput {
  fileName: string;
  text: string;
}

export interface OpenedSource {
  source: SourceRef;
  text: string;
}

export interface ProjectIdentityRef {
  id: string;
  root: string;
  manifestPath: string;
}

export interface OpenProjectInput {
  project: ProjectIdentityRef;
  fileName: string;
  text: string;
}

export interface OpenedProject {
  project: ProjectIdentityRef;
  source: SourceRef;
  text: string;
}

export interface WorkbenchTransport {
  readonly runtime: RuntimeKind;
  readonly capabilities: RuntimeCapabilities;
  openSource(input?: OpenSourceInput): Promise<OpenedSource | null>;
  openProject?(input?: OpenProjectInput): Promise<OpenedProject | null>;
  dispatch(request: CommandEnvelope, signal?: AbortSignal): Promise<CommandResponse>;
  runBuild?(
    request: CommandEnvelope,
    onEvent: (event: BuildEvent) => void,
    signal: AbortSignal,
  ): Promise<void>;
  prepareLivePreviewOutput?(
    source: SourceRef,
  ): Promise<CommandOutputRef>;
  discardLivePreviewOutput?(output: CommandOutputRef): Promise<void>;
  resolveFinalPreview(
    descriptor: FinalPreviewDescriptor,
  ): Promise<Uint8Array>;
  pickFinalPreview(): Promise<ResolvedFinalPreview | null>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  return Object.keys(value).every((key) => keys.includes(key));
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

export function readProjectIdentity(value: unknown): ProjectIdentityRef {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["id", "root", "manifestPath"]) ||
    !isNonEmptyString(value.id) ||
    !isNonEmptyString(value.root) ||
    !isNonEmptyString(value.manifestPath)
  ) {
    throw new Error("无效的 ThesisForge project 标识");
  }
  return {
    id: value.id,
    root: value.root,
    manifestPath: value.manifestPath,
  };
}

function readSourceRef(value: unknown): SourceRef {
  if (!isObject(value)) {
    throw new Error("无效的 ThesisForge project 响应");
  }
  if (value.kind === "desktop") {
    if (
      !hasOnlyKeys(value, ["kind", "path", "fileName"]) ||
      !isNonEmptyString(value.path) ||
      !isNonEmptyString(value.fileName)
    ) {
      throw new Error("无效的 ThesisForge project 响应");
    }
    return { kind: "desktop", path: value.path, fileName: value.fileName };
  }
  if (value.kind === "web-workspace") {
    if (
      !hasOnlyKeys(value, ["kind", "workspaceId", "fileName"]) ||
      !isNonEmptyString(value.workspaceId) ||
      !isNonEmptyString(value.fileName)
    ) {
      throw new Error("无效的 ThesisForge project 响应");
    }
    return {
      kind: "web-workspace",
      workspaceId: value.workspaceId,
      fileName: value.fileName,
    };
  }
  if (value.kind === "web-upload") {
    if (
      !hasOnlyKeys(value, ["kind", "uploadId", "fileName"]) ||
      !isNonEmptyString(value.uploadId) ||
      !isNonEmptyString(value.fileName)
    ) {
      throw new Error("无效的 ThesisForge project 响应");
    }
    return {
      kind: "web-upload",
      uploadId: value.uploadId,
      fileName: value.fileName,
    };
  }
  throw new Error("无效的 ThesisForge project 响应");
}

export function readOpenedProject(value: unknown): OpenedProject {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["project", "source", "text"]) ||
    typeof value.text !== "string"
  ) {
    throw new Error("无效的 ThesisForge project 响应");
  }
  return {
    project: readProjectIdentity(value.project),
    source: readSourceRef(value.source),
    text: value.text,
  };
}
