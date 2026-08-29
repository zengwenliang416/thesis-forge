import assert from "node:assert/strict";
import {
  access,
  chmod,
  mkdtemp,
  mkdir,
  readFile,
  readdir,
  symlink,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  createImportPlan,
  publishImport,
  serializePublicPlan,
} from "../docforge-project/scripts/lib/importer.mjs";
import { planAssetDestination } from "../docforge-project/scripts/lib/markdown.mjs";
import { lexicalPathDiagnostic } from "../docforge-project/scripts/lib/path-safety.mjs";

async function fixture(markdown, files = {}) {
  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-project-test-"));
  const source = path.join(root, "input.md");
  await writeFile(source, markdown, "utf8");
  for (const [name, value] of Object.entries(files)) {
    const target = path.join(root, name);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, value);
  }
  return { root, source, destination: path.join(root, "result") };
}

test("compatible Markdown remains byte-identical and uses neutral defaults", async () => {
  const sourceText = "# Notes\n\nA **bold** paragraph with `code`.\n";
  const input = await fixture(sourceText);
  const plan = await createImportPlan(input);

  assert.equal(plan.changed, false);
  assert.equal(plan.documentText, sourceText);
  assert.match(plan.manifest, /schema: docforge\.project\.v1/);
  assert.match(plan.manifest, /language: "und"/);
  assert.match(plan.manifest, /type: general/);
  assert.match(plan.manifest, /template_id: "docforge-standard"/);
  assert.match(plan.manifest, /en: "Notes"/);
  assert.doesNotMatch(plan.manifest, /academic:/);
  assert.doesNotMatch(plan.manifest, /output:/);
  assert.doesNotMatch(plan.manifest, /review:/);
});

test("the first H1 supplies exact neutral cover metadata without changing Markdown", async () => {
  const input = await fixture("# 项目记录 {#chap:notes}\n\n正文。\n");
  const plan = await createImportPlan(input);

  assert.equal(plan.changed, false);
  assert.match(plan.manifest, /zh: "项目记录"/);
  assert.equal(
    plan.diagnostics.some((item) => item.code === "DFP-METADATA-TITLE-FROM-H1"),
    true,
  );
});

test("thematic breaks are rewritten into visible DocForge paragraphs with provenance", async () => {
  const input = await fixture("# Notes\n\n---\n\n* * *\n\n___\n");
  const plan = await createImportPlan(input);

  assert.equal(plan.changed, true);
  assert.equal(plan.documentText, "# Notes\n\n———\n\n———\n\n———\n");
  assert.deepEqual(
    plan.rewrites,
    [
      { kind: "thematic-break", line: 3, from: "---", to: "———" },
      { kind: "thematic-break", line: 5, from: "* * *", to: "———" },
      { kind: "thematic-break", line: 7, from: "___", to: "———" },
    ],
  );
});

