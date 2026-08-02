import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL("..", import.meta.url));
const repositoryRoot = fileURLToPath(new URL("../..", import.meta.url));
const virtualEnvironmentPython =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
const virtualEnvironmentPythonPath = resolve(
  repositoryRoot,
  virtualEnvironmentPython,
);
const python =
  process.env.THESISFORGE_PYTHON ??
  (existsSync(virtualEnvironmentPythonPath)
    ? virtualEnvironmentPythonPath
    : process.platform === "win32"
      ? "python"
      : "python3");
const serverScript = resolve(frontendRoot, "e2e/real_http_server.py");

export default defineConfig({
  testDir: ".",
  testMatch: "real-http.acceptance.ts",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:4187",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "real-http-chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
  webServer: {
    command: `pnpm build && "${python}" "${serverScript}" --port 4187`,
    cwd: frontendRoot,
    url: "http://127.0.0.1:4187",
    reuseExistingServer: false,
    timeout: 120000,
  },
});
