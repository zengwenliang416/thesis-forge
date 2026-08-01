export const PROTOCOL_VERSION = "thesisforge.workbench.v1" as const;

export type RuntimeKind = "web" | "tauri";
export type SourceKind = "desktop" | "web-workspace" | "web-upload";
export type OperationKind =
  | "open"
  | "inspect"
  | "validate"
  | "build"
  | "save"
  | "download"
  | "refresh";

export interface DesktopSourceRef {
  kind: "desktop";
  path: string;
  fileName: string;
}

export interface WebWorkspaceSourceRef {
  kind: "web-workspace";
  workspaceId: string;
  fileName: string;
}

export interface WebUploadSourceRef {
  kind: "web-upload";
  uploadId: string;
  fileName: string;
}

export type SourceRef =
  | DesktopSourceRef
  | WebWorkspaceSourceRef
  | WebUploadSourceRef;

export interface CommandEnvelope {
  protocol: typeof PROTOCOL_VERSION;
  requestId: string;
  operation: string;
  payload: {
    source?: SourceRef;
    output?: {
      kind: "desktop" | "web-download";
      path?: string;
      workspaceId?: string;
      fileName?: string;
    };
    templatePath?: string | null;
    text?: string;
  };
}

export interface SerializedDiagnostic {
  severity: "info" | "warning" | "error";
  code: string;
  message: string;
  line: number | null;
  target: string | null;
  details: Record<string, string | number>;
}

export interface CommandSuccess {
  protocol: typeof PROTOCOL_VERSION;
  requestId: string;
  ok: true;
  result: Record<string, unknown>;
}

export interface CommandFailure {
  protocol: typeof PROTOCOL_VERSION;
  requestId: string;
  ok: false;
  error: {
    kind: "protocol" | "request" | "permission" | "domain" | "transport";
    message: string;
    stage?: string;
  };
}

export type CommandResponse = CommandSuccess | CommandFailure;

export function assertCommandResponse(value: unknown): CommandResponse {
  if (
    typeof value !== "object" ||
    value === null ||
    !("protocol" in value) ||
    value.protocol !== PROTOCOL_VERSION ||
    !("requestId" in value) ||
    typeof value.requestId !== "string" ||
    value.requestId.length === 0 ||
    !("ok" in value) ||
    typeof value.ok !== "boolean"
  ) {
    throw new Error("无效的 ThesisForge transport 响应");
  }
  if (value.ok) {
    if (
      !("result" in value) ||
      typeof value.result !== "object" ||
      value.result === null ||
      Array.isArray(value.result)
    ) {
      throw new Error("无效的 ThesisForge transport 响应");
    }
  } else if (
    !("error" in value) ||
    typeof value.error !== "object" ||
    value.error === null ||
    !("kind" in value.error) ||
    !["protocol", "request", "permission", "domain", "transport"].includes(
      String(value.error.kind),
    ) ||
    !("message" in value.error) ||
    typeof value.error.message !== "string"
  ) {
    throw new Error("无效的 ThesisForge transport 响应");
  }
  return value as CommandResponse;
}
