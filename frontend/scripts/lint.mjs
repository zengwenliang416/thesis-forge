import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { extname, join, relative } from "node:path";

const root = fileURLToPath(new URL("../src/", import.meta.url));
const failures = [];

async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await walk(path);
      continue;
    }
    if (![".ts", ".tsx"].includes(extname(entry.name))) {
      continue;
    }
    const content = await readFile(path, "utf8");
    const name = relative(join(root, ".."), path);
    if (/[ \t]+$/m.test(content)) {
      failures.push(`${name}: trailing whitespace`);
    }
    if (/\bany\b/.test(content)) {
      failures.push(`${name}: explicit any is forbidden`);
    }
    if (
      name.includes("/components/") &&
      /(fetch\s*\(|@tauri-apps\/api|thesis_forge)/.test(content)
    ) {
      failures.push(`${name}: components must use WorkbenchTransport`);
    }
  }
}

await walk(root);
if (failures.length) {
  console.error(failures.join("\n"));
  process.exitCode = 1;
}
