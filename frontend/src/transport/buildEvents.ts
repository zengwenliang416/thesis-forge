import {
  PROTOCOL_VERSION,
  readSerializedDiagnostics,
  type SerializedDiagnostic,
} from "./dto";

export type BuildStage =
  | "parse"
  | "validate"
  | "compile"
  | "render"
  | "finalize";

export type BuildErrorKind =
  | "validation"
  | "permission"
  | "render"
  | "finalize"
  | "canceled"
  | "transport";

export interface BuildOutput {
  kind: "desktop" | "web-download";
  name: string;
  downloadId?: string;
}

interface BuildEventBase {
  protocol: typeof PROTOCOL_VERSION;
  requestId: string;
}

export type BuildEvent =
  | (BuildEventBase & { type: "progress"; stage: BuildStage })
  | (BuildEventBase & {
      type: "success";
      result: {
        output: BuildOutput;
        diagnostics: SerializedDiagnostic[];
      };
    })
  | (BuildEventBase & {
      type: "error";
      error: {
        kind: BuildErrorKind;
        message: string;
        stage?: BuildStage;
      };
    });

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  return Object.keys(value).every((key) => keys.includes(key));
}

function isStage(value: unknown): value is BuildStage {
  return ["parse", "validate", "compile", "render", "finalize"].includes(
    String(value),
  );
}

function readOutput(value: unknown): BuildOutput {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, ["kind", "name", "downloadId"]) ||
    !["desktop", "web-download"].includes(String(value.kind)) ||
    typeof value.name !== "string" ||
    value.name.length === 0 ||
    (value.downloadId !== undefined && typeof value.downloadId !== "string")
  ) {
    throw new Error("无效的 ThesisForge 构建事件");
  }
  return value as unknown as BuildOutput;
}

export function assertBuildEvent(
  value: unknown,
  requestId?: string,
): BuildEvent {
  if (
    !isObject(value) ||
    value.protocol !== PROTOCOL_VERSION ||
    typeof value.requestId !== "string" ||
    value.requestId.length === 0 ||
    (requestId !== undefined && value.requestId !== requestId) ||
    typeof value.type !== "string"
  ) {
    throw new Error("无效的 ThesisForge 构建事件");
  }
  if (
    value.type === "progress" &&
    hasOnlyKeys(value, ["protocol", "requestId", "type", "stage"]) &&
    isStage(value.stage)
  ) {
    return value as unknown as BuildEvent;
  }
  if (
    value.type === "success" &&
    hasOnlyKeys(value, ["protocol", "requestId", "type", "result"]) &&
    isObject(value.result) &&
    hasOnlyKeys(value.result, ["source", "output", "diagnostics", "progress"])
  ) {
    return {
      protocol: PROTOCOL_VERSION,
      requestId: value.requestId,
      type: "success",
      result: {
        output: readOutput(value.result.output),
        diagnostics: readSerializedDiagnostics(value.result, true),
      },
    };
  }
  if (
    value.type === "error" &&
    hasOnlyKeys(value, ["protocol", "requestId", "type", "error"]) &&
    isObject(value.error) &&
    hasOnlyKeys(value.error, ["kind", "message", "stage"]) &&
    [
      "validation",
      "permission",
      "render",
      "finalize",
      "canceled",
      "transport",
    ].includes(String(value.error.kind)) &&
    typeof value.error.message === "string" &&
    (value.error.stage === undefined || isStage(value.error.stage))
  ) {
    return value as unknown as BuildEvent;
  }
  throw new Error("无效的 ThesisForge 构建事件");
}
