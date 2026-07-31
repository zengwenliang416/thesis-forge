"use strict";

const path = require("node:path");
const { chromium } = require("playwright");

const evidenceDir = __dirname;
const url = process.env.THESISFORGE_PROTOTYPE_URL || "http://127.0.0.1:49324/";

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  });

  try {
    const desktop = await browser.newPage({
      viewport: { width: 1440, height: 1000 },
      deviceScaleFactor: 1
    });
    await desktop.goto(url, { waitUntil: "networkidle" });
    await desktop.addStyleTag({
      content: "*, *::before, *::after { animation: none !important; transition: none !important; }"
    });
    await desktop.waitForTimeout(700);
    await desktop.screenshot({
      path: path.join(evidenceDir, "desktop-populated.png"),
      fullPage: true
    });

    const shellAnchors = await desktop.locator(
      '[data-specnav-project-shell="thesisforge-workbench"][data-state="populated"]'
    ).count();
    const screenAnchors = await desktop.locator(
      '[data-specnav-screen="thesisforge-workbench"][data-specnav-variant="academic-three-pane"]'
    ).count();

    const states = {};
    for (const state of ["populated", "loading", "empty", "error", "disabled", "permission"]) {
      await desktop.locator(`[data-state-target="${state}"]`).click();
      states[state] = {
        visible: await desktop.locator(`[data-state-view="${state}"]:visible`).count(),
        buildDisabled: await desktop.locator("#build-button").isDisabled(),
        shellState: await desktop.locator(".app-shell").getAttribute("data-state")
      };
    }

    await desktop.locator('[data-state-target="populated"]').click();
    await desktop.locator("#build-button").click();
    await desktop.locator("#build-progress.is-visible").waitFor();
    const buildFirstStage = await desktop.locator("#build-progress-title").innerText();
    await desktop.locator("#toast").waitFor({ state: "visible", timeout: 6000 });
    const buildToast = await desktop.locator("#toast").innerText();

    const mobile = await browser.newPage({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 1
    });
    await mobile.goto(url, { waitUntil: "networkidle" });
    await mobile.addStyleTag({
      content: "*, *::before, *::after { animation: none !important; transition: none !important; }"
    });
    await mobile.waitForTimeout(300);

    const mobilePanels = {};
    for (const panel of ["outline", "editor", "preview", "diagnostics"]) {
      await mobile.locator(`[data-panel-target="${panel}"]`).click();
      await mobile.waitForTimeout(220);
      mobilePanels[panel] = await mobile.locator(
        `[data-panel="${panel}"].is-mobile-active:visible`
      ).count();
    }

    await mobile.locator('[data-panel-target="preview"]').click();
    await mobile.waitForTimeout(260);
    await mobile.screenshot({
      path: path.join(evidenceDir, "mobile-preview.png"),
      fullPage: true
    });
    await mobile.locator('[data-state-target="permission"]').click();
    await mobile.waitForTimeout(220);
    await mobile.screenshot({
      path: path.join(evidenceDir, "mobile-permission.png"),
      fullPage: true
    });

    const result = {
      ok: true,
      title: await desktop.title(),
      shellAnchors,
      screenAnchors,
      states,
      buildFirstStage,
      buildToast,
      mobilePanels,
      desktopPanelOpacities: await desktop.locator(".panel, .diagnostics-panel").evaluateAll(
        (nodes) => nodes.map((node) => getComputedStyle(node).opacity)
      ),
      desktopBodyWidth: await desktop.evaluate(() => document.body.scrollWidth),
      mobileBodyWidth: await mobile.evaluate(() => document.body.scrollWidth)
    };
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
