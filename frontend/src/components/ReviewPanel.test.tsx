import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createInitialWorkspaceState } from "../state/workspace";
import type { WorkspaceState } from "../state/workspace";
import type { SerializedPreviewBlock } from "../transport/dto";
import { ReviewPanel } from "./ReviewPanel";

function stateWithBlocks(blocks: SerializedPreviewBlock[]): WorkspaceState {
  return {
    ...createInitialWorkspaceState(),
    status: "populated",
    source: {
      kind: "desktop",
      name: "thesis.md",
      writable: true,
    },
    preview: {
      status: "ready",
      message: null,
      disclaimer: "结构预览不代表 Word 最终分页。",
      blocks,
    },
  };
}

describe("ReviewPanel", () => {
  it("renders reader-facing content without technical markers or raw paths", () => {
    const state = stateWithBlocks([
      {
        selectionId: "para:intro",
        semanticId: "chap:intro",
        kind: "paragraph",
        line: 12,
        state: "ready",
        markers: [{ severity: "warning", code: "heading-level-jump" }],
        content: {
          type: "text",
          text: "系统结构见图 1-1，访问项目主页，x² + y²，[1]脚注1。",
          level: null,
          runs: [
            { type: "text", text: "系统结构见" },
            { type: "reference", targetId: "fig:arch", text: "图 1-1" },
            {
              type: "hyperlink",
              text: "项目主页",
              destination: "https://example.test/project",
            },
            { type: "math", latex: "x^2 + y^2", text: "x² + y²" },
            {
              type: "citation",
              keys: ["ref-1"],
              ordinals: [1],
              locator: null,
              text: "[1]",
            },
            {
              type: "footnote-reference",
              label: "scope",
              footnoteId: 1,
              text: "脚注1",
            },
          ],
        },
      },
      {
        selectionId: "fig:arch",
        semanticId: "fig:arch",
        kind: "figure",
        line: 18,
        state: "ready",
        markers: [],
        content: {
          type: "figure",
          src: "/private/project/assets/arch.png",
          caption: "系统架构",
          label: "图 1-1",
          width: null,
          available: true,
        },
      },
      {
        selectionId: "raw:paragraph",
        semanticId: null,
        kind: "paragraph",
        line: 21,
        state: "ready",
        markers: [],
        content: {
          type: "text",
          text: "正文 {#chap:raw} para:secret /workspace/private/article.md /mnt/secret/article.md @secret-key ref:target [@secret-key]",
          level: null,
          runs: [],
        },
      },
    ]);
    const { container } = render(
      <ReviewPanel state={state} onActivated={() => undefined} />,
    );

    expect(screen.getByRole("region", { name: "文档内容审阅" })).toBeVisible();
    expect(screen.getAllByText("图 1-1")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "项目主页" })).toHaveAttribute(
      "href",
      "https://example.test/project",
    );
    expect(screen.getByText("x² + y²")).toBeVisible();
    expect(screen.getByText("系统架构")).toBeVisible();
    expect(container.textContent).not.toContain("chap:intro");
    expect(container.textContent).not.toContain("fig:arch");
    expect(container.textContent).not.toContain("ref-1");
    expect(container.textContent).not.toContain("/private/project");
    expect(container.textContent).not.toContain("heading-level-jump");
    expect(container.textContent).not.toContain("x^2 + y^2");
    expect(container.textContent).not.toContain("{#chap:raw}");
    expect(container.textContent).not.toContain("/Volumes/secret");
    expect(container.textContent).not.toContain("para:secret");
    expect(container.textContent).not.toContain("/workspace/private");
    expect(container.textContent).not.toContain("@secret-key");
    expect(container.textContent).not.toContain("ref:target");
    expect(container.textContent).not.toContain("[@secret-key]");
    expect(screen.getByRole("button", { name: "正文" })).toBeVisible();
    expect(
      screen.getByRole("img", { name: "图 1-1 系统架构" }),
    ).not.toHaveAttribute("aria-label", expect.stringContaining("/private"));
  });

  it("keeps rich blocks visible and turns unsupported content into a reader-facing problem", () => {
    const state = stateWithBlocks([
      {
        selectionId: "list:steps",
        semanticId: null,
        kind: "list",
        line: 20,
        state: "ready",
        markers: [],
        content: {
          type: "list",
          ordered: true,
          start: 1,
          items: [
            { text: "初始化", level: 0, ordinal: 1, runs: [] },
            { text: "运行", level: 0, ordinal: 2, runs: [] },
          ],
        },
      },
      {
        selectionId: "tbl:results",
        semanticId: "tbl:results",
        kind: "table",
        line: 23,
        state: "ready",
        markers: [],
        content: {
          type: "table",
          caption: "实验结果",
          label: "表 1-1",
          rows: [
            {
              header: true,
              cells: [{ text: "指标", alignment: "center" }],
            },
            {
              header: false,
              cells: [{ text: "准确率", alignment: "left" }],
            },
          ],
        },
      },
      {
        selectionId: "lst:code",
        semanticId: "lst:code",
        kind: "listing",
        line: 28,
        state: "ready",
        markers: [],
        content: {
          type: "listing",
          caption: "示例代码",
          language: "python",
          code: "print('ok')",
        },
      },
      {
        selectionId: "alg:flow",
        semanticId: "alg:flow",
        kind: "algorithm",
        line: 34,
        state: "ready",
        markers: [],
        content: {
          type: "algorithm",
          caption: "处理流程",
          body: "1. 读取\n2. 输出",
        },
      },
      {
        selectionId: "unknown",
        semanticId: null,
        kind: "future-node",
        line: 40,
        state: "unsupported",
        markers: [],
        content: { type: "unsupported", originalKind: "future-node" },
      },
    ]);
    const { container } = render(
      <ReviewPanel state={state} onActivated={() => undefined} />,
    );

    expect(screen.getByText("初始化")).toBeVisible();
    expect(screen.getByRole("table")).toBeVisible();
    expect(screen.getByText("实验结果")).toBeVisible();
    expect(screen.getByText("print('ok')")).toBeVisible();
    expect(screen.getByText("处理流程")).toBeVisible();
    expect(screen.getByText("此内容无法在 Review 中显示")).toBeVisible();
    expect(container.textContent).not.toContain("future-node");
  });

  it("renders rich inline formatting, code blocks, and nested blockquotes", () => {
    const state = stateWithBlocks([
      {
        selectionId: "format:paragraph",
        semanticId: null,
        kind: "paragraph",
        line: 41,
        state: "ready",
        markers: [],
        content: {
          type: "text",
          text: "粗斜体代码",
          level: null,
          runs: [
            {
              type: "text",
              text: "粗斜体代码",
              bold: true,
              italic: true,
              code: true,
            },
          ],
        },
      },
      {
        selectionId: "code:block",
        semanticId: null,
        kind: "code_block",
        line: 42,
        state: "ready",
        markers: [],
        content: {
          type: "code-block",
          language: "python",
          code: "print(1)\n",
        },
      },
      {
        selectionId: "quote:block",
        semanticId: null,
        kind: "blockquote",
        line: 43,
        state: "ready",
        markers: [],
        content: {
          type: "blockquote",
          children: [
            {
              kind: "paragraph",
              state: "ready",
              content: {
                type: "text",
                text: "外层引用",
                level: null,
                runs: [{ type: "text", text: "外层引用", bold: true }],
              },
            },
            {
              kind: "blockquote",
              state: "ready",
              content: {
                type: "blockquote",
                children: [
                  {
                    kind: "paragraph",
                    state: "unsupported",
                    content: {
                      type: "text",
                      text: "内层引用",
                      level: null,
                      runs: [{ type: "text", text: "内层引用", italic: true }],
                    },
                  },
                ],
              },
            },
          ],
        },
      },
    ]);
    const { container } = render(
      <ReviewPanel state={state} onActivated={() => undefined} />,
    );

    const formatted = screen.getByText("粗斜体代码");
    expect(formatted.closest("strong")).not.toBeNull();
    expect(formatted.closest("em")).not.toBeNull();
    expect(formatted.closest("code")).toHaveClass("review-inline-code");
    expect(screen.getByText("print(1)").closest("pre")).toHaveAttribute(
      "data-language",
      "python",
    );
    const quote = container.querySelector("blockquote.review-blockquote");
    expect(quote).toBeInTheDocument();
    expect(within(quote as HTMLElement).getByText("外层引用")).toBeVisible();
    expect(quote?.querySelector("blockquote.review-blockquote")).toBeInTheDocument();
    expect(
      quote?.querySelector('[data-review-state="unsupported"]'),
    ).toBeInTheDocument();
  });

  it("sanitizes rich DTO fields and accessibility attributes without changing code", () => {
    const state = stateWithBlocks([
      {
        selectionId: "list:raw",
        semanticId: null,
        kind: "list",
        line: 50,
        state: "ready",
        markers: [],
        content: {
          type: "list",
          ordered: false,
          start: null,
          items: [
            {
              text: "列表 {#item:raw} /tmp/input",
              level: 0,
              ordinal: null,
              runs: [],
            },
          ],
        },
      },
      {
        selectionId: "table:raw",
        semanticId: null,
        kind: "table",
        line: 51,
        state: "ready",
        markers: [],
        content: {
          type: "table",
          caption: "结果 {#tbl:raw}",
          label: "表 2-1",
          rows: [
            {
              header: false,
              cells: [{ text: "数据 /private/table.csv", alignment: "left" }],
            },
          ],
        },
      },
      {
        selectionId: "equation:raw",
        semanticId: null,
        kind: "equation",
        line: 52,
        state: "ready",
        markers: [],
        content: {
          type: "equation",
          latex: String.raw`$$\frac{a}{b} + \sqrt{x} + \unknown{a} \\ b$$`,
          label: "式（2-1）{#eq:raw}",
        },
      },
      {
        selectionId: "footnote:raw",
        semanticId: null,
        kind: "footnote",
        line: 53,
        state: "ready",
        markers: [],
        content: {
          type: "footnote",
          label: "scope {#fn:raw}",
          footnoteId: 3,
          text: "脚注正文 [@secret] /Volumes/footnote.md",
          runs: [],
        },
      },
      {
        selectionId: "bibliography:raw",
        semanticId: null,
        kind: "bibliography",
        line: 54,
        state: "ready",
        markers: [],
        content: {
          type: "bibliography",
          entries: [
            {
              key: "secret-key",
              ordinal: 1,
              text: "作者。标题。secret-key {#ref:raw} /Users/secret/ref.bib",
            },
          ],
        },
      },
      {
        selectionId: "figure:remote",
        semanticId: null,
        kind: "figure",
        line: 54,
        state: "ready",
        markers: [],
        content: {
          type: "figure",
          src: "https://example.test/source/source-meta?source=secret#fig:raw",
          caption:
            "说明 figure:raw source:source-meta target:target-meta selection:selection-meta node:node-meta line:line-meta /workspace/private/figure.png",
          label: "figure:raw source:source-meta",
          width: null,
          available: true,
        },
      },
      {
        selectionId: "listing:literal",
        semanticId: null,
        kind: "listing",
        line: 55,
        state: "ready",
        markers: [],
        content: {
          type: "listing",
          caption: "代码示例",
          language: "python",
          code: "{#literal} [@literal] @fig:literal /Volumes/literal",
        },
      },
      {
        selectionId: "link:local",
        semanticId: null,
        kind: "paragraph",
        line: 56,
        state: "ready",
        markers: [],
        content: {
          type: "text",
          text: "",
          level: null,
          runs: [
            {
              type: "hyperlink",
              text: "本地文件 {#link:raw}",
              destination: "/Volumes/secret/thesis.md",
            },
            {
              type: "hyperlink",
              text: "远程文件 ref:target",
              destination: "https://example.test/doc?selectionId=secret#fig:raw",
            },
            {
              type: "hyperlink",
              text: "技术路径",
              destination: "https://example.test/source:source-meta",
            },
            {
              type: "hyperlink",
              text: "路径引用",
              destination: "https://example.test/cite-key",
            },
            {
              type: "hyperlink",
              text: "邮件引用",
              destination: "mailto:secret-key",
            },
            {
              type: "citation",
              keys: ["secret-key"],
              ordinals: [5],
              locator: null,
              text: "secret-key",
            },
            {
              type: "footnote-reference",
              label: "internal {#footnote:raw}",
              footnoteId: 4,
              text: "脚注4",
            },
          ],
        },
      },
    ]);
    const { container } = render(
      <ReviewPanel state={state} onActivated={() => undefined} />,
    );

    expect(screen.getByText("列表")).toBeVisible();
    expect(screen.getByText("数据")).toBeVisible();
    const math = screen.getByRole("math");
    expect(math).toHaveTextContent("(a)/(b) + √(x)");
    expect(math.textContent).toContain("\n");
    expect(math.textContent).not.toContain("\\");
    expect(math.textContent).not.toContain("$$");
    expect(math.getAttribute("aria-label")).not.toContain("\\");
    expect(math.getAttribute("aria-label")).not.toContain("$$");
    expect(screen.getByText("脚注正文")).toBeVisible();
    expect(screen.getByText(/作者。标题。/)).toBeVisible();
    expect(screen.getByText("[5]")).toBeVisible();
    expect(screen.getByText("说明")).toBeVisible();
    expect(
      screen.getByRole("img", { name: "图片 说明" }),
    ).toBeVisible();
    const code = screen.getByText(
      "{#literal} [@literal] @fig:literal /Volumes/literal",
    );
    expect(code).toBeVisible();
    expect(code.closest("pre")).not.toBeNull();
    expect(container.querySelector('a[href*="/Volumes/"]')).toBeNull();
    expect(container.querySelector('a[href*="fig:raw"]')).toBeNull();
    expect(container.querySelector('a[href*="selectionId"]')).toBeNull();
    expect(container.querySelector('a[href*="source:source-meta"]')).toBeNull();
    expect(container.querySelector('a[href*="cite-key"]')).toBeNull();
    expect(container.querySelector('a[href^="mailto:"]')).toBeNull();
    expect(container.querySelector('img[src*="fig:raw"]')).toBeNull();
    expect(container.querySelector('img[src*="source"]')).toBeNull();
    expect(screen.getByTitle("脚注 4")).toBeVisible();
    const nonCode = container.querySelector(".review-document")!
      .cloneNode(true) as HTMLElement;
    nonCode.querySelectorAll("pre").forEach((node) => node.remove());
    expect(nonCode.textContent).not.toContain("secret-key");
    expect(nonCode.textContent).not.toContain("{#");
    expect(nonCode.textContent).not.toContain("[@");
    expect(nonCode.textContent).not.toContain("/Volumes/secret");
    expect(nonCode.textContent).not.toContain("/private/");
    expect(nonCode.textContent).not.toContain("/tmp/");
    expect(nonCode.textContent).not.toContain("/Users/secret");
    expect(nonCode.textContent).not.toContain("/workspace/");
    expect(nonCode.textContent).not.toContain("/mnt/");
    expect(nonCode.textContent).not.toContain("ref:target");
    expect(nonCode.textContent).not.toContain("figure:raw");
    expect(nonCode.textContent).not.toContain("source:source-meta");
    expect(nonCode.textContent).not.toContain("target:target-meta");
    expect(nonCode.textContent).not.toContain("selection:selection-meta");
    expect(nonCode.textContent).not.toContain("node:node-meta");
    expect(nonCode.textContent).not.toContain("line:line-meta");
    for (const element of container.querySelectorAll<HTMLElement>(
      "[aria-label], [title], [href], [src]",
    )) {
      const attributes = ["aria-label", "title", "href", "src"]
        .map((name) => element.getAttribute(name) ?? "")
        .join(" ");
      expect(attributes).not.toMatch(
        /(?:\{#|@\w|(?:para|fn|ref|footnote|figure|source|target|selection|node|line):|\/workspace\/|\/mnt\/)/,
      );
    }
    expect(screen.getByRole("button", { name: "列表" })).toHaveAttribute(
      "aria-label",
      "列表",
    );
  });

  it("supports source navigation and explicit empty or blocked states", async () => {
    const user = userEvent.setup();
    const activated = vi.fn();
    const state = stateWithBlocks([
      {
        selectionId: "chap:intro",
        semanticId: "chap:intro",
        kind: "heading",
        line: 8,
        state: "ready",
        markers: [],
        content: {
          type: "text",
          text: "绪论",
          level: 1,
          runs: [],
        },
      },
    ]);
    const { rerender } = render(
      <ReviewPanel state={state} onActivated={activated} />,
    );

    const block = screen.getByRole("button", { name: "绪论" });
    await user.click(block);
    expect(activated).toHaveBeenCalledWith({
      selectionId: "chap:intro",
      line: 8,
    });
    block.focus();
    await user.keyboard("{Enter}");
    expect(activated).toHaveBeenCalledTimes(2);

    rerender(
      <ReviewPanel
        state={createInitialWorkspaceState()}
        onActivated={() => undefined}
      />,
    );
    expect(screen.getByText("等待载入文档")).toBeVisible();

    rerender(
      <ReviewPanel
        state={{
          ...state,
          preview: {
            status: "blocked",
            message:
              "存在 1 个错误诊断，无法生成 Review。cite-key para:secret /workspace/private ref:target",
            disclaimer: "结构预览不代表 Word 最终分页。",
            blocks: [],
          },
        }}
        onActivated={() => undefined}
      />,
    );
    expect(screen.getByText("内容审阅暂不可用")).toBeVisible();
    expect(
      screen.getByText("存在 1 个错误诊断，无法生成 Review。"),
    ).toBeVisible();
    expect(
      screen.queryByText(/cite-key|para:secret|\/workspace\/private|ref:target/),
    ).toBeNull();
  });
});
