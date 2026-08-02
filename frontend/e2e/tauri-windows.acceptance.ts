import assert from "node:assert/strict";
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { chromium, type Browser, type Page } from "@playwright/test";

function requireEnvironment(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

const sourcePath = requireEnvironment("THESISFORGE_WINDOWS_SOURCE");
const evidenceDirectory = requireEnvironment("THESISFORGE_WINDOWS_EVIDENCE");
const appBinaryPath = requireEnvironment("THESISFORGE_WINDOWS_APP");
const cdpPort = Number(process.env.THESISFORGE_WINDOWS_CDP_PORT ?? "9222");

if (!Number.isInteger(cdpPort) || cdpPort < 1024 || cdpPort > 65_535) {
  throw new Error(`Invalid THESISFORGE_WINDOWS_CDP_PORT: ${cdpPort}`);
}

const outputPath = sourcePath.replace(/\.md$/i, ".docx");
const marker = "<!-- windows native acceptance -->";
const cdpEndpoint = `http://127.0.0.1:${cdpPort}`;

function captureProcessOutput(
  child: ChildProcess,
): { stdout: string[]; stderr: string[] } {
  const output = { stdout: [] as string[], stderr: [] as string[] };
  assert(child.stdout);
  assert(child.stderr);
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");
  child.stdout.on("data", (chunk: string) => {
    output.stdout.push(chunk);
    process.stdout.write(chunk);
  });
  child.stderr.on("data", (chunk: string) => {
    output.stderr.push(chunk);
    process.stderr.write(chunk);
  });
  return output;
}

async function waitForCdp(
  child: ChildProcess,
): Promise<Record<string, unknown>> {
  const deadline = Date.now() + 60_000;
  let lastError = "endpoint not requested";

  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(
        `Installed ThesisForge exited before CDP was ready: ${child.exitCode}`,
      );
    }
    try {
      const response = await fetch(`${cdpEndpoint}/json/version`, {
        signal: AbortSignal.timeout(2_000),
      });
      if (response.ok) {
        const endpoint = (await response.json()) as Record<string, unknown>;
        if (typeof endpoint.webSocketDebuggerUrl === "string") {
          return endpoint;
        }
        lastError = "CDP response did not include webSocketDebuggerUrl";
      } else {
        lastError = `CDP returned HTTP ${response.status}`;
      }
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Installed ThesisForge CDP endpoint was not ready: ${lastError}`);
}

async function waitForWorkbenchPage(browser: Browser): Promise<Page> {
  const deadline = Date.now() + 30_000;

  while (Date.now() < deadline) {
    for (const context of browser.contexts()) {
      for (const page of context.pages()) {
        if (page.isClosed()) {
          continue;
        }
        if ((await page.locator(".app-shell").count()) > 0) {
          return page;
        }
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Connected WebView2 target did not render the ThesisForge workbench");
}

async function waitForSavedSource(): Promise<void> {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    if ((await readFile(sourcePath, "utf8")).includes(marker)) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("Installed app did not persist the edited source");
}

function stopInstalledApp(child: ChildProcess): void {
  if (child.pid === undefined || child.exitCode !== null) {
    return;
  }
  spawnSync("taskkill.exe", ["/PID", String(child.pid), "/T", "/F"], {
    stdio: "ignore",
  });
}

async function main(): Promise<void> {
  await mkdir(evidenceDirectory, { recursive: true });
  const sourceText = await readFile(sourcePath, "utf8");
  const existingWebViewArgs =
    process.env.WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS?.trim();
  const webViewArgs = [
    existingWebViewArgs,
    `--remote-debugging-port=${cdpPort}`,
    "--remote-allow-origins=*",
  ]
    .filter(Boolean)
    .join(" ");
  const app = spawn(appBinaryPath, [], {
    env: {
      ...process.env,
      THESISFORGE_BLOCK_NETWORK: "1",
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: webViewArgs,
    },
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: false,
  });
  app.stdin?.end();
  const processOutput = captureProcessOutput(app);
  let browser: Browser | undefined;

  try {
    const endpoint = await waitForCdp(app);
    await writeFile(
      path.join(evidenceDirectory, "windows-cdp-endpoint.json"),
      JSON.stringify(endpoint, null, 2),
      "utf8",
    );
    browser = await chromium.connectOverCDP(cdpEndpoint);
    const page = await waitForWorkbenchPage(browser);
    const tauriInternals = await page.evaluate(() => {
      const candidate = window as unknown as {
        __TAURI_INTERNALS__?: unknown;
      };
      return typeof candidate.__TAURI_INTERNALS__ === "object";
    });
    assert.equal(tauriInternals, true);

    await page.evaluate<
      void,
      { path: string; fileName: string; text: string }
    >(
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

    const shell = page.locator(".app-shell");
    await shell.waitFor({ state: "visible" });
    assert.equal(await shell.getAttribute("data-runtime"), "tauri");
    assert.match(await shell.innerText(), /本地桌面/);

    await page.getByRole("button", { name: "打开 Markdown 文稿" }).click();
    const editor = page.getByLabel("Markdown 文稿内容");
    await editor.waitFor({ state: "visible" });
    await page.waitForFunction(
      () =>
        (
          document.querySelector(
            '[aria-label="Markdown 文稿内容"]',
          ) as HTMLTextAreaElement | null
        )?.value.includes("thesis:") === true,
    );

    await page.keyboard.press("Control+k");
    assert.equal(
      await editor.evaluate((element) => element === document.activeElement),
      true,
    );
    await editor.press("Control+End");
    await editor.press("Enter");
    await editor.type(marker);

    const save = page.getByRole("button", { name: "保存文稿" });
    await save.waitFor({ state: "visible" });
    assert.equal(await save.isEnabled(), true);
    await save.click();
    await waitForSavedSource();

    const validate = page.getByRole("button", { name: "验证论文" });
    assert.equal(await validate.isEnabled(), true);
    await validate.click();
    await page.waitForFunction(
      () => document.querySelector(".app-shell")?.getAttribute("data-state") === "populated",
    );

    const build = page.getByRole("button", { name: "构建 DOCX" });
    assert.equal(await build.isEnabled(), true);
    await build.click();
    const progress = page.getByLabel("构建进度");
    await progress.getByText("构建完成", { exact: false }).waitFor({
      timeout: 90_000,
    });
    assert.match(await page.getByLabel("输出结果").innerText(), /thesis\.docx/);

    const output = await readFile(outputPath);
    assert.equal(output.subarray(0, 2).toString("ascii"), "PK");
    assert.ok((await stat(outputPath)).size > 1_000);

    const sensory = await page.evaluate(() => {
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
    await page.screenshot({ path: screenshotPath });
    await writeFile(
      path.join(evidenceDirectory, "windows-native-acceptance.json"),
      JSON.stringify(
        {
          ok: true,
          appBinaryPath,
          sourcePath,
          outputPath,
          outputBytes: (await stat(outputPath)).size,
          automation: "playwright-cdp",
          cdpEndpoint,
          tauriInternals,
          externalSocketsBlocked: true,
          sensory,
          screenshotPath,
          completedAt: new Date().toISOString(),
        },
        null,
        2,
      ),
      "utf8",
    );
  } finally {
    await writeFile(
      path.join(evidenceDirectory, "windows-app-output.json"),
      JSON.stringify(processOutput, null, 2),
      "utf8",
    );
    await browser?.close().catch(() => undefined);
    stopInstalledApp(app);
  }
}

await main();
