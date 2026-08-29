import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { access, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

test("package and Skill identities are distinct and lifecycle scripts are absent", async () => {
  const packageJson = JSON.parse(await readFile(path.join(ROOT, "package.json"), "utf8"));
  const manifest = JSON.parse(
    await readFile(path.join(ROOT, "docforge-project", "manifest.json"), "utf8"),
  );
  const skill = await readFile(path.join(ROOT, "docforge-project", "SKILL.md"), "utf8");

  assert.equal(packageJson.name, "docforge-project-skill");
  assert.equal(manifest.name, "docforge-project");
  assert.match(skill, /^name:\s*docforge-project$/m);
  for (const lifecycle of ["preinstall", "install", "postinstall", "prepare"]) {
    assert.equal(packageJson.scripts[lifecycle], undefined);
  }
  assert.deepEqual(packageJson.bin, {
    "docforge-project-skill": "bin/docforge-project-skill.mjs",
  });
  assert.equal(packageJson.main, undefined);
  assert.ok(packageJson.files.includes("docforge-project/LICENSE"));
  for (const entry of packageJson.files) {
    await access(path.join(ROOT, entry));
  }
});

test("governance metadata declares owner, cadence, output, and rollback", async () => {
  const manifest = JSON.parse(
    await readFile(path.join(ROOT, "docforge-project", "manifest.json"), "utf8"),
  );
  assert.equal(manifest.maturity_tier, "governed");
  assert.ok(manifest.owner);
  assert.ok(manifest.review_cadence);
  assert.ok(manifest.output_contract);
  assert.ok(manifest.rollback_boundary);
});

test("Yao-visible bridge delegates to the canonical Node CLI", async () => {
  const bridge = await readFile(
    path.join(ROOT, "docforge-project", "scripts", "docforge_project.py"),
    "utf8",
  );
  assert.match(bridge, /docforge-project\.mjs/);
  assert.match(bridge, /subprocess\.run/);
  assert.doesNotMatch(bridge, /shell\s*=\s*True/);
});

test("root and subcommand help are successful read-only operations", () => {
  const cli = path.join(ROOT, "bin", "docforge-project-skill.mjs");
  for (const args of [["--help"], ["import", "--help"], ["install", "--help"]]) {
    const result = spawnSync(process.execPath, [cli, ...args], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /Usage:/);
  }
});