test("front matter and local image rewrites retain deterministic provenance", async () => {
  const input = await fixture(
    "---\nlanguage: zh-CN\ntitle: 文档\nunknown: keep-visible\n---\n# 标题\n\n![示意图](images/a.png)\n",
    { "images/a.png": Buffer.from("image-bytes") },
  );
  const first = await createImportPlan(input);
  const second = await createImportPlan(input);
  const publicFirst = serializePublicPlan(first);

  assert.equal(first.changed, true);
  assert.equal(first.documentText, second.documentText);
  assert.match(first.documentText, /!\[示意图\]\(assets\/images\/a\.png\)\{#fig:a-[a-f0-9]{8}\}/);
  assert.match(first.manifest, /zh: "文档"/);
  assert.equal(first.resources[0].destination, "assets/images/a.png");
  assert.equal(publicFirst.diagnostics[0].code, "DFP-METADATA-UNMAPPED");
  assert.equal(Object.isFrozen(first), true);
  assert.equal(Object.isFrozen(first.resources), true);
});

test("citations require an explicit bibliography", async () => {
  const input = await fixture("# Notes\n\nEvidence [@smith2025].\n");
  await assert.rejects(
    createImportPlan(input),
    (error) => error.diagnostics.some((item) => item.code === "DFP-BIBLIOGRAPHY-REQUIRED"),
  );
});

test("remote, traversal, inline image, and MDX inputs are blocked", async () => {
  const cases = [
    ["![remote](https://example.com/a.png)\n", "DFP-RESOURCE-REMOTE"],
    ["![escape](../a.png)\n", "DFP-RESOURCE-TRAVERSAL"],
    ["text ![inline](a.png)\n", "DFP-MARKDOWN-INLINE-IMAGE"],
    ['import Widget from "./widget.js";\n', "DFP-MARKDOWN-MDX"],
  ];
  for (const [markdown, code] of cases) {
    const input = await fixture(markdown, { "a.png": "a" });
    await assert.rejects(
      createImportPlan(input),
      (error) => error.diagnostics.some((item) => item.code === code),
    );
  }
});

test("symlink escape is blocked even when the target exists", async () => {
  const outside = await mkdtemp(path.join(os.tmpdir(), "docforge-outside-"));
  await writeFile(path.join(outside, "secret.png"), "secret");
  const input = await fixture("![secret](assets/secret.png)\n");
  await mkdir(path.join(input.root, "assets"));
  await symlink(path.join(outside, "secret.png"), path.join(input.root, "assets", "secret.png"));

  await assert.rejects(
    createImportPlan(input),
    (error) => error.diagnostics.some((item) => item.code === "DFP-RESOURCE-SYMLINK-ESCAPE"),
  );
});

test("invalid encoding, missing input, and existing destinations fail before writes", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-input-safety-"));
  const invalid = path.join(root, "invalid.md");
  const missing = path.join(root, "missing.md");
  const existing = path.join(root, "existing");
  await writeFile(invalid, Buffer.from([0xff, 0xfe, 0xfd]));
  await mkdir(existing);
  await writeFile(path.join(existing, "keep.txt"), "keep", "utf8");

  await assert.rejects(
    createImportPlan({ source: invalid, destination: path.join(root, "invalid-project") }),
    (error) => error.diagnostics.some((item) => item.code === "DFP-INPUT-ENCODING"),
  );
  await assert.rejects(
    createImportPlan({ source: missing, destination: path.join(root, "missing-project") }),
    (error) => error.diagnostics.some((item) => item.code === "DFP-INPUT-MISSING"),
  );
  await assert.rejects(
    createImportPlan({ source: invalid, destination: existing }),
    (error) => error.diagnostics.some((item) => item.code === "DFP-DESTINATION-EXISTS"),
  );

  await assert.rejects(access(path.join(root, "invalid-project")));
  await assert.rejects(access(path.join(root, "missing-project")));
  assert.equal(await readFile(path.join(existing, "keep.txt"), "utf8"), "keep");
});

test("portable path checks reject POSIX, Windows, device, and remote resource forms", () => {
  const cases = [
    ["/tmp/image.png", "DFP-RESOURCE-ABSOLUTE"],
    ["C:\\images\\image.png", "DFP-RESOURCE-ABSOLUTE"],
    ["NUL", "DFP-RESOURCE-DEVICE"],
    ["data:image/png;base64,AA==", "DFP-RESOURCE-REMOTE"],
  ];
  for (const [raw, code] of cases) {
    assert.equal(lexicalPathDiagnostic(raw, raw)?.code, code);
  }
});

test("case-folding asset collisions receive deterministic content-hash suffixes", () => {
  const destinations = new Map();
  assert.equal(
    planAssetDestination("images/A.png", "a".repeat(64), destinations),
    "assets/images/A.png",
  );
  assert.equal(
    planAssetDestination("images/a.png", "b".repeat(64), destinations),
    "assets/images/a-bbbbbbbb.png",
  );
  assert.equal(
    planAssetDestination("images/a.png", "b".repeat(64), destinations),
    "assets/images/a-bbbbbbbb.png",
  );
});

test("failed DocForge inspection removes owned staging and leaves destination absent", async () => {
  const input = await fixture("# Notes\n\nSafe content.\n");
  const plan = await createImportPlan(input);
  const fake = path.join(input.root, process.platform === "win32" ? "docforge.cmd" : "docforge");
  if (process.platform === "win32") {
    await writeFile(fake, "@exit /b 1\r\n", "utf8");
  } else {
    await writeFile(fake, "#!/bin/sh\nexit 1\n", "utf8");
    await chmod(fake, 0o755);
  }

  await assert.rejects(
    publishImport(plan, { docforgeBin: fake }),
    (error) => error.diagnostics.some((item) => item.code === "DFP-DOCFORGE-INSPECT"),
  );
  await assert.rejects(access(input.destination));
  const residue = (await readdir(input.root)).filter((name) =>
    name.startsWith(".result.docforge-stage-"),
  );
  assert.deepEqual(residue, []);
});
