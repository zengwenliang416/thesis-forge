import { describe, expect, it } from "vitest";

describe("Windows Tauri WebdriverIO service compatibility", () => {
  it("loads and initializes the configured service classes", async () => {
    const serviceModule = await import("@wdio/tauri-service");
    const appBinaryPath = process.execPath;
    const options = {
      appBinaryPath,
      driverProvider: "external",
      autoInstallTauriDriver: false,
      autoDownloadEdgeDriver: true,
    };
    const capabilities = {
      browserName: "tauri",
      "tauri:options": {
        application: appBinaryPath,
      },
    };

    expect(
      Reflect.construct(serviceModule.default, [options, capabilities]),
    ).toBeInstanceOf(serviceModule.default);
    expect(
      Reflect.construct(serviceModule.launcher, [
        options,
        capabilities,
        {},
      ]),
    ).toBeInstanceOf(serviceModule.launcher);
  });
});
