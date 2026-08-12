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
export type CommandOperation = OperationKind | "preview";

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

export interface CommandOutputRef {
  kind: "desktop" | "web-download";
  path?: string;
  workspaceId?: string;
  fileName?: string;
  livePreviewId?: string;
}

export interface CommandEnvelope {
  protocol: typeof PROTOCOL_VERSION;
  requestId: string;
  operation: CommandOperation;
  payload: {
    source?: SourceRef;
    output?: CommandOutputRef;
    templateId?: string | null;
    templatePath?: string | null;
    text?: string;
    intent?: "publish" | "live-preview";
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

export interface SerializedPreviewMarker {
  severity: "info" | "warning" | "error";
  code: string;
}

export interface SerializedOutlineItem {
  selectionId: string;
  semanticId: string | null;
  level: number;
  text: string;
  line: number | null;
  markers: SerializedPreviewMarker[];
}

export type SerializedPreviewRun =
  | { type: "text"; text: string }
  | { type: "reference"; targetId: string; text: string }
  | {
      type: "citation";
      keys: string[];
      ordinals: number[];
      locator: string | null;
      text: string;
    }
  | {
      type: "footnote-reference";
      label: string;
      footnoteId: number;
      text: string;
    };

export type SerializedPreviewContent =
  | {
      type: "cover";
      fields: Array<{ label: string; value: string }>;
    }
  | {
      type: "section";
      role: "cover" | "front_matter" | "main";
    }
  | {
      type: "toc";
      minLevel: number;
      maxLevel: number;
    }
  | {
      type: "text";
      text: string;
      level: number | null;
      runs: SerializedPreviewRun[];
    }
  | {
      type: "list";
      ordered: boolean;
      start: number | null;
      items: Array<{
        text: string;
        level: number;
        ordinal: number | null;
        runs: SerializedPreviewRun[];
      }>;
    }
  | {
      type: "figure";
      src: string;
      caption: string;
      label: string;
      width: string | null;
      available: boolean;
    }
  | {
      type: "table";
      caption: string;
      label: string;
      rows: Array<{
        header: boolean;
        cells: Array<{
          text: string;
          alignment: "left" | "center" | "right" | null;
        }>;
      }>;
    }
  | {
      type: "equation";
      latex: string;
      label: string;
    }
  | {
      type: "listing";
      caption: string;
      language: string | null;
      code: string;
    }
  | {
      type: "algorithm";
      caption: string;
      body: string;
    }
  | {
      type: "footnote";
      label: string;
      footnoteId: number;
      text: string;
      runs: SerializedPreviewRun[];
    }
  | {
      type: "bibliography";
      entries: Array<{ key: string; ordinal: number; text: string }>;
    }
  | {
      type: "unsupported";
      originalKind: string;
    };

export interface SerializedPreviewBlock {
  selectionId: string;
  semanticId: string | null;
  kind: string;
  line: number | null;
  state: "ready" | "unsupported";
  markers: SerializedPreviewMarker[];
  content: SerializedPreviewContent;
}

export interface SerializedPreviewDocument {
  status: "empty" | "ready" | "blocked";
  message: string | null;
  disclaimer: string;
  blocks: SerializedPreviewBlock[];
}

export interface SerializedPreviewResult {
  schemaVersion: 1;
  outline: SerializedOutlineItem[];
  preview: SerializedPreviewDocument;
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

function isDetails(value: unknown): value is Record<string, string | number> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.values(value).every(
      (item) => typeof item === "string" || typeof item === "number",
    )
  );
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

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isLine(value: unknown): value is number | null {
  return (
    value === null ||
    (typeof value === "number" && Number.isInteger(value) && value >= 1)
  );
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 1;
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isPreviewMarker(value: unknown): value is SerializedPreviewMarker {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["severity", "code"]) &&
    ["info", "warning", "error"].includes(String(value.severity)) &&
    typeof value.code === "string" &&
    value.code.length > 0
  );
}

function isPreviewRun(value: unknown): value is SerializedPreviewRun {
  if (!isObject(value) || typeof value.type !== "string") {
    return false;
  }
  if (value.type === "text") {
    return (
      hasOnlyKeys(value, ["type", "text"]) && typeof value.text === "string"
    );
  }
  if (value.type === "reference") {
    return (
      hasOnlyKeys(value, ["type", "targetId", "text"]) &&
      typeof value.targetId === "string" &&
      value.targetId.length > 0 &&
      typeof value.text === "string"
    );
  }
  if (value.type === "citation") {
    return (
      hasOnlyKeys(value, [
        "type",
        "keys",
        "ordinals",
        "locator",
        "text",
      ]) &&
      isStringArray(value.keys) &&
      Array.isArray(value.ordinals) &&
      value.ordinals.every(isPositiveInteger) &&
      isNullableString(value.locator) &&
      typeof value.text === "string"
    );
  }
  if (value.type === "footnote-reference") {
    return (
      hasOnlyKeys(value, ["type", "label", "footnoteId", "text"]) &&
      typeof value.label === "string" &&
      isPositiveInteger(value.footnoteId) &&
      typeof value.text === "string"
    );
  }
  return false;
}

function isPreviewContent(value: unknown): value is SerializedPreviewContent {
  if (!isObject(value) || typeof value.type !== "string") {
    return false;
  }
  if (value.type === "cover") {
    return (
      hasOnlyKeys(value, ["type", "fields"]) &&
      Array.isArray(value.fields) &&
      value.fields.every(
        (field) =>
          isObject(field) &&
          hasOnlyKeys(field, ["label", "value"]) &&
          typeof field.label === "string" &&
          typeof field.value === "string",
      )
    );
  }
  if (value.type === "section") {
    return (
      hasOnlyKeys(value, ["type", "role"]) &&
      ["cover", "front_matter", "main"].includes(String(value.role))
    );
  }
  if (value.type === "toc") {
    return (
      hasOnlyKeys(value, ["type", "minLevel", "maxLevel"]) &&
      isPositiveInteger(value.minLevel) &&
      isPositiveInteger(value.maxLevel)
    );
  }
  if (value.type === "text") {
    return (
      hasOnlyKeys(value, ["type", "text", "level", "runs"]) &&
      typeof value.text === "string" &&
      (value.level === null || isPositiveInteger(value.level)) &&
      Array.isArray(value.runs) &&
      value.runs.every(isPreviewRun)
    );
  }
  if (value.type === "list") {
    return (
      hasOnlyKeys(value, ["type", "ordered", "start", "items"]) &&
      typeof value.ordered === "boolean" &&
      (value.start === null || isPositiveInteger(value.start)) &&
      Array.isArray(value.items) &&
      value.items.every(
        (item) =>
          isObject(item) &&
          hasOnlyKeys(item, ["text", "level", "ordinal", "runs"]) &&
          typeof item.text === "string" &&
          isNonNegativeInteger(item.level) &&
          (item.ordinal === null || isPositiveInteger(item.ordinal)) &&
          Array.isArray(item.runs) &&
          item.runs.every(isPreviewRun),
      )
    );
  }
  if (value.type === "figure") {
    return (
      hasOnlyKeys(value, [
        "type",
        "src",
        "caption",
        "label",
        "width",
        "available",
      ]) &&
      typeof value.src === "string" &&
      typeof value.caption === "string" &&
      typeof value.label === "string" &&
      isNullableString(value.width) &&
      typeof value.available === "boolean"
    );
  }
  if (value.type === "table") {
    return (
      hasOnlyKeys(value, ["type", "caption", "label", "rows"]) &&
      typeof value.caption === "string" &&
      typeof value.label === "string" &&
      Array.isArray(value.rows) &&
      value.rows.every(
        (row) =>
          isObject(row) &&
          hasOnlyKeys(row, ["header", "cells"]) &&
          typeof row.header === "boolean" &&
          Array.isArray(row.cells) &&
          row.cells.every(
            (cell) =>
              isObject(cell) &&
              hasOnlyKeys(cell, ["text", "alignment"]) &&
              typeof cell.text === "string" &&
              (cell.alignment === null ||
                ["left", "center", "right"].includes(String(cell.alignment))),
          ),
      )
    );
  }
  if (value.type === "equation") {
    return (
      hasOnlyKeys(value, ["type", "latex", "label"]) &&
      typeof value.latex === "string" &&
      typeof value.label === "string"
    );
  }
  if (value.type === "listing") {
    return (
      hasOnlyKeys(value, ["type", "caption", "language", "code"]) &&
      typeof value.caption === "string" &&
      isNullableString(value.language) &&
      typeof value.code === "string"
    );
  }
  if (value.type === "algorithm") {
    return (
      hasOnlyKeys(value, ["type", "caption", "body"]) &&
      typeof value.caption === "string" &&
      typeof value.body === "string"
    );
  }
  if (value.type === "footnote") {
    return (
      hasOnlyKeys(value, [
        "type",
        "label",
        "footnoteId",
        "text",
        "runs",
      ]) &&
      typeof value.label === "string" &&
      isPositiveInteger(value.footnoteId) &&
      typeof value.text === "string" &&
      Array.isArray(value.runs) &&
      value.runs.every(isPreviewRun)
    );
  }
  if (value.type === "bibliography") {
    return (
      hasOnlyKeys(value, ["type", "entries"]) &&
      Array.isArray(value.entries) &&
      value.entries.every(
        (entry) =>
          isObject(entry) &&
          hasOnlyKeys(entry, ["key", "ordinal", "text"]) &&
          typeof entry.key === "string" &&
          isPositiveInteger(entry.ordinal) &&
          typeof entry.text === "string",
      )
    );
  }
  if (value.type === "unsupported") {
    return (
      hasOnlyKeys(value, ["type", "originalKind"]) &&
      typeof value.originalKind === "string" &&
      value.originalKind.length > 0
    );
  }
  return false;
}

function isOutlineItem(value: unknown): value is SerializedOutlineItem {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "selectionId",
      "semanticId",
      "level",
      "text",
      "line",
      "markers",
    ]) &&
    typeof value.selectionId === "string" &&
    value.selectionId.length > 0 &&
    isNullableString(value.semanticId) &&
    isPositiveInteger(value.level) &&
    typeof value.text === "string" &&
    isLine(value.line) &&
    Array.isArray(value.markers) &&
    value.markers.every(isPreviewMarker)
  );
}

