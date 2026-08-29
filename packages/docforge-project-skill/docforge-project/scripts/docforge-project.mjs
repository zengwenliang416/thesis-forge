#!/usr/bin/env node

import path from "node:path";
import { fileURLToPath } from "node:url";

import { DiagnosticError } from "./lib/diagnostics.mjs";
import {
  createImportPlan,
  publishImport,
  resolveDocForge,
  serializePublicPlan,
} from "./lib/importer.mjs";
import {
  installSkill,
  rollbackSkill,
} from "./lib/installer.mjs";

const SKILL_ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

function usage() {
  return `docforge-project-skill

Usage:
  docforge-project-skill plan <source.md> <destination> [options]
  docforge-project-skill import <source.md> <destination> [options]
  docforge-project-skill install --target codex [--update]
  docforge-project-skill rollback --destination <path> --backup <path>

Import options:
  --source-root <path>       Confine all input reads to this directory
  --bibtex <path>            Local BibTeX path relative to the source boundary
  --docforge-bin <path>      DocForge executable (default: docforge on PATH)
  --project-id <id>          Explicit project ID
  --language <tag>           Project language (default: und)
  --title-zh <text>          Explicit Chinese title
  --title-en <text>          Explicit English title
  --author <name>            Repeatable author name
  --organization <text>      Explicit organization
  --date <YYYY-MM-DD>        Explicit document date
  --version <text>           Explicit document version
  --keyword <text>           Repeatable keyword
  --template-id <id>         Template ID (default: docforge-standard)
  --build                    Verify with docforge build after publication
  --json                     Emit JSON only
`;
}

function parseArgs(args) {
  const positional = [];
  const values = { authors: [], keywords: [] };
  const aliases = new Map([
    ["--source-root", "sourceRoot"],
    ["--bibtex", "bibliography"],
    ["--docforge-bin", "docforgeBin"],
    ["--project-id", "projectId"],
    ["--language", "language"],
    ["--title-zh", "titleZh"],
    ["--title-en", "titleEn"],
    ["--organization", "organization"],
    ["--date", "date"],
    ["--version", "version"],
    ["--template-id", "templateId"],
    ["--destination", "installDestination"],
    ["--backup", "backup"],
    ["--target", "target"],
  ]);
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (!arg.startsWith("--")) {
      positional.push(arg);
      continue;
    }
    if (arg === "--json" || arg === "--build" || arg === "--update" || arg === "--help") {
      values[arg.slice(2)] = true;
      continue;
    }
    if (arg === "--author" || arg === "--keyword") {
      const value = args[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`${arg} requires a value`);
      }
      values[arg === "--author" ? "authors" : "keywords"].push(value);
      index += 1;
      continue;
    }
    const key = aliases.get(arg);
    const value = args[index + 1];
    if (!key || !value || value.startsWith("--")) {
      throw new Error(`Unknown or incomplete option: ${arg}`);
    }
    values[key] = value;
    index += 1;
  }
  return { positional, values };
}

function printResult(result, jsonOnly) {
  if (jsonOnly) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

async function runImport(command, positional, values) {
  if (positional.length !== 2) {
    throw new Error(`${command} requires <source.md> and <destination>`);
  }
  await resolveDocForge(values.docforgeBin);
  const plan = await createImportPlan({
    ...values,
    source: positional[0],
    destination: positional[1],
  });
  if (command === "plan") {
    return serializePublicPlan(plan);
  }
  return publishImport(plan, {
    docforgeBin: values.docforgeBin,
    build: values.build,
  });
}

export async function main(args) {
  try {
    const [command, ...rest] = args;
    if (!command || command === "--help" || command === "help") {
      process.stdout.write(usage());
      return;
    }
    const { positional, values } = parseArgs(rest);
    if (values.help) {
      process.stdout.write(usage());
      return;
    }
    let result;
    if (command === "plan" || command === "import") {
      result = await runImport(command, positional, values);
    } else if (command === "install") {
      if (positional.length > 0) {
        throw new Error("install accepts options only");
      }
      result = await installSkill(SKILL_ROOT, {
        target: values.target,
        destination: values.installDestination,
        update: values.update,
      });
    } else if (command === "rollback") {
      if (!values.installDestination || !values.backup) {
        throw new Error("rollback requires --destination and --backup");
      }
      result = await rollbackSkill({
        destination: values.installDestination,
        backup: values.backup,
      });
    } else {
      throw new Error(`Unknown command: ${command}`);
    }
    printResult(result, values.json);
  } catch (error) {
    const payload = {
      ok: false,
      error: error.message,
      diagnostics:
        error instanceof DiagnosticError
          ? error.diagnostics
          : [
              {
                code: "DFP-CLI-USAGE",
                severity: "error",
                target: "command",
                message: error.message,
                action: "Run docforge-project-skill --help.",
              },
            ],
    };
    process.stderr.write(`${JSON.stringify(payload, null, 2)}\n`);
    process.exitCode = error instanceof DiagnosticError ? 1 : 2;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main(process.argv.slice(2));
}
