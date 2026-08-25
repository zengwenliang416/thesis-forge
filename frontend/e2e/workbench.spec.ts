import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import type { BuildReport } from "../src/transport/buildEvents";

const workspaceId = "a".repeat(32);
const sourceText = "# 绪论\n";
const manifestText = `schema: thesisforge.project.v2
project:
  id: mocked-workbench
  source: thesis.md
template:
  id: example-university-2026
`;
const projectIdentity = {
  id: "mocked-workbench",
  root: "/workspace/thesis",
  manifestPath: "/workspace/thesis/thesisforge.yaml",
};
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
const BUILD_STAGES = [
  "parse",
  "validate",
  "compile",
  "render",
  "finalize",
  "postflight",
  "preview",
] as const;

type BuildOutput = NonNullable<BuildReport["output"]>;

function completedBuildEvent(
  requestId: string,
  output: BuildOutput,
  intent: BuildReport["intent"] = "publish",
) {
  const report: BuildReport = {
    schemaVersion: "thesisforge.build-report.v2",
    buildId: requestId,
    intent,
    outcome: "succeeded",
    stages: BUILD_STAGES.map((name) => ({ name, status: "succeeded" as const })),
    failedStage: null,
    primaryDiagnosticId: null,
    diagnostics: [],
    logs: [],
    output,
  };
  return {
    protocol: "thesisforge.workbench.v1",
    requestId,
    type: "completed",
    report,
  };
}

function openedProjectResponse() {
  return {
    protocol: "thesisforge.workbench.v1",
    ok: true,
    project: projectIdentity,
    source: {
      kind: "web-workspace",
      workspaceId,
      fileName: "thesis.md",
    },
    text: sourceText,
  };
}

function projectFiles() {
  return [
    {
      name: "thesisforge.yaml",
      mimeType: "text/yaml",
      buffer: Buffer.from(manifestText),
    },
    {
      name: "thesis.md",
      mimeType: "text/markdown",
      buffer: Buffer.from(sourceText),
    },
  ];
}

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

