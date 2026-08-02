import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const workspaceRoot = fileURLToPath(
  new URL("../test-results/real-http-workspaces/", import.meta.url),
);
const sourceText = `---
document:
  type: bachelor_thesis
  language: zh-CN
  spec_version: "1.0"
thesis:
  title: "真实 HTTP 验收"
author:
  name: "测试作者"
render:
  template_id: "bachelor-base"
---

# 绪论 {#chap:introduction}

初始正文。
`;
const savedText = sourceText.replace(
  "初始正文。",
  "通过真实 HTTP adapter 保存。",
);

test("runs the Web workbench through the real Python HTTP adapter", async ({
  page,
}) => {
  await page.goto("/");

  const workspaceResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/workspaces") &&
      response.request().method() === "POST",
  );
  await page.locator('input[type="file"]').setInputFiles({
    name: "thesis.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(sourceText),
  });
  const workspaceResponse = await workspaceResponsePromise;
  expect(workspaceResponse.status()).toBe(201);
  expect(workspaceResponse.headers()["x-thesisforge-adapter"]).toBe(
    "python-wsgi",
  );
  const workspacePayload = (await workspaceResponse.json()) as {
    source: { workspaceId: string };
  };
  const workspaceId = workspacePayload.source.workspaceId;

  const editor = page.getByRole("textbox", { name: "Markdown 文稿内容" });
  await expect(editor).toHaveValue(sourceText);
  await expect(page.getByText("结构预览不代表 Word 最终分页。")).toBeVisible();

  await editor.fill(savedText);
  await expect(page.getByRole("button", { name: "验证论文" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "构建 DOCX" })).toBeDisabled();

  const saveResponsePromise = page.waitForResponse((response) => {
    if (!response.url().endsWith("/api/v1/dispatch")) {
      return false;
    }
    return response.request().postDataJSON().operation === "save";
  });
  await page.getByRole("button", { name: "保存文稿" }).click();
  expect((await saveResponsePromise).status()).toBe(200);
  await expect(page.getByText("文稿、模板与预览已同步")).toBeVisible();
  await expect(page.getByRole("button", { name: "验证论文" })).toBeEnabled();

  const validateResponsePromise = page.waitForResponse((response) => {
    if (!response.url().endsWith("/api/v1/dispatch")) {
      return false;
    }
    return response.request().postDataJSON().operation === "preview";
  });
  await page.getByRole("button", { name: "验证论文" }).click();
  const validatePayload = (await (
    await validateResponsePromise
  ).json()) as { ok: boolean };
  expect(validatePayload.ok).toBe(true);

  const buildResponsePromise = page.waitForResponse((response) =>
    response.url().endsWith("/api/v1/build-stream"),
  );
  await page.getByRole("button", { name: "构建 DOCX" }).click();
  expect((await buildResponsePromise).status()).toBe(200);
  await expect(page.getByText("构建完成")).toBeVisible();
  await expect(page.getByText("thesis.docx")).toBeVisible();

  expect(
    await readFile(`${workspaceRoot}/${workspaceId}/thesis.md`, "utf8"),
  ).toBe(savedText);
  const docx = await readFile(`${workspaceRoot}/${workspaceId}/thesis.docx`);
  expect(docx.byteLength).toBeGreaterThan(1_000);
  expect(docx.subarray(0, 2).toString("ascii")).toBe("PK");
});
