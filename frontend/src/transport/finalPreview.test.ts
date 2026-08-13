import {
  readFinalPreviewDescriptor,
  readPdfBytes,
} from "./finalPreview";

describe("final preview descriptor", () => {
  it("accepts strict Web and desktop descriptors", () => {
    expect(
      readFinalPreviewDescriptor({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        downloadId: "a".repeat(32),
      }),
    ).toMatchObject({ engine: "libreoffice" });
    expect(
      readFinalPreviewDescriptor({
        engine: "wps",
        label: "WPS PDF",
        fileName: "wps-export.pdf",
        authorizationId: "b".repeat(32),
      }),
    ).toMatchObject({ engine: "wps" });
  });

  it.each([
    {
      engine: "libreoffice",
      label: "LibreOffice PDF",
      fileName: "preview.pdf",
    },
    {
      engine: "libreoffice",
      label: "WPS PDF",
      fileName: "preview.pdf",
    },
    {
      engine: "wps",
      label: "WPS PDF",
      fileName: "../preview.pdf",
    },
    {
      engine: "wps",
      label: "WPS PDF",
      fileName: "preview.pdf",
      downloadId: "a".repeat(32),
    },
    {
      engine: "libreoffice",
      label: "LibreOffice PDF",
      fileName: "preview.pdf",
      downloadId: "a".repeat(32),
      authorizationId: "b".repeat(32),
    },
    {
      engine: "wps",
      label: "WPS PDF",
      fileName: "preview.pdf",
      authorizationId: "not-an-authorization",
    },
    {
      engine: "libreoffice",
      label: "LibreOffice PDF",
      fileName: "preview.pdf",
      path: "/private/preview.pdf",
    },
  ])("rejects malformed or path-bearing descriptors", (descriptor) => {
    expect(() => readFinalPreviewDescriptor(descriptor)).toThrow(
      "无效的最终预览描述",
    );
  });

  it("accepts only PDF signature bytes", () => {
    expect(readPdfBytes(new TextEncoder().encode("%PDF-1.7"))).toBeInstanceOf(
      Uint8Array,
    );
    expect(readPdfBytes(Array.from(new TextEncoder().encode("%PDF-1.7"))))
      .toBeInstanceOf(Uint8Array);
    expect(() => readPdfBytes(new TextEncoder().encode("not-pdf"))).toThrow(
      "无效的 PDF 数据",
    );
    expect(() => readPdfBytes([0x25, 0x50, 0x44, 0x46, 256])).toThrow(
      "无效的 PDF 数据",
    );
    expect(() => readPdfBytes([0x25, 0x50, 0x44, 0x46, 1.5])).toThrow(
      "无效的 PDF 数据",
    );
  });
});