function onePagePdf(): Buffer {
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
    "<< /Length 61 >>\nstream\nBT /F1 24 Tf 72 720 Td (ThesisForge PDF Preview) Tj ET\nendstream",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  const chunks = [Buffer.from("%PDF-1.4\n%\xe2\xe3\xcf\xd3\n", "binary")];
  const offsets = [0];
  for (const [index, object] of objects.entries()) {
    offsets.push(Buffer.concat(chunks).length);
    chunks.push(Buffer.from(`${index + 1} 0 obj\n${object}\nendobj\n`, "ascii"));
  }
  const xrefOffset = Buffer.concat(chunks).length;
  const xref = [
    `xref\n0 ${objects.length + 1}\n`,
    "0000000000 65535 f \n",
    ...offsets
      .slice(1)
      .map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`),
    `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\n`,
    `startxref\n${xrefOffset}\n%%EOF\n`,
  ].join("");
  chunks.push(Buffer.from(xref, "ascii"));
  return Buffer.concat(chunks);
}

test("launches the shared workbench with keyboard-visible controls", async (
  { page },
  testInfo,
) => {
  await page.goto("/");

  await expect(page.getByText("ThesisForge", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "打开 ThesisForge 项目" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Markdown 编辑器" })).toBeVisible();
  if (testInfo.project.name !== "mobile-chromium") {
    await expect(
      page.getByRole("region", { name: "论文最终版式预览" }),
    ).toBeVisible();
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
  await page.getByRole("tab", { name: "预览" }).click();
  await expect(page.getByRole("tab", { name: "实时版式" })).toBeVisible();
  await expect(
    page.getByRole("region", { name: "论文最终版式预览" }),
  ).toBeVisible();
  await expect(page.getByText("尚无最终版式")).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true);
});

test("keeps the product identity and compact actions visible on mobile", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium");
  await page.goto("/");

  await expect(page.getByText("ThesisForge", { exact: true })).toBeVisible();
  const controls = [
    page.getByRole("button", { name: "打开 ThesisForge 项目" }),
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
      body: JSON.stringify(openedProjectResponse()),
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
  await page.route("**/api/v1/build-stream", async (route) => {
    const request = route.request().postDataJSON() as Record<string, unknown>;
    operations.push(request);
    const requestId = String(request.requestId);
    const events = [
      ...["parse", "validate", "compile", "render", "finalize"].map(
        (stage) => ({
          protocol: "thesisforge.workbench.v1",
          requestId,
          type: "progress",
          stage,
        }),
      ),
      completedBuildEvent(requestId, {
        docxPath: "/tmp/thesis.docx",
        pdfPath: null,
        previewStale: false,
        successfulBuildId: requestId,
      }),
    ];
    await route.fulfill({
      status: 200,
      contentType: "application/x-ndjson",
      body: `${events.map((event) => JSON.stringify(event)).join("\n")}\n`,
    });
  });
  await page.goto("/");

  await page.locator('input[type="file"]').setInputFiles(projectFiles());
  const editor = page.getByRole("textbox", { name: "Markdown 文稿内容" });
  await expect(editor).toHaveValue("# 绪论\n");
  await page.getByRole("tab", { name: "结构" }).click();
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

  await expect
    .poll(
      () =>
        operations.filter(
          (request) =>
            request.operation !== "build" ||
            (request.payload as { intent?: string }).intent === "publish",
        ).length,
    )
    .toBe(4);
  const userOperations = operations.filter(
    (request) =>
      request.operation !== "build" ||
      (request.payload as { intent?: string }).intent === "publish",
  );
  expect(userOperations.map((request) => request.operation)).toEqual([
    "preview",
    "save",
    "preview",
    "build",
  ]);
  expect(userOperations[1]).toMatchObject({
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
  expect(userOperations[3]).toMatchObject({
    operation: "build",
    payload: {
      intent: "publish",
      output: {
        kind: "web-download",
        workspaceId,
        fileName: "thesis.docx",
      },
    },
  });
  await expect(page.getByText("构建完成")).toBeVisible();
  await expect(page.getByText("thesis.docx")).toBeVisible();
});

test("loads and refreshes a complete automatic PDF after an edit", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  const pdfBytes = onePagePdf();
  let livePreviewBuilds = 0;
  let livePreviewReads = 0;
  await page.route("**/api/v1/workspaces", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(openedProjectResponse()),
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
        result: request.operation === "preview" ? previewResult : {},
      }),
    });
  });
  await page.route("**/api/v1/build-stream", async (route) => {
    const request = route.request().postDataJSON() as {
      requestId: string;
      payload: {
        intent?: string;
        output: {
          fileName: string;
          livePreviewId?: string;
        };
      };
    };
    const livePreview = request.payload.intent === "live-preview";
    if (livePreview) {
      livePreviewBuilds += 1;
    }
    const outputName = request.payload.output.fileName;
    const finalPreview = {
      engine: "libreoffice" as const,
      label: "LibreOffice PDF" as const,
      fileName: outputName.replace(/\.docx$/i, ".preview.pdf"),
      downloadId: workspaceId,
      ...(livePreview
        ? { livePreviewId: request.payload.output.livePreviewId }
        : {}),
    };
    await route.fulfill({
      status: 200,
      contentType: "application/x-ndjson",
      body: `${JSON.stringify(
        completedBuildEvent(
          request.requestId,
          {
            docxPath: `/tmp/${outputName}`,
            pdfPath: null,
            previewStale: false,
            successfulBuildId: request.requestId,
            finalPreview,
          },
          livePreview ? "live-preview" : "publish",
        ),
      )}\n`,
    });
  });
  await page.route(
    `**/api/v1/workspaces/${workspaceId}/live-previews/*`,
    async (route) => {
      livePreviewReads += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/pdf",
        body: pdfBytes,
        headers: {
          "cache-control": "no-store",
          "x-content-type-options": "nosniff",
        },
      });
    },
  );
  await page.goto("/");
  await page.locator('input[type="file"]').setInputFiles(projectFiles());

  await expect(page.getByText("LibreOffice PDF")).toBeVisible();
  await expect(page.getByText("当前 Office 预览")).toBeVisible();
  await expect.poll(() => livePreviewBuilds).toBe(1);
  await expect.poll(() => livePreviewReads).toBe(1);
  await expect(page.getByTitle("最终版式 PDF")).toHaveAttribute(
    "src",
    /^blob:/,
  );

  await page
    .getByRole("textbox", { name: "Markdown 文稿内容" })
    .fill("# 绪论\n\n修改后的正文。\n");
  await expect(page.getByText("已过期", { exact: true })).toBeVisible();
  await expect.poll(() => livePreviewBuilds).toBe(2);
  await expect.poll(() => livePreviewReads).toBe(2);
  await expect(page.getByText("当前 Office 预览")).toBeVisible();
  await expect(page.getByTitle("最终版式 PDF")).toBeVisible();
});

test("cancels an active Web build and retries without losing prior output", async ({
  page,
}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  const pending: { release: (() => void) | null } = { release: null };
  let buildCount = 0;
  let cancelCount = 0;
  await page.route("**/api/v1/build-cancel", async (route) => {
    cancelCount += 1;
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });
  await page.route("**/api/v1/build-stream", async (route) => {
    buildCount += 1;
    const request = route.request().postDataJSON() as { requestId: string };
    if (buildCount === 1) {
      await new Promise<void>((resolve) => {
        pending.release = resolve;
      });
      try {
        await route.fulfill({
          status: 200,
          contentType: "application/x-ndjson",
          body: "",
        });
      } catch {
        // The browser aborted the first request as part of cooperative cancel.
      }
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/x-ndjson",
      body: `${JSON.stringify(
        completedBuildEvent(request.requestId, {
          docxPath: "/tmp/retry.docx",
          pdfPath: null,
          previewStale: false,
          successfulBuildId: request.requestId,
        }),
      )}\n`,
    });
  });
  await page.route("**/api/v1/dispatch", async (route) => {
    const request = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        protocol: "thesisforge.workbench.v1",
        requestId: request.requestId,
        ok: true,
        result: previewResult,
      }),
    });
  });
  await page.route("**/api/v1/workspaces", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(openedProjectResponse()),
    });
  });
  await page.goto("/");
  await page.locator('input[type="file"]').setInputFiles(projectFiles());

  await page.getByRole("button", { name: "构建 DOCX" }).click();
  await expect(page.getByRole("button", { name: "取消构建" })).toBeVisible();
  await page.getByRole("button", { name: "取消构建" }).click();
  await expect(page.getByText("操作已取消")).toBeVisible();
  await expect(page.getByRole("button", { name: "构建 DOCX" })).toBeEnabled();
  pending.release?.();
  await expect.poll(() => cancelCount).toBe(1);

  await page.getByRole("button", { name: "构建 DOCX" }).click();
  await expect(page.getByText("retry.docx")).toBeVisible();
  await expect(page.getByText("构建完成")).toBeVisible();
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
      body: JSON.stringify(openedProjectResponse()),
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

  await page.locator('input[type="file"]').setInputFiles(projectFiles());
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
    page.getByRole("button", { name: "打开 ThesisForge 项目" }),
  ).toBeFocused();
  const separator = page.getByRole("separator", { name: "调整大纲宽度" });
  await separator.focus();
  await page.keyboard.press("ArrowRight");
  await expect(separator).toHaveAttribute("aria-valuenow", "276");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true);
});
