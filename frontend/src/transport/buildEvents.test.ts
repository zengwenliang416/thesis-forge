import { PROTOCOL_VERSION } from "./dto";
import { assertBuildEvent } from "./buildEvents";

describe("build event DTO", () => {
  it("accepts strict progress, success, and typed error events", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "build-1",
        type: "progress",
        stage: "render",
      }),
    ).toMatchObject({ type: "progress", stage: "render" });
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "build-1",
        type: "success",
        result: {
          output: {
            kind: "desktop",
            name: "thesis.docx",
            finalPreview: {
              engine: "libreoffice",
              label: "LibreOffice PDF",
              fileName: "thesis.preview.pdf",
              authorizationId: "b".repeat(32),
            },
          },
          diagnostics: [],
        },
      }),
    ).toMatchObject({
      type: "success",
      result: {
        output: {
          finalPreview: { engine: "libreoffice" },
        },
      },
    });
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "build-1",
        type: "error",
        error: {
          kind: "canceled",
          message: "构建已取消",
          stage: "finalize",
        },
      }),
    ).toMatchObject({ type: "error" });
  });

  it("rejects unknown stages, private output paths, and request drift", () => {
    expect(() =>
      assertBuildEvent(
        {
          protocol: PROTOCOL_VERSION,
          requestId: "build-1",
          type: "progress",
          stage: "upload",
        },
        "build-1",
      ),
    ).toThrow("无效的 ThesisForge 构建事件");
    expect(() =>
      assertBuildEvent(
        {
          protocol: PROTOCOL_VERSION,
          requestId: "build-old",
          type: "success",
          result: {
            output: {
              kind: "desktop",
              name: "thesis.docx",
              path: "/private/thesis.docx",
            },
            diagnostics: [],
          },
        },
        "build-1",
      ),
    ).toThrow("无效的 ThesisForge 构建事件");
    expect(() =>
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "build-1",
        type: "success",
        result: {
          output: {
            kind: "desktop",
            name: "thesis.docx",
            finalPreview: {
              engine: "libreoffice",
              label: "LibreOffice PDF",
              fileName: "../thesis.preview.pdf",
            },
          },
          diagnostics: [],
        },
      }),
    ).toThrow("无效的最终预览描述");
  });
});
