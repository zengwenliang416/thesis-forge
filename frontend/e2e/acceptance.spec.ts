import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const workspaceId = "b".repeat(32);
const previewFixture = JSON.parse(
  readFileSync(
    new URL("../../tests/fixtures/preview-workbench-v1.json", import.meta.url),
    "utf8",
  ),
) as Record<string, unknown>;
const acceptedPreview = {
  ...previewFixture,
  diagnostics: [],
};

test.beforeEach(async ({ page }) => {
  let livePreviewSequence = 0;
  await page.route("**/api/v1/live-previews", async (route) => {
    livePreviewSequence += 1;
    const request = route.request().postDataJSON() as {
      source: { workspaceId: string };
    };
    const livePreviewId = livePreviewSequence.toString(16).padStart(32, "0");
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        ok: true,
        output: {
          kind: "web-download",
          workspaceId: request.source.workspaceId,
          fileName: `.thesisforge-live-preview-${livePreviewId}.docx`,
          livePreviewId,
        },
      }),
    });
  });
  await page.route("**/api/v1/live-previews/discard", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        ok: true,
      }),
    });
  });
});

function contrastRatio(
  foreground: [number, number, number],
  background: [number, number, number],
) {
  const luminance = ([red, green, blue]: [number, number, number]) => {
    const channels = [red, green, blue].map((value) => {
      const channel = value / 255;
      return channel <= 0.03928
        ? channel / 12.92
        : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  };
  const light = luminance(foreground);
  const dark = luminance(background);
  return (Math.max(light, dark) + 0.05) / (Math.min(light, dark) + 0.05);
}

function rgb(value: string): [number, number, number] {
  const channels = value.match(/\d+/g)?.slice(0, 3).map(Number);
  if (!channels || channels.length !== 3) {
    throw new Error(`Unsupported computed color: ${value}`);
  }
  return channels as [number, number, number];
}

test("verifies empty, disabled, keyboard-focus, contrast, resize, and reduced motion", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name === "mobile-chromium");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");

  await expect(page.getByText("当前工作区没有 Markdown 文稿")).toBeVisible();
  if (testInfo.project.name === "desktop-chromium") {
    await expect(page.getByRole("button", { name: "保存文稿" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "验证论文" })).toBeDisabled();
  } else {
    await expect(page.getByRole("button", { name: "保存文稿" })).toBeHidden();
    await expect(page.getByRole("button", { name: "验证论文" })).toBeHidden();
  }
  await expect(page.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
  await expect(page.getByLabel("学校模板")).toBeDisabled();

  await page.keyboard.press("Tab");
  const open = page.getByRole("button", { name: "打开 Markdown 文稿" });
  await expect(open).toBeFocused();
  const focusStyle = await open.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
      transitionDuration: style.transitionDuration,
      animationDuration: style.animationDuration,
    };
  });
  expect(focusStyle.outlineStyle).not.toBe("none");
  expect(Number.parseFloat(focusStyle.outlineWidth)).toBeGreaterThanOrEqual(3);
  expect(Number.parseFloat(focusStyle.transitionDuration)).toBeLessThanOrEqual(0.01);
  expect(Number.parseFloat(focusStyle.animationDuration)).toBeLessThanOrEqual(0.01);

  const statusColors = await page.locator(".status-strip").evaluate((element) => {
    const style = getComputedStyle(element);
    return { color: style.color, background: style.backgroundColor };
  });
  expect(contrastRatio(rgb(statusColors.color), rgb(statusColors.background))).toBeGreaterThanOrEqual(
    7,
  );

  await page.setViewportSize({ width: 1024, height: 680 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true);
});

