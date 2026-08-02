import assert from "node:assert/strict";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { $, browser } from "@wdio/globals";

const sourcePath = process.env.THESISFORGE_WINDOWS_SOURCE;
const evidenceDirectory = process.env.THESISFORGE_WINDOWS_EVIDENCE;
const appBinaryPath = process.env.THESISFORGE_WINDOWS_APP;

if (!sourcePath || !evidenceDirectory || !appBinaryPath) {
  throw new Error(
    "THESISFORGE_WINDOWS_SOURCE, THESISFORGE_WINDOWS_EVIDENCE, and " +
      "THESISFORGE_WINDOWS_APP are required",
  );
}

const outputPath = sourcePath.replace(/\.md$/i, ".docx");
const marker = "<!-- windows native acceptance -->";

describe("installed Windows Tauri acceptance", () => {
  it("opens, saves, validates, builds, and records sensory evidence", async () => {
    const sourceText = await readFile(sourcePath, "utf8");
    await mkdir(evidenceDirectory, { recursive: true });

    const webdriverActive = await browser.execute(() => navigator.webdriver);
    assert.equal(webdriverActive, true);

    await browser.execute(
      (fixture: { path: string; fileName: string; text: string }) => {
        const internals = (
          window as unknown as {
            __TAURI_INTERNALS__: {
              invoke(
                command: string,
                args?: Record<string, unknown>,
                options?: Record<string, unknown>,
              ): Promise<unknown>;
            };
          }
        ).__TAURI_INTERNALS__;
        const originalInvoke = internals.invoke.bind(internals);
        internals.invoke = (command, args, options) => {
          if (command === "pick_source") {
            return Promise.resolve({
              source: {
                kind: "desktop",
                path: fixture.path,
                fileName: fixture.fileName,
              },
              text: fixture.text,
            });
          }
          return originalInvoke(command, args, options);
        };
      },
      {
        path: sourcePath,
        fileName: path.basename(sourcePath),
        text: sourceText,
      },
    );

    const shell = await $(".app-shell");
    await shell.waitForDisplayed();
    assert.equal(await shell.getAttribute("data-runtime"), "tauri");
    assert.match(await shell.getText(), /本地桌面/);

    const open = await $('aria/打开 Markdown 文稿');
    await open.click();

    const editor = await $('aria/Markdown 文稿内容');
    await browser.waitUntil(
      async () => (await editor.getValue()).includes("thesis:"),
      { timeoutMsg: "installed app did not populate the complete example" },
    );

    await browser.keys(["Control", "k"]);
    assert.equal(await editor.isFocused(), true);
    await browser.keys(["Control", "End"]);
    await editor.addValue(`\n${marker}\n`);

    const save = await $('aria/保存文稿');
    await save.waitForEnabled();
    await save.click();
    await browser.waitUntil(
      async () => (await readFile(sourcePath, "utf8")).includes(marker),
      { timeoutMsg: "installed app did not persist the edited source" },
    );

    const validate = await $('aria/验证论文');
    await validate.waitForEnabled();
    await validate.click();
    await browser.waitUntil(
      async () => (await shell.getAttribute("data-state")) === "populated",
      { timeoutMsg: "installed app did not complete native validation" },
    );

    const build = await $('aria/构建 DOCX');
    await build.waitForEnabled();
    await build.click();
    const progress = await $('aria/构建进度');
    await browser.waitUntil(
      async () => (await progress.getText()).includes("构建完成"),
      {
        timeout: 90_000,
        timeoutMsg: "installed app did not complete the packaged sidecar build",
      },
    );
    assert.match(await $('aria/输出结果').getText(), /thesis\.docx/);

    const output = await readFile(outputPath);
    assert.equal(output.subarray(0, 2).toString("ascii"), "PK");
    assert.ok((await stat(outputPath)).size > 1_000);

    const sensory = await browser.execute(() => {
      const reducedMotionRule = Array.from(document.styleSheets).some(
        (sheet) => {
          try {
            return Array.from(sheet.cssRules).some((rule) =>
              rule.cssText.includes("prefers-reduced-motion"),
            );
          } catch {
            return false;
          }
        },
      );
      return {
        title: document.title,
        runtime: document.querySelector(".app-shell")?.getAttribute("data-runtime"),
        state: document.querySelector(".app-shell")?.getAttribute("data-state"),
        activeLabel: document.activeElement?.getAttribute("aria-label"),
        reducedMotionRule,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
      };
    });
    assert.equal(sensory.runtime, "tauri");
    assert.equal(sensory.state, "populated");
    assert.equal(sensory.reducedMotionRule, true);

    const screenshotPath = path.join(
      evidenceDirectory,
      "windows-native-acceptance.png",
    );
    await browser.saveScreenshot(screenshotPath);
    await writeFile(
      path.join(evidenceDirectory, "windows-native-acceptance.json"),
      JSON.stringify(
        {
          ok: true,
          appBinaryPath,
          sourcePath,
          outputPath,
          outputBytes: (await stat(outputPath)).size,
          webdriverActive,
          sensory,
          screenshotPath,
          completedAt: new Date().toISOString(),
        },
        null,
        2,
      ),
      "utf8",
    );
  });
});
