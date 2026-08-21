import type { FinalPreviewDescriptor } from "./finalPreview";
import { PROTOCOL_VERSION } from "./dto";

export type { FinalPreviewDescriptor } from "./finalPreview";

export type BuildStage =
  | "parse"
  | "validate"
  | "compile"
  | "render"
  | "finalize"
  | "postflight"
  | "preview";

export type BuildStageStatus =
  | "pending"
  | "running"
  | "succeeded"
  | "failed"
  | "skipped";

export type BuildErrorKind =
  | "validation"
  | "compile"
  | "permission"
  | "render"
  | "finalize"
  | "canceled"
  | "transport";

// Workspace projection types; wire terminal events use BuildReport only.
export interface BuildOutput {
  kind: "desktop" | "web-download";
  name: string;
  downloadId?: string;
  finalPreview?: FinalPreviewDescriptor;
}

export interface BuildReportStage {
  name: BuildStage;
  status: BuildStageStatus;
  startedAt?: string | null;
  completedAt?: string | null;
}

export interface BuildReportSourceRange {
  file: string;
  startLine: number;
  startColumn: number | null;
  endLine: number | null;
  endColumn: number | null;
}

export interface BuildReportRelatedLocation {
  message: string;
  source: BuildReportSourceRange;
}

export type BuildReportDetail = string | number | boolean | null;

export interface BuildReportDiagnostic {
  id: string;
  severity: "error" | "warning" | "info";
  category:
    | "project"
    | "source"
    | "semantic"
    | "reference"
    | "resource"
    | "template"
    | "compile"
    | "docx"
    | "office"
    | "permission"
    | "transport"
    | "internal";
  code: string;
  stage: BuildStage;
  message: string;
  source: BuildReportSourceRange | null;
  target: string | null;
  suggestion: string | null;
  relatedLocations: BuildReportRelatedLocation[];
  details: Record<string, BuildReportDetail>;
}

export interface BuildReportLog {
  sequence: number;
  stage: BuildStage;
  level: "debug" | "info" | "warning" | "error";
  message: string;
}

export interface BuildReportOutput {
  docxPath: string | null;
  pdfPath: string | null;
  previewStale: boolean;
  successfulBuildId: string | null;
}

export interface BuildReport {
  schemaVersion: "thesisforge.build-report.v2";
  buildId: string;
  intent: "publish" | "live-preview";
  outcome: "succeeded" | "failed" | "canceled";
  startedAt?: string | null;
  completedAt?: string | null;
  stages: BuildReportStage[];
  failedStage: BuildStage | null;
  primaryDiagnosticId: string | null;
  diagnostics: BuildReportDiagnostic[];
  logs: BuildReportLog[];
  output: BuildReportOutput | null;
}

interface BuildEventBase {
  protocol: typeof PROTOCOL_VERSION;
  requestId: string;
}

export type CompletedBuildEvent = BuildEventBase & {
  type: "completed";
  report: BuildReport;
};

export type BuildEvent =
  | (BuildEventBase & { type: "progress"; stage: BuildStage })
  | CompletedBuildEvent;

const STAGES: readonly BuildStage[] = [
  "parse",
  "validate",
  "compile",
  "render",
  "finalize",
  "postflight",
  "preview",
];

const STAGE_STATUSES: readonly BuildStageStatus[] = [
  "pending",
  "running",
  "succeeded",
  "failed",
  "skipped",
];

const DIAGNOSTIC_CATEGORIES: readonly BuildReportDiagnostic["category"][] = [
  "project",
  "source",
  "semantic",
  "reference",
  "resource",
  "template",
  "compile",
  "docx",
  "office",
  "permission",
  "transport",
  "internal",
];

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  return Object.keys(value).every((key) => keys.includes(key));
}

