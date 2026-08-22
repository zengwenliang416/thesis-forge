import fixture from "../../../tests/fixtures/preview-workbench-v1.json";
import {
  readSerializedPreviewResult,
  type SerializedPreviewResult,
  type SerializedPreviewRun,
} from "./dto";

describe("preview transport DTO", () => {
  const typedFixture = fixture as unknown as SerializedPreviewResult;
  const paragraphBlock = fixture.preview.blocks[1];
  if (paragraphBlock.content.type !== "text") {
    throw new Error("preview fixture paragraph block is not text content");
  }
  const paragraphRuns = (
    paragraphBlock.content as unknown as { runs: SerializedPreviewRun[] }
  ).runs;

  it("accepts the versioned renderer-neutral golden contract", () => {
    expect(
      readSerializedPreviewResult(
        fixture as unknown as Record<string, unknown>,
        true,
      ),
    ).toEqual(typedFixture);
  });

  it("accepts all canonical rich inline run variants", () => {
    const richRuns = [
      { type: "text", text: "前" },
      { type: "reference", targetId: "fig:arch", text: "图 1-1" },
      {
        type: "hyperlink",
        text: "项目主页",
        destination: "https://example.test",
      },
      { type: "math", latex: "x^2 + y^2", text: "x^2 + y^2" },
      { type: "soft-break", text: " " },
      { type: "hard-break", text: "\n" },
      {
        type: "citation",
        keys: ["ref-1"],
        ordinals: [1],
        locator: null,
        text: "[1]",
      },
      {
        type: "footnote-reference",
        label: "note",
        footnoteId: 1,
        text: "脚注1",
      },
    ];
    const value = {
      ...fixture,
      preview: {
        ...fixture.preview,
        blocks: [
          ...fixture.preview.blocks.slice(0, 1),
          {
            ...paragraphBlock,
            content: {
              ...paragraphBlock.content,
              runs: richRuns,
            },
          },
          ...fixture.preview.blocks.slice(2),
        ],
      },
    };

    expect(
      readSerializedPreviewResult(value as unknown as Record<string, unknown>, true),
    ).toEqual(value);
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
    {
      name: "unknown inline run",
      value: {
        ...fixture,
        preview: {
          ...fixture.preview,
          blocks: [
            ...fixture.preview.blocks.slice(0, 1),
            {
              ...paragraphBlock,
              content: {
                ...paragraphBlock.content,
                runs: [
                  ...paragraphRuns,
                  { type: "inline-future", text: "不支持" },
                ],
              },
            },
            ...fixture.preview.blocks.slice(2),
          ],
        },
      },
    },
    {
      name: "hyperlink extra key",
      value: {
        ...fixture,
        preview: {
          ...fixture.preview,
          blocks: [
            ...fixture.preview.blocks.slice(0, 1),
            {
              ...fixture.preview.blocks[1],
              content: {
                ...fixture.preview.blocks[1].content,
                runs: [
                  {
                    type: "hyperlink",
                    text: "项目主页",
                    destination: "https://example.test",
                    payload: {},
                  },
                ],
              },
            },
            ...fixture.preview.blocks.slice(2),
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
