import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  installSkill,
  rollbackSkill,
} from "../docforge-project/scripts/lib/installer.mjs";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const SKILL_ROOT = path.join(ROOT, "docforge-project");

test("fresh explicit installation writes a validated managed Skill", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-install-"));
  const destination = path.join(root, "skills", "docforge-project");
  const result = await installSkill(SKILL_ROOT, { destination });
  const marker = JSON.parse(
    await readFile(path.join(destination, ".docforge-project-install.json"), "utf8"),
  );

  assert.equal(result.status, "installed");
  assert.equal(marker.skill, "docforge-project");
  assert.match(result.reload, /Restart Codex|reload its Skill registry/);
  assert.match(await readFile(path.join(destination, "SKILL.md"), "utf8"), /name: docforge-project/);
});

test("unmanaged target is never overwritten", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-install-"));
  const destination = path.join(root, "docforge-project");
  await mkdir(destination);
  await writeFile(path.join(destination, "user.txt"), "keep");

  await assert.rejects(
    installSkill(SKILL_ROOT, { destination, update: true }),
    (error) => error.diagnostics.some((item) => item.code === "DFP-INSTALL-UNMANAGED"),
  );
  assert.equal(await readFile(path.join(destination, "user.txt"), "utf8"), "keep");
});

test("managed update creates a backup that can be rolled back", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "docforge-install-"));
  const destination = path.join(root, "docforge-project");
  await installSkill(SKILL_ROOT, { destination });
  await writeFile(path.join(destination, "local-proof.txt"), "old");

  const update = await installSkill(SKILL_ROOT, { destination, update: true });
  assert.ok(update.backup);
  assert.equal(await readFile(path.join(update.backup, "local-proof.txt"), "utf8"), "old");

  const rollback = await rollbackSkill({ destination, backup: update.backup });
  assert.equal(rollback.status, "rolled-back");
  assert.equal(await readFile(path.join(destination, "local-proof.txt"), "utf8"), "old");
});
