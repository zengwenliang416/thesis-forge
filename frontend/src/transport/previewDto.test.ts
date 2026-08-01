import fixture from "../../../tests/fixtures/preview-workbench-v1.json";
import {
  readSerializedPreviewResult,
  type SerializedPreviewResult,
} from "./dto";

describe("preview transport DTO", () => {
  const typedFixture = fixture as unknown as SerializedPreviewResult;

  it("accepts the versioned renderer-neutral golden contract", () => {
    expect(
      readSerializedPreviewResult(
        fixture as unknown as Record<string, unknown>,
        true,
      ),
    ).toEqual(typedFixture);
  });

  it.each([
    {
      name: "missing outline",
      value: { preview: fixture.preview },
    },
    {
      name: "invalid source line",
      value: {
        ...fixture,
        outline: [{ ...fixture.outline[0], line: 0 }],
      },
    },
    {
      name: "unknown content type",
      value: {
        ...fixture,
        preview: {
          ...fixture.preview,
          blocks: [
            {
              ...fixture.preview.blocks[0],
              content: { type: "docx-xml", xml: "<w:p/>" },
            },
          ],
        },
      },
    },
    {
      name: "path leak",
      value: {
        ...fixture,
        preview: {
          ...fixture.preview,
          blocks: [
            {
              ...fixture.preview.blocks[2],
              content: {
                ...fixture.preview.blocks[2].content,
                assetPath: "/private/tmp/arch.png",
              },
            },
          ],
        },
      },
    },
  ])("rejects malformed nested preview data: $name", ({ value }) => {
    expect(() =>
      readSerializedPreviewResult(value as Record<string, unknown>, true),
    ).toThrow("无效的 ThesisForge transport 响应");
  });

  it("requires preview data for preview consumers", () => {
    expect(() => readSerializedPreviewResult({}, true)).toThrow(
      "无效的 ThesisForge transport 响应",
    );
  });
});
