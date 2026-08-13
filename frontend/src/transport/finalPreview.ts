export type FinalPreviewDescriptor =
  | {
      engine: "libreoffice";
      label: "LibreOffice PDF";
      fileName: string;
      downloadId?: string;
      authorizationId?: string;
      livePreviewId?: string;
    }
  | {
      engine: "wps";
      label: "WPS PDF";
      fileName: string;
      downloadId?: never;
      authorizationId?: string;
    };

export interface ResolvedFinalPreview {
  descriptor: FinalPreviewDescriptor;
  bytes: Uint8Array;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPlainPdfName(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 4 &&
    !value.includes("/") &&
    !value.includes("\\") &&
    value.toLowerCase().endsWith(".pdf")
  );
}

function isDownloadId(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length === 32 &&
    /^[0-9a-f]+$/.test(value)
  );
}

function isAuthorizationId(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length === 32 &&
    /^[0-9a-f]+$/.test(value)
  );
}

export function readFinalPreviewDescriptor(
  value: unknown,
): FinalPreviewDescriptor {
  if (
    !isObject(value) ||
    !Object.keys(value).every((key) =>
      [
        "engine",
        "label",
        "fileName",
        "downloadId",
        "authorizationId",
        "livePreviewId",
      ].includes(key),
    ) ||
    !isPlainPdfName(value.fileName) ||
    (value.authorizationId !== undefined &&
      !isAuthorizationId(value.authorizationId)) ||
    (value.livePreviewId !== undefined &&
      !isAuthorizationId(value.livePreviewId))
  ) {
    throw new Error("无效的最终预览描述");
  }
  if (
    value.engine === "libreoffice" &&
    value.label === "LibreOffice PDF" &&
    ((isDownloadId(value.downloadId) &&
      value.authorizationId === undefined) ||
      (value.downloadId === undefined &&
        isAuthorizationId(value.authorizationId))) &&
    !(
      value.livePreviewId !== undefined &&
      value.downloadId === undefined
    )
  ) {
    return value as FinalPreviewDescriptor;
  }
  if (
    value.engine === "wps" &&
    value.label === "WPS PDF" &&
    value.downloadId === undefined &&
    value.livePreviewId === undefined
  ) {
    return value as FinalPreviewDescriptor;
  }
  throw new Error("无效的最终预览描述");
}

export function readPdfBytes(value: unknown): Uint8Array {
  const bytes = ArrayBuffer.isView(value)
    ? new Uint8Array(value.buffer, value.byteOffset, value.byteLength)
    : Object.prototype.toString.call(value) === "[object ArrayBuffer]"
      ? new Uint8Array(value as ArrayBuffer)
      : Array.isArray(value) &&
          value.every(
            (byte) =>
              typeof byte === "number" &&
              Number.isInteger(byte) &&
              byte >= 0 &&
              byte <= 255,
          )
        ? Uint8Array.from(value)
        : null;
  if (!bytes || bytes.length < 5) {
    throw new Error("无效的 PDF 数据");
  }
  const signature = [0x25, 0x50, 0x44, 0x46, 0x2d];
  if (!signature.every((byte, index) => bytes[index] === byte)) {
    throw new Error("无效的 PDF 数据");
  }
  return bytes;
}
