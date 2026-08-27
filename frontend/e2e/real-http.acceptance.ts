import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_DOCX_FILENAME,
  DEFAULT_SOURCE_FILENAME,
  MANIFEST_FILENAME,
  PROJECT_SCHEMA_VERSION,
} from "../src/transport/constants";

const workspaceRoot = fileURLToPath(
  new URL("../test-results/real-http-workspaces/", import.meta.url),
);
const manifestText = `schema: ${PROJECT_SCHEMA_VERSION}
project:
  id: real-http-acceptance
  language: zh-CN
document:
  source: ${DEFAULT_SOURCE_FILENAME}
metadata:
  title:
    zh: 真实 HTTP 验收
  authors:
    - name: 测试作者
render:
  template_id: docforge-standard
`;
const sourceText = `# 绪论 {#chap:introduction}

初始正文。
`;
const savedText = sourceText.replace(
  "初始正文。",
  "通过真实 HTTP adapter 保存。",
);

test("runs the Web workbench through the real Python HTTP adapter", async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.goto("/");

  const workspaceResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/workspaces") &&
      response.request().method() === "POST",
  );
  await page.locator('input[type="file"]').setInputFiles([
    {
      name: MANIFEST_FILENAME,
      mimeType: "application/yaml",
      buffer: Buffer.from(manifestText),
    },
    {
      name: DEFAULT_SOURCE_FILENAME,
      mimeType: "text/markdown",
      buffer: Buffer.from(sourceText),
    },
  ]);
  const workspaceResponse = await workspaceResponsePromise;
  expect(workspaceResponse.status()).toBe(201);
  expect(workspaceResponse.headers()["x-docforge-adapter"]).toBe(
    "python-wsgi",
  );
  const workspacePayload = (await workspaceResponse.json()) as {
    project: { id: string; root: string; manifestPath: string };
    source: { workspaceId: string; fileName: string };
  };
  const workspaceId = workspacePayload.source.workspaceId;
  expect(workspacePayload.project.id).toBe("real-http-acceptance");
  expect(workspacePayload.project.root).not.toContain(workspaceRoot);
  expect(workspacePayload.project.manifestPath).not.toContain(workspaceRoot);
  expect(workspacePayload.source.fileName).toBe(DEFAULT_SOURCE_FILENAME);

  const editor = page.getByRole("textbox", { name: "Markdown 文档内容" });
  await expect(editor).toHaveValue(sourceText);
  await page.getByRole("tab", { name: "结构" }).click();
  await expect(page.getByText("结构预览不代表 Word 最终分页。")).toBeVisible();

  await editor.fill(savedText);
  await expect(page.getByRole("button", { name: "检查文档" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "生成 DOCX" })).toBeDisabled();

  const saveResponsePromise = page.waitForResponse((response) => {
    if (!response.url().endsWith("/api/v1/dispatch")) {
      return false;
    }
    return response.request().postDataJSON().operation === "save";
  });
  await page.getByRole("button", { name: "保存文档" }).click();
  expect((await saveResponsePromise).status()).toBe(200);
  await expect(page.getByText("文档、模板与预览已同步")).toBeVisible();
  await expect(page.getByRole("button", { name: "检查文档" })).toBeEnabled();

  const validateResponsePromise = page.waitForResponse((response) => {
    if (!response.url().endsWith("/api/v1/dispatch")) {
      return false;
    }
    return response.request().postDataJSON().operation === "preview";
  });
  await page.getByRole("button", { name: "检查文档" }).click();
  const validatePayload = (await (
    await validateResponsePromise
  ).json()) as { ok: boolean };
  expect(validatePayload.ok).toBe(true);

  const buildResponsePromise = page.waitForResponse((response) => {
    if (!response.url().endsWith("/api/v1/build-stream")) {
      return false;
    }
    const request = response.request().postDataJSON() as {
      payload?: { intent?: string };
    };
    return request.payload?.intent === "publish";
  });
  await page.getByRole("button", { name: "生成 DOCX" }).click();
  expect((await buildResponsePromise).status()).toBe(200);
  await expect(page.getByText("构建完成")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(DEFAULT_DOCX_FILENAME)).toBeVisible({
    timeout: 30_000,
  });

  expect(
    await readFile(
      `${workspaceRoot}/${workspaceId}/${DEFAULT_SOURCE_FILENAME}`,
      "utf8",
    ),
  ).toBe(savedText);
  expect(
    await readFile(
      `${workspaceRoot}/${workspaceId}/${MANIFEST_FILENAME}`,
      "utf8",
    ),
  ).toBe(manifestText);
  const docx = await readFile(
    `${workspaceRoot}/${workspaceId}/${DEFAULT_DOCX_FILENAME}`,
  );
  expect(docx.byteLength).toBeGreaterThan(1_000);
  expect(docx.subarray(0, 2).toString("ascii")).toBe("PK");
});