test("saves with Ctrl+S when the minimum desktop toolbar hides secondary actions", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "minimum-desktop-chromium");
  let savedText: string | undefined;
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
    const request = route.request().postDataJSON() as {
      requestId: string;
      operation: string;
      payload: { text?: string };
    };
    if (request.operation === "save") {
      savedText = request.payload.text;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        ok: true,
        result: request.operation === "preview" ? acceptedPreview : {},
      }),
    });
  });
  await page.goto("/");
  const sourceText = "# 绪论\n";
  await page.locator('input[type="file"]').setInputFiles({
    name: "thesis.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(sourceText),
  });

  const editor = page.getByRole("textbox", { name: "Markdown 文稿内容" });
  await page.keyboard.press("Control+k");
  await expect(editor).toBeFocused();
  const editedText = `${await editor.inputValue()}\n最小桌面宽度保存回归。\n`;
  await editor.fill(editedText);
  await expect(editor).toHaveValue(editedText);
  await expect(page.getByText("文稿有未保存修改")).toBeVisible();
  const save = page.locator('[aria-label="保存文稿"]');
  await expect(save).toHaveCount(1);
  await expect(save).toBeHidden();
  await expect(save).toBeEnabled();

  await page.keyboard.press("Control+s");

  await expect.poll(() => savedText).toBe(editedText);
  await expect(page.getByText("文稿、模板与预览已同步")).toBeVisible();
});

test("verifies loading and permission recovery without losing the opened source", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  let releaseWorkspace: (() => void) | undefined;
  await page.route("**/api/v1/workspaces", async (route) => {
    await new Promise<void>((resolve) => {
      releaseWorkspace = resolve;
    });
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
    const request = route.request().postDataJSON() as { requestId: string };
    await route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        ok: false,
        error: {
          kind: "permission",
          message: "目标目录没有写入权限",
        },
      }),
    });
  });
  await page.goto("/");

  const upload = page.locator('input[type="file"]').setInputFiles({
    name: "thesis.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 绪论\n"),
  });
  await expect(page.getByText("正在读取工作区")).toBeVisible();
  await expect(page.getByRole("button", { name: "打开 Markdown 文稿" })).toBeDisabled();
  releaseWorkspace?.();
  await upload;

  await expect(page.getByText("目标位置不可写")).toBeVisible();
  await expect(page.getByText("目标目录没有写入权限")).toBeVisible();
  await expect(page.getByRole("button", { name: "恢复工作区" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Markdown 文稿内容" })).toHaveValue(
    "# 绪论\n",
  );
});

test("verifies populated, dirty, and successful output states with the complete preview", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
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
    const request = route.request().postDataJSON() as {
      requestId: string;
      operation: string;
    };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        ok: true,
        result: request.operation === "preview" ? acceptedPreview : {},
      }),
    });
  });
  await page.route("**/api/v1/build-stream", async (route) => {
    const request = route.request().postDataJSON() as { requestId: string };
    const events = [
      ...["parse", "validate", "compile", "render", "finalize"].map((stage) => ({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        type: "progress",
        stage,
      })),
      {
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        type: "success",
        result: {
          output: {
            kind: "web-download",
            name: "accepted.docx",
            downloadId: workspaceId,
          },
          diagnostics: [],
        },
      },
    ];
    await route.fulfill({
      status: 200,
      contentType: "application/x-ndjson",
      body: `${events.map((event) => JSON.stringify(event)).join("\n")}\n`,
    });
  });
  await page.goto("/");
  await page.locator('input[type="file"]').setInputFiles({
    name: "thesis.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# 绪论\n"),
  });

  await expect(page.getByText("文稿、模板与预览已同步")).toBeVisible();
  await page.getByRole("tab", { name: "结构" }).click();
  await expect(page.getByText("结构预览不代表 Word 最终分页。")).toBeVisible();
  const editor = page.getByRole("textbox", { name: "Markdown 文稿内容" });
  await editor.fill("# 绪论\n\n已修改。\n");
  await expect(page.getByText("文稿有未保存修改")).toBeVisible();
  await expect(page.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();
  await page.getByRole("button", { name: "保存文稿" }).click();
  await page.getByRole("button", { name: "构建 DOCX" }).click();

  await expect(page.getByText("构建完成")).toBeVisible();
  await expect(page.getByText("accepted.docx")).toBeVisible();
});
