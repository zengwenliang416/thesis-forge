import path from "node:path";
import os from "node:os";
import {
  access,
  cp,
  mkdir,
  readFile,
  rename,
  rm,
  writeFile,
} from "node:fs/promises";
import { randomBytes } from "node:crypto";

import { DiagnosticError, diagnostic } from "./diagnostics.mjs";

const MARKER = ".docforge-project-install.json";
const RUNTIME_ENTRIES = [
  "SKILL.md",
  "LICENSE",
  "agents",
  "manifest.json",
  "evals",
  "references",
  "security",
  "scripts",
  "tests",
  "reports/skill-ir.json",
  "reports/security_trust_report.json",
  "reports/security_trust_report.md",
  "reports/trust-supplement.md",
  "reports/output_quality_scorecard.json",
  "reports/output_quality_scorecard.md",
];

async function exists(candidate) {
  try {
    await access(candidate);
    return true;
  } catch {
    return false;
  }
}

async function readJson(candidate) {
  return JSON.parse(await readFile(candidate, "utf8"));
}

export function resolveInstallDestination(options = {}) {
  if (options.destination) {
    return path.resolve(options.destination);
  }
  if (options.target !== "codex") {
    throw new DiagnosticError("Unsupported install target", [
      diagnostic(
        "DFP-INSTALL-TARGET",
        "error",
        String(options.target ?? ""),
        "Only the codex target is currently supported.",
        "Use install --target codex or pass --destination explicitly.",
      ),
    ]);
  }
  const codexHome = process.env.CODEX_HOME
    ? path.resolve(process.env.CODEX_HOME)
    : path.join(os.homedir(), ".codex");
  return path.join(codexHome, "skills", "docforge-project");
}

async function validateSkillRoot(skillRoot) {
  const manifest = await readJson(path.join(skillRoot, "manifest.json"));
  const skill = await readFile(path.join(skillRoot, "SKILL.md"), "utf8");
  if (manifest.name !== "docforge-project" || !/^name:\s*docforge-project\s*$/m.test(skill)) {
    throw new DiagnosticError("Packaged Skill identity is invalid", [
      diagnostic(
        "DFP-INSTALL-PACKAGE-INVALID",
        "error",
        "docforge-project",
        "Packaged Skill identity does not match docforge-project.",
        "Reinstall from a verified package.",
      ),
    ]);
  }
  return manifest;
}

async function copyRuntimeSkill(skillRoot, stage) {
  await mkdir(stage, { recursive: false });
  for (const entry of RUNTIME_ENTRIES) {
    const target = path.join(stage, entry);
    await mkdir(path.dirname(target), { recursive: true });
    await cp(path.join(skillRoot, entry), target, {
      recursive: true,
      errorOnExist: true,
      force: false,
    });
  }
}

export async function installSkill(skillRoot, options = {}) {
  const manifest = await validateSkillRoot(skillRoot);
  const destination = resolveInstallDestination(options);
  const parent = path.dirname(destination);
  await mkdir(parent, { recursive: true });

  const destinationExists = await exists(destination);
  let previousMarker = null;
  if (destinationExists) {
    try {
      previousMarker = await readJson(path.join(destination, MARKER));
    } catch {
      throw new DiagnosticError("Existing Skill is unmanaged", [
        diagnostic(
          "DFP-INSTALL-UNMANAGED",
          "error",
          path.basename(destination),
          "Existing destination is not a managed docforge-project installation.",
          "Choose another destination or move the unmanaged directory manually.",
        ),
      ]);
    }
    if (!options.update) {
      throw new DiagnosticError("Explicit update is required", [
        diagnostic(
          "DFP-INSTALL-UPDATE-REQUIRED",
          "error",
          path.basename(destination),
          "A managed installation already exists.",
          "Run the same install command with --update.",
        ),
      ]);
    }
  }

  const token = randomBytes(6).toString("hex");
  const stage = path.join(parent, `.docforge-project.install-${token}`);
  const backup = destinationExists
    ? path.join(parent, `.docforge-project.backup-${previousMarker.version}-${token}`)
    : null;
  try {
    await copyRuntimeSkill(skillRoot, stage);
    await writeFile(
      path.join(stage, MARKER),
      `${JSON.stringify(
        {
          schema: "docforge.skill-install.v1",
          package: "docforge-project-skill",
          skill: "docforge-project",
          version: manifest.version,
        },
        null,
        2,
      )}\n`,
      "utf8",
    );
    await validateSkillRoot(stage);
    if (destinationExists) {
      await rename(destination, backup);
    }
    try {
      await rename(stage, destination);
    } catch (error) {
      if (backup && (await exists(backup)) && !(await exists(destination))) {
        await rename(backup, destination);
      }
      throw error;
    }
  } catch (error) {
    await rm(stage, { recursive: true, force: true });
    throw error;
  }

  return {
    status: destinationExists ? "updated" : "installed",
    skill: "docforge-project",
    version: manifest.version,
    destination,
    backup,
    rollback: backup
      ? `docforge-project-skill rollback --destination ${JSON.stringify(destination)} --backup ${JSON.stringify(backup)}`
      : null,
    reload: "Restart Codex or reload its Skill registry before first use.",
  };
}

export async function rollbackSkill(options) {
  const destination = path.resolve(options.destination);
  const backup = path.resolve(options.backup);
  const backupMarker = await readJson(path.join(backup, MARKER));
  if (backupMarker.package !== "docforge-project-skill") {
    throw new DiagnosticError("Backup is unmanaged", [
      diagnostic(
        "DFP-INSTALL-BACKUP-INVALID",
        "error",
        path.basename(backup),
        "Backup is not a managed docforge-project installation.",
        "Use the exact backup path reported by the installer.",
      ),
    ]);
  }
  const displaced = `${destination}.replaced-${randomBytes(4).toString("hex")}`;
  if (await exists(destination)) {
    await rename(destination, displaced);
  }
  try {
    await rename(backup, destination);
    await rm(displaced, { recursive: true, force: true });
  } catch (error) {
    if (await exists(displaced)) {
      await rename(displaced, destination);
    }
    throw error;
  }
  return {
    status: "rolled-back",
    destination,
    version: backupMarker.version,
  };
}
