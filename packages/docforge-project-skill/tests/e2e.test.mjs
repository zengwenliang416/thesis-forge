import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  access,
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  createImportPlan,
  publishImport,
} from "../docforge-project/scripts/lib/importer.mjs";

const PACKAGE_ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const REPOSITORY_ROOT = path.resolve(PACKAGE_ROOT, "../..");
const DEFAULT_DOCFORGE = path.join(REPOSITORY_ROOT, ".venv", "bin", "docforge");

async function executableOrNull(candidate) {
  try {
    await access(candidate);
    return candidate;
  } catch {
    return null;
  }
}

test("ordinary Markdown without Front Matter passes real inspect and validate", async (t) => {
  const docforge = process.env.DOCFORGE_BIN ?? (await executableOrNull(DEFAULT_DOCFORGE));
  if (!docforge) {
    t.skip("real DocForge executable is unavailable");
    return;
  }

  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-project-minimal-e2e-"));
  const source = path.join(root, "input.md");
  const destination = path.join(root, "project");
  await writeFile(source, "# Packed project\n\nOrdinary Markdown input.\n", "utf8");

  const plan = await createImportPlan({ source, destination });
  const result = await publishImport(plan, { docforgeBin: docforge });

  assert.deepEqual(result.verification, {
    inspect: "passed",
    validate: "passed",
    build: "not-requested",
  });
});

test("long Markdown can exceed the default child-process buffer and still verify", async (t) => {
  const docforge = process.env.DOCFORGE_BIN ?? (await executableOrNull(DEFAULT_DOCFORGE));
  if (!docforge) {
    t.skip("real DocForge executable is unavailable");
    return;
  }

  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-project-long-e2e-"));
  const source = path.join(root, "input.md");
  const destination = path.join(root, "project");
  const paragraphs = Array.from(
    { length: 2500 },
    (_, index) => `Paragraph ${index + 1} contains enough ordinary text for inspection.`,
  );
  await writeFile(source, `# Long document\n\n${paragraphs.join("\n\n")}\n`, "utf8");

  const plan = await createImportPlan({ source, destination });
  const result = await publishImport(plan, { docforgeBin: docforge });

  assert.deepEqual(result.verification, {
    inspect: "passed",
    validate: "passed",
    build: "not-requested",
  });
});

test("comprehensive file-backed fixture passes real inspect, validate, and build", async (t) => {
  const docforge = process.env.DOCFORGE_BIN ?? (await executableOrNull(DEFAULT_DOCFORGE));
  if (!docforge) {
    t.skip("real DocForge executable is unavailable");
    return;
  }

  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-project-e2e-"));
  const source = path.join(root, "input.md");
  const destination = path.join(root, "project");
  await copyFile(path.join(PACKAGE_ROOT, "tests", "fixtures", "comprehensive.md"), source);
  await mkdir(path.join(root, "images"));
  await copyFile(
    path.join(REPOSITORY_ROOT, "tests", "fixtures", "v2-project", "assets", "model.png"),
    path.join(root, "images", "model.png"),
  );
  await copyFile(
    path.join(REPOSITORY_ROOT, "tests", "fixtures", "v2-project", "references.bib"),
    path.join(root, "references.bib"),
  );

  const plan = await createImportPlan({
    source,
    destination,
    bibliography: "references.bib",
  });
  const result = await publishImport(plan, {
    docforgeBin: docforge,
    build: true,
  });

  assert.deepEqual(result.verification, {
    inspect: "passed",
    validate: "passed",
    build: "passed",
  });
  const document = await readFile(path.join(destination, "document.md"), "utf8");
  assert.match(document, /^# 全格式验证/m);
  assert.match(document, /\*\*粗体\*\*/);
  assert.match(document, /`inline_code`/);
  assert.match(document, /\[本地语义链接\]\(#chap:overview\)/);
  assert.match(document, /^- 无序列表/m);
  assert.match(document, /^> 这是引用块。/m);
  assert.match(document, /^\| 指标 \| 数值 \|/m);
  assert.match(document, /\$x\+y\$/);
  assert.match(document, /^```python/m);
  assert.match(document, /\[\^note\]/);
  assert.match(document, /\[@smith2025\]/);
  assert.match(document, /\{#fig:model-[a-f0-9]{8}\}/);
  assert.ok(await readFile(path.join(destination, "source", "original.md")));
  assert.ok(await readFile(path.join(destination, "build", "document.docx")));

  for (const entry of [destination, path.join(destination, "docforge.yaml")]) {
    const inspect = spawnSync(docforge, ["inspect", entry], { encoding: "utf8" });
    const validate = spawnSync(docforge, ["validate", entry, "--json"], {
      encoding: "utf8",
    });
    assert.equal(inspect.status, 0, inspect.stderr);
    assert.equal(validate.status, 0, validate.stdout || validate.stderr);
  }
});