function isPreviewBlock(value: unknown): value is SerializedPreviewBlock {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "selectionId",
      "semanticId",
      "kind",
      "line",
      "state",
      "markers",
      "content",
    ]) &&
    typeof value.selectionId === "string" &&
    value.selectionId.length > 0 &&
    isNullableString(value.semanticId) &&
    typeof value.kind === "string" &&
    value.kind.length > 0 &&
    isLine(value.line) &&
    ["ready", "unsupported"].includes(String(value.state)) &&
    Array.isArray(value.markers) &&
    value.markers.every(isPreviewMarker) &&
    isPreviewContent(value.content)
  );
}

function isPreviewDocument(value: unknown): value is SerializedPreviewDocument {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["status", "message", "disclaimer", "blocks"]) &&
    ["empty", "ready", "blocked"].includes(String(value.status)) &&
    isNullableString(value.message) &&
    typeof value.disclaimer === "string" &&
    value.disclaimer.length > 0 &&
    Array.isArray(value.blocks) &&
    value.blocks.every(isPreviewBlock)
  );
}

export function readSerializedPreviewResult(
  result: Record<string, unknown>,
  required = false,
): SerializedPreviewResult | null {
  const hasPreviewData = "schemaVersion" in result || "preview" in result;
  if (!hasPreviewData) {
    if (required) {
      throw new Error("无效的 ThesisForge transport 响应");
    }
    return null;
  }
  if (
    result.schemaVersion !== 1 ||
    !Array.isArray(result.outline) ||
    !result.outline.every(isOutlineItem) ||
    !isPreviewDocument(result.preview)
  ) {
    throw new Error("无效的 ThesisForge transport 响应");
  }
  return result as unknown as SerializedPreviewResult;
}

function isSerializedDiagnostic(value: unknown): value is SerializedDiagnostic {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    "severity" in value &&
    ["info", "warning", "error"].includes(String(value.severity)) &&
    "code" in value &&
    typeof value.code === "string" &&
    value.code.length > 0 &&
    "message" in value &&
    typeof value.message === "string" &&
    "line" in value &&
    (value.line === null ||
      (typeof value.line === "number" &&
        Number.isInteger(value.line) &&
        value.line >= 1)) &&
    "target" in value &&
    (value.target === null || typeof value.target === "string") &&
    "details" in value &&
    isDetails(value.details)
  );
}

export function readSerializedDiagnostics(
  result: Record<string, unknown>,
  required = false,
): SerializedDiagnostic[] {
  if (!("diagnostics" in result)) {
    if (required) {
      throw new Error("无效的 ThesisForge transport 响应");
    }
    return [];
  }
  if (
    !Array.isArray(result.diagnostics) ||
    !result.diagnostics.every(isSerializedDiagnostic)
  ) {
    throw new Error("无效的 ThesisForge transport 响应");
  }
  return result.diagnostics;
}

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
    readSerializedDiagnostics(value.result as Record<string, unknown>);
    readSerializedPreviewResult(value.result as Record<string, unknown>);
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
