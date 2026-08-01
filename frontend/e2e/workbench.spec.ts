import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const workspaceId = "a".repeat(32);
const previewFixture = JSON.parse(
  readFileSync(
    new URL("../../tests/fixtures/preview-workbench-v1.json", import.meta.url),
    "utf8",
  ),
) as Record<string, unknown> & {
  preview: Record<string, unknown>;
};
const previewResult = {
  ...previewFixture,
  diagnostics: [],
};

test("launches the shared workbench with keyboard-visible controls", async (
  { page },
  testInfo,
) => {
  await page.goto("/");

  await expect(page.getByText("ThesisForge")).toBeVisible();
  await expect(page.getByRole("button", { name: "打开 Markdown 文稿" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Markdown 编辑器" })).toBeVisible();
  if (testInfo.project.name !== "mobile-chromium") {
    await expect(page.getByRole("region", { name: "论文结构预览" })).toBeVisible();
    await expect(page.getByRole("region", { name: "诊断结果" })).toBeVisible();
  } else {
    await expect(page.getByRole("tab", { name: "编辑" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  }

  await page.keyboard.press("Control+K");
  await expect(page.getByRole("textbox", { name: "Markdown 文稿内容" })).toBeFocused();
});

test("uses mobile panel navigation without horizontal overflow", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium");
  await page.goto("/");

  await page.getByRole("tab", { name: "诊断" }).click();
  await expect(page.getByRole("tab", { name: "诊断" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByRole("region", { name: "诊断结果" })).toHaveAttribute(
    "data-mobile-active",
    "true",
  );
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true);
});

test("keeps the product identity and compact actions visible on mobile", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium");
  await page.goto("/");

  await expect(page.getByText("ThesisForge")).toBeVisible();
  const controls = [
    page.getByRole("button", { name: "打开 Markdown 文稿" }),
    page.getByRole("button", { name: "构建 DOCX" }),
    page.getByRole("tab", { name: "诊断" }),
  ];
  for (const control of controls) {
    await expect(control).toBeVisible();
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box?.x).toBeGreaterThanOrEqual(0);
    expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(
      await page.evaluate(() => window.innerWidth),
    );
  }
});

test("opens, edits, explicitly saves, refreshes, and builds through HTTP", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  const operations: Array<Record<string, unknown>> = [];
  await page.route("**/api/v1/workspaces", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        ok: true,
        source: {
          kind: "web-workspace",
          workspaceId,
          fileName: "thesis.md",
        },
        text: "# 绪论\n",
      }),
    });
  });
  await page.route("**/api/v1/dispatch", async (route) => {
    const request = route.request().postDataJSON() as Record<string, unknown>;
    operations.push(request);
    const result = request.operation === "preview" ? previewResult : {};
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        ok: true,
        result,
      }),
    });
  });
  await page.goto("/");

  await page.locator('input[type="file"]').setInputFiles({
    name: "thesis.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 绪论\n"),
  });
  const editor = page.getByRole("textbox", { name: "Markdown 文稿内容" });
  await expect(editor).toHaveValue("# 绪论\n");
  const outline = page.getByRole("complementary", { name: "论文大纲" });
  const outlineHeading = outline.getByRole("button", {
    name: /绪论.*第 8 行/,
  });
  await expect(outlineHeading).toBeVisible();
  await expect(page.getByText("系统架构")).toBeVisible();
  await expect(page.getByText("结构预览不代表 Word 最终分页。")).toBeVisible();
  await outlineHeading.click();
  await expect(outlineHeading).toHaveAttribute("aria-pressed", "true");
  await editor.fill("# 绪论\n\n正文。\n");
  await expect(page.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
  await page.getByRole("button", { name: "保存文稿" }).click();
  await expect(page.getByText("文稿、模板与预览已同步")).toBeVisible();
  await page.getByRole("button", { name: "构建 DOCX" }).click();

  await expect.poll(() => operations.length).toBe(4);
  expect(operations.map((request) => request.operation)).toEqual([
    "preview",
    "save",
    "preview",
    "build",
  ]);
  expect(operations[1]).toMatchObject({
    operation: "save",
    payload: {
      source: {
        kind: "web-workspace",
        workspaceId,
        fileName: "thesis.md",
      },
      text: "# 绪论\n\n正文。\n",
    },
  });
  expect(operations[3]).toMatchObject({
    operation: "build",
    payload: {
      output: {
        kind: "web-download",
        workspaceId,
        fileName: "thesis.docx",
      },
    },
  });
});

test("selects a template and blocks build on an activated fatal diagnostic", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  const operations: Array<Record<string, unknown>> = [];
  await page.route("**/api/v1/workspaces", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        ok: true,
        source: {
          kind: "web-workspace",
          workspaceId,
          fileName: "thesis.md",
        },
        text: "# 绪论\n",
      }),
    });
  });
  await page.route("**/api/v1/dispatch", async (route) => {
    const request = route.request().postDataJSON() as Record<string, unknown>;
    operations.push(request);
    const selectedTemplate =
      (request.payload as { templateId?: string | null }).templateId ??
      null;
    const diagnostics =
      request.operation === "preview" && selectedTemplate
        ? [
            {
              severity: "error",
              code: "missing-template-style",
              message: "Template does not define a required semantic style",
              line: 1,
              target: "heading.level1",
              details: {},
            },
          ]
        : [];
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        ok: true,
        result:
          request.operation === "preview"
            ? {
                ...previewFixture,
                diagnostics,
                preview:
                  diagnostics.length > 0
                    ? {
                        status: "blocked",
                        message: "存在 1 个错误诊断，无法生成结构预览。",
                        disclaimer: "结构预览不代表 Word 最终分页。",
                        blocks: [],
                      }
                    : previewFixture.preview,
              }
            : {},
      }),
    });
  });
  await page.goto("/");

  await page.locator('input[type="file"]').setInputFiles({
    name: "thesis.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 绪论\n"),
  });
  await page
    .getByLabel("学校模板")
    .selectOption("example-university-2026");

  await expect(page.getByText("模板未定义所需样式：heading.level1")).toBeVisible();
  await expect(page.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
  await expect(page.getByText("存在 1 个错误诊断，构建已禁用。")).toBeVisible();
  const diagnostic = page.getByRole("button", { name: /第 1 行/ });
  await diagnostic.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("textbox", { name: "Markdown 文稿内容" }),
  ).toBeFocused();

  expect(operations.at(-1)).toMatchObject({
    operation: "preview",
    payload: {
      templateId: "example-university-2026",
    },
  });
});

test("preserves keyboard focus order and panel resizing at desktop widths", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name === "mobile-chromium");
  await page.goto("/");

  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "打开 Markdown 文稿" }),
  ).toBeFocused();
  const separator = page.getByRole("separator", { name: "调整大纲宽度" });
  await separator.focus();
  await page.keyboard.press("ArrowRight");
  await expect(separator).toHaveAttribute("aria-valuenow", "276");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true);
});
