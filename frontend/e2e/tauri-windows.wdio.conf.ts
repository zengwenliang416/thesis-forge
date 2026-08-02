import path from "node:path";

const appBinaryPath = process.env.THESISFORGE_WINDOWS_APP;

if (!appBinaryPath) {
  throw new Error("THESISFORGE_WINDOWS_APP is required");
}

export const config = {
  runner: "local",
  specs: [path.resolve("e2e/tauri-windows.acceptance.ts")],
  maxInstances: 1,
  services: [
    [
      "@wdio/tauri-service",
      {
        appBinaryPath,
        driverProvider: "external",
        autoInstallTauriDriver: false,
        autoDownloadEdgeDriver: true,
        captureBackendLogs: true,
        captureFrontendLogs: true,
        startTimeout: 60_000,
      },
    ],
  ],
  capabilities: [
    {
      browserName: "tauri",
      "tauri:options": {
        application: appBinaryPath,
      },
    },
  ],
  outputDir: path.resolve("logs/wdio"),
  logLevel: "info",
  waitforTimeout: 20_000,
  connectionRetryTimeout: 120_000,
  connectionRetryCount: 2,
  framework: "mocha",
  reporters: ["spec"],
  mochaOpts: {
    ui: "bdd",
    timeout: 120_000,
  },
};