function hasRequiredKeys(
  value: Record<string, unknown>,
  keys: readonly string[],
): boolean {
  return keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

function isStringEnum<T extends string>(
  value: unknown,
  values: readonly T[],
): value is T {
  return typeof value === "string" && values.includes(value as T);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isPositiveInteger(value: unknown): value is number {
  return isFiniteNumber(value) && Number.isInteger(value) && value >= 1;
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function daysInMonth(year: number, month: number): number {
  if (month === 2) {
    return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
      ? 29
      : 28;
  }
  return [4, 6, 9, 11].includes(month) ? 30 : 31;
}

function isDateTime(value: unknown): value is string {
  if (typeof value !== "string") {
    return false;
  }
  const match =
    /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?([Zz]|[+-]\d{2}:\d{2})$/.exec(
      value,
    );
  if (!match) {
    return false;
  }
  const [, year, month, day, hour, minute, second, zone] = match;
  const numericYear = Number(year);
  const numericMonth = Number(month);
  const numericDay = Number(day);
  const numericHour = Number(hour);
  const numericMinute = Number(minute);
  const numericSecond = Number(second);
  if (
    numericMonth < 1 ||
    numericMonth > 12 ||
    numericDay < 1 ||
    numericDay > daysInMonth(numericYear, numericMonth) ||
    numericHour > 23 ||
    numericMinute > 59 ||
    numericSecond > 59 &&
      !(numericSecond === 60 && numericHour === 23 && numericMinute === 59)
  ) {
    return false;
  }
  if (zone.toUpperCase() !== "Z") {
    const offsetHour = Number(zone.slice(1, 3));
    const offsetMinute = Number(zone.slice(4, 6));
    if (offsetHour > 23 || offsetMinute > 59) {
      return false;
    }
  }
  return true;
}

function isNullableDateTime(value: unknown): value is string | null {
  return value === null || isDateTime(value);
}

function hasOptionalDate(
  value: Record<string, unknown>,
  key: "startedAt" | "completedAt",
): boolean {
  return (
    !Object.prototype.hasOwnProperty.call(value, key) ||
    isNullableDateTime(value[key])
  );
}

function isSourceRange(value: unknown): value is BuildReportSourceRange {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
      "file",
      "startLine",
      "startColumn",
      "endLine",
      "endColumn",
    ]) ||
    !hasRequiredKeys(value, [
      "file",
      "startLine",
      "startColumn",
      "endLine",
      "endColumn",
    ]) ||
    typeof value.file !== "string" ||
    value.file.length === 0 ||
    !isPositiveInteger(value.startLine) ||
    (value.startColumn !== null && !isPositiveInteger(value.startColumn)) ||
    (value.endLine !== null && !isPositiveInteger(value.endLine)) ||
    (value.endColumn !== null && !isPositiveInteger(value.endColumn))
  ) {
    return false;
  }
  if (value.endLine !== null && value.endLine < value.startLine) {
    return false;
  }
  return !(
    value.endLine === value.startLine &&
    value.startColumn !== null &&
    value.endColumn !== null &&
    value.endColumn < value.startColumn
  );
}

function isStageState(value: unknown): value is BuildReportStage {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["name", "status", "startedAt", "completedAt"]) &&
    hasRequiredKeys(value, ["name", "status"]) &&
    isStringEnum(value.name, STAGES) &&
    isStringEnum(value.status, STAGE_STATUSES) &&
    hasOptionalDate(value, "startedAt") &&
    hasOptionalDate(value, "completedAt")
  );
}

function isRelatedLocation(
  value: unknown,
): value is BuildReportRelatedLocation {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["message", "source"]) &&
    hasRequiredKeys(value, ["message", "source"]) &&
    typeof value.message === "string" &&
    isSourceRange(value.source)
  );
}

function isDetails(
  value: unknown,
): value is Record<string, BuildReportDetail> {
  return (
    isObject(value) &&
    Object.values(value).every(
      (item) =>
        item === null ||
        typeof item === "string" ||
        typeof item === "boolean" ||
        isFiniteNumber(item),
    )
  );
}

function isDiagnostic(value: unknown): value is BuildReportDiagnostic {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "id",
      "severity",
      "category",
      "code",
      "stage",
      "message",
      "source",
      "target",
      "suggestion",
      "relatedLocations",
      "details",
    ]) &&
    hasRequiredKeys(value, [
      "id",
      "severity",
      "category",
      "code",
      "stage",
      "message",
      "source",
      "target",
      "suggestion",
      "relatedLocations",
      "details",
    ]) &&
    typeof value.id === "string" &&
    value.id.length > 0 &&
    isStringEnum(value.severity, ["error", "warning", "info"]) &&
    isStringEnum(value.category, DIAGNOSTIC_CATEGORIES) &&
    typeof value.code === "string" &&
    /^TF-[A-Z0-9-]+$/.test(value.code) &&
    isStringEnum(value.stage, STAGES) &&
    typeof value.message === "string" &&
    value.message.length > 0 &&
    (value.source === null || isSourceRange(value.source)) &&
    isNullableString(value.target) &&
    isNullableString(value.suggestion) &&
    Array.isArray(value.relatedLocations) &&
    value.relatedLocations.every(isRelatedLocation) &&
    isDetails(value.details)
  );
}

function isLog(value: unknown): value is BuildReportLog {
  return (
    isObject(value) &&
    hasOnlyKeys(value, ["sequence", "stage", "level", "message"]) &&
    hasRequiredKeys(value, ["sequence", "stage", "level", "message"]) &&
    isFiniteNumber(value.sequence) &&
    Number.isInteger(value.sequence) &&
    value.sequence >= 0 &&
    isStringEnum(value.stage, STAGES) &&
    isStringEnum(value.level, ["debug", "info", "warning", "error"]) &&
    typeof value.message === "string" &&
    value.message.length <= 4000
  );
}

function isOutput(value: unknown): value is BuildReportOutput {
  return (
    isObject(value) &&
    hasOnlyKeys(value, [
      "docxPath",
      "pdfPath",
      "previewStale",
      "successfulBuildId",
    ]) &&
    hasRequiredKeys(value, [
      "docxPath",
      "pdfPath",
      "previewStale",
      "successfulBuildId",
    ]) &&
    isNullableString(value.docxPath) &&
    isNullableString(value.pdfPath) &&
    typeof value.previewStale === "boolean" &&
    isNullableString(value.successfulBuildId)
  );
}

function isReport(value: unknown): value is BuildReport {
  if (
    !isObject(value) ||
    !hasOnlyKeys(value, [
      "schemaVersion",
      "buildId",
      "intent",
      "outcome",
      "startedAt",
      "completedAt",
      "stages",
      "failedStage",
      "primaryDiagnosticId",
      "diagnostics",
      "logs",
      "output",
    ]) ||
    !hasRequiredKeys(value, [
      "schemaVersion",
      "buildId",
      "intent",
      "outcome",
      "stages",
      "failedStage",
      "primaryDiagnosticId",
      "diagnostics",
      "logs",
      "output",
    ]) ||
    value.schemaVersion !== "thesisforge.build-report.v2" ||
    typeof value.buildId !== "string" ||
    value.buildId.length === 0 ||
    !isStringEnum(value.intent, ["publish", "live-preview"]) ||
    !isStringEnum(value.outcome, ["succeeded", "failed", "canceled"]) ||
    !hasOptionalDate(value, "startedAt") ||
    !hasOptionalDate(value, "completedAt") ||
    !Array.isArray(value.stages) ||
    value.stages.length === 0 ||
    !value.stages.every(isStageState) ||
    (value.failedStage !== null &&
      !isStringEnum(value.failedStage, STAGES)) ||
    (value.primaryDiagnosticId !== null &&
      typeof value.primaryDiagnosticId !== "string") ||
    !Array.isArray(value.diagnostics) ||
    !value.diagnostics.every(isDiagnostic) ||
    !Array.isArray(value.logs) ||
    value.logs.length > 500 ||
    !value.logs.every(isLog) ||
    (value.output !== null && !isOutput(value.output))
  ) {
    return false;
  }
  return (
    value.primaryDiagnosticId === null ||
    value.diagnostics.some(
      (diagnostic) => diagnostic.id === value.primaryDiagnosticId,
    )
  );
}

function readReport(value: unknown): BuildReport {
  if (!isReport(value)) {
    throw new Error("无效的 ThesisForge BuildReport");
  }
  return value;
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
    isStringEnum(value.stage, STAGES)
  ) {
    return {
      protocol: PROTOCOL_VERSION,
      requestId: value.requestId,
      type: "progress",
      stage: value.stage,
    };
  }
  if (
    value.type === "completed" &&
    hasOnlyKeys(value, ["protocol", "requestId", "type", "report"]) &&
    hasRequiredKeys(value, ["protocol", "requestId", "type", "report"])
  ) {
    return {
      protocol: PROTOCOL_VERSION,
      requestId: value.requestId,
      type: "completed",
      report: readReport(value.report),
    };
  }
  throw new Error("无效的 ThesisForge 构建事件");
}
