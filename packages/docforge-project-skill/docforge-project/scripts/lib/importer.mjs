import path from "node:path";
import { constants as fsConstants } from "node:fs";
import {
  access,
  copyFile,
  mkdir,
  readFile,
  realpath,
  rename,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import { createHash, randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";

import { DiagnosticError, diagnostic, throwIfBlocked } from "./diagnostics.mjs";
import { extractFrontMatter } from "./frontmatter.mjs";
import { serializeManifest } from "./manifest.mjs";
import { normalizeMarkdown } from "./markdown.mjs";
import { isInside, resolveConfinedFile } from "./path-safety.mjs";

const PROJECT_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
const LANGUAGE_RE = /^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/;
const DOCFORGE_MAX_BUFFER = 64 * 1024 * 1024;

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function stableProjectId(destination) {
  const base = path
    .basename(destination)
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^[^a-z0-9]+|[^a-z0-9]+$/g, "");
  return (base || `project-${sha256(path.basename(destination)).slice(0, 8)}`).slice(0, 64);
}

function uniqueStrings(values) {
  return [...new Set(values.map((value) => String(value).trim()).filter(Boolean))];
}

function localizedTitle(value, language) {
  const text = String(value).trim();
  if (String(language).toLowerCase().startsWith("zh") || /[\p{Script=Han}]/u.test(text)) {
    return { zh: text, en: null };
  }
  return { zh: null, en: text };
}

function firstLevelOneHeading(markdown) {
  let fence = null;
  for (const line of markdown.split(/\r?\n/)) {
    const fenceMatch = /^\s*(`{3,}|~{3,})/.exec(line);
    if (fenceMatch) {
      const marker = fenceMatch[1][0];
      fence = fence === null ? marker : fence === marker ? null : fence;
      continue;
    }
    if (fence) {
      continue;
    }
    const heading = /^#(?!#)\s+(.+?)\s*#*\s*$/.exec(line);
    if (heading) {
      return heading[1].replace(/\s+\{#[A-Za-z0-9_.:-]+\}\s*$/, "").trim() || null;
    }
  }
  return null;
}

function metadataFrom(frontMatter, options, diagnostics, sourceName) {
  const raw = frontMatter.values;
  const language = options.language ?? raw.language ?? raw.lang ?? "und";
  const explicitLanguage = language !== "und";
  let title = {
    zh: options.titleZh ?? raw.title_zh ?? null,
    en: options.titleEn ?? raw.title_en ?? null,
  };
  if (raw.title && explicitLanguage) {
    if (String(language).toLowerCase().startsWith("zh")) {
      title.zh ??= raw.title;
    } else {
      title.en ??= raw.title;
    }
  } else if (raw.title) {
    title = localizedTitle(raw.title, language);
    diagnostics.push(
      diagnostic(
        "DFP-METADATA-TITLE-LOCALIZED",
        "warning",
        "front-matter.title",
        "The unlocalized Front Matter title was preserved in a deterministic localized title slot.",
        "Pass --language with --title-zh or --title-en to select the slot explicitly.",
      ),
    );
  }
  if (!title.zh && !title.en) {
    const heading = firstLevelOneHeading(frontMatter.body);
    const fallback = heading ?? path.basename(sourceName, path.extname(sourceName));
    title = localizedTitle(fallback, language);
    diagnostics.push(
      diagnostic(
        heading ? "DFP-METADATA-TITLE-FROM-H1" : "DFP-METADATA-TITLE-FROM-FILENAME",
        "warning",
        heading ? "heading:1" : path.basename(sourceName),
        heading
          ? "The first level-one heading was preserved as required cover metadata."
          : "The Markdown filename was preserved as required cover metadata.",
        "Pass --title-zh or --title-en to set cover metadata explicitly.",
      ),
    );
  }

  const rawAuthors = options.authors.length > 0 ? options.authors : raw.authors ?? raw.author ?? [];
  const authors = Array.isArray(rawAuthors) ? rawAuthors : [rawAuthors];
  const rawKeywords = options.keywords.length > 0 ? options.keywords : raw.keywords ?? [];
  const keywords = Array.isArray(rawKeywords) ? rawKeywords : [rawKeywords];
  return {
    language,
    title: title.zh || title.en ? title : null,
    authors: uniqueStrings(authors),
    organization: options.organization ?? raw.organization ?? null,
    date: options.date ?? raw.date ?? null,
    version: options.version ?? raw.version ?? null,
    keywords: uniqueStrings(keywords),
    templateId: options.templateId ?? raw.template_id ?? "docforge-standard",
  };
}

async function exists(candidate) {
  try {
    await access(candidate);
    return true;
  } catch {
    return false;
  }
}

async function decodeUtf8(bytes) {
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new DiagnosticError("Input is not valid UTF-8", [
      diagnostic(
        "DFP-INPUT-ENCODING",
        "error",
        "source",
        "Markdown input is not valid UTF-8.",
        "Convert the file to UTF-8 and run the plan again.",
      ),
    ]);
  }
}

function redactCommandOutput(value, roots) {
  let output = String(value ?? "");
  for (const root of roots) {
    if (root) {
      output = output.replaceAll(root, "<path>");
    }
  }
  if (output.length <= 4000) {
    return output;
  }
  const omitted = output.length - 4000;
  return `${output.slice(0, 2000)}\n... <${omitted} characters omitted> ...\n${output.slice(-2000)}`;
}

function runDocForge(command, args, roots) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    env: {
      ...process.env,
      NO_PROXY: "*",
      no_proxy: "*",
    },
    timeout: 120_000,
    maxBuffer: DOCFORGE_MAX_BUFFER,
  });
  return {
    status: result.status,
    error: result.error,
    stdout: redactCommandOutput(result.stdout, roots),
    stderr: redactCommandOutput(result.stderr, roots),
  };
}

export async function resolveDocForge(command = "docforge") {
  if (command.includes("/") || command.includes("\\")) {
    const resolved = path.resolve(command);
    try {
      await access(resolved, fsConstants.X_OK);
      return resolved;
    } catch {
      throw new DiagnosticError("DocForge executable is unavailable", [
        diagnostic(
          "DFP-DOCFORGE-MISSING",
          "error",
          path.basename(command),
          "The selected DocForge executable is missing or not executable.",
          "Install DocForge or pass --docforge-bin with an executable path.",
        ),
      ]);
    }
  }
  const probe = spawnSync(command, ["--help"], { encoding: "utf8", timeout: 30_000 });
  if (probe.error?.code === "ENOENT") {
    throw new DiagnosticError("DocForge executable is unavailable", [
      diagnostic(
        "DFP-DOCFORGE-MISSING",
        "error",
        command,
        "The docforge executable was not found on PATH.",
        "Install DocForge or pass --docforge-bin with an executable path.",
      ),
    ]);
  }
  return command;
}

export async function createImportPlan(inputOptions) {
  const options = {
    source: inputOptions.source,
    destination: inputOptions.destination,
    sourceRoot: inputOptions.sourceRoot,
    bibliography: inputOptions.bibliography,
    projectId: inputOptions.projectId,
    language: inputOptions.language,
    titleZh: inputOptions.titleZh,
    titleEn: inputOptions.titleEn,
    authors: inputOptions.authors ?? [],
    organization: inputOptions.organization,
    date: inputOptions.date,
    version: inputOptions.version,
    keywords: inputOptions.keywords ?? [],
    templateId: inputOptions.templateId,
  };
  const diagnostics = [];
  const sourceInput = path.resolve(options.source);
  const destination = path.resolve(options.destination);

  if (![".md", ".markdown"].includes(path.extname(sourceInput).toLowerCase())) {
    diagnostics.push(
      diagnostic(
        "DFP-INPUT-EXTENSION",
        "error",
        path.basename(sourceInput),
        "Primary input must use .md or .markdown.",
        "Select one Markdown source file.",
      ),
    );
  }
  if (await exists(destination)) {
    diagnostics.push(
      diagnostic(
        "DFP-DESTINATION-EXISTS",
        "error",
        path.basename(destination),
        "Destination already exists and will not be merged or overwritten.",
        "Choose a new destination directory.",
      ),
    );
  }
  const destinationParent = path.dirname(destination);
  if (!(await exists(destinationParent)) || !(await stat(destinationParent)).isDirectory()) {
    diagnostics.push(
      diagnostic(
        "DFP-DESTINATION-PARENT",
        "error",
        path.basename(destinationParent),
        "Destination parent must already exist.",
        "Create or select a writable parent directory.",
      ),
    );
  }

  let source;
  let sourceRoot;
  let bytes;
  try {
    source = await realpath(sourceInput);
    if (!(await stat(source)).isFile()) {
      throw new Error("not-file");
    }
    sourceRoot = await realpath(options.sourceRoot ? path.resolve(options.sourceRoot) : path.dirname(source));
    if (!isInside(sourceRoot, source)) {
      diagnostics.push(
        diagnostic(
          "DFP-INPUT-BOUNDARY",
          "error",
          path.basename(source),
          "Markdown source resolves outside the selected source boundary.",
          "Select a source root that contains the Markdown without symlink escape.",
        ),
      );
    }
    bytes = await readFile(source);
  } catch {
    diagnostics.push(
      diagnostic(
        "DFP-INPUT-MISSING",
        "error",
        path.basename(sourceInput),
        "Markdown input is missing or is not a regular file.",
        "Select an existing UTF-8 Markdown file.",
      ),
    );
  }
  throwIfBlocked(diagnostics);

  const originalText = await decodeUtf8(bytes);
  const frontMatter = extractFrontMatter(originalText);
  diagnostics.push(...frontMatter.diagnostics);
  for (const key of frontMatter.unknownKeys) {
    diagnostics.push(
      diagnostic(
        "DFP-METADATA-UNMAPPED",
        "warning",
        `front-matter.${key}`,
        "Unknown Front Matter was not mapped into the strict manifest.",
        "Pass supported neutral metadata explicitly if it is required.",
      ),
    );
  }
  const metadata = metadataFrom(frontMatter, options, diagnostics, path.basename(source));
  if (!LANGUAGE_RE.test(metadata.language)) {
    diagnostics.push(
      diagnostic(
        "DFP-METADATA-LANGUAGE",
        "error",
        "project.language",
        "Language must be a valid BCP 47-style language tag.",
        "Use a value such as und, zh-CN, or en.",
      ),
    );
  }

  const normalized = await normalizeMarkdown(frontMatter.body, sourceRoot);
  diagnostics.push(...normalized.diagnostics);

  let bibliography = null;
  if (options.bibliography) {
    const resolved = await resolveConfinedFile(
      sourceRoot,
      options.bibliography,
      path.basename(options.bibliography),
    );
    if (resolved.diagnostic) {
      diagnostics.push(resolved.diagnostic);
    } else if (path.extname(resolved.path).toLowerCase() !== ".bib") {
      diagnostics.push(
        diagnostic(
          "DFP-BIBLIOGRAPHY-EXTENSION",
          "error",
          path.basename(resolved.path),
          "Bibliography input must be a .bib file.",
          "Select a local BibTeX file.",
        ),
      );
    } else {
      const bibliographyBytes = await readFile(resolved.path);
      bibliography = {
        source: resolved.path,
        sourceRelative: path.relative(sourceRoot, resolved.path).split(path.sep).join("/"),
        destination: "references.bib",
        sha256: sha256(bibliographyBytes),
      };
    }
  }
  if (normalized.hasCitation && !bibliography) {
    diagnostics.push(
      diagnostic(
        "DFP-BIBLIOGRAPHY-REQUIRED",
        "error",
        "citations",
        "Citation syntax requires an explicitly supplied local BibTeX file.",
        "Run again with --bibtex <local-file.bib>.",
      ),
    );
  }

  const projectId = options.projectId ?? stableProjectId(destination);
  if (!PROJECT_ID_RE.test(projectId)) {
    diagnostics.push(
      diagnostic(
        "DFP-PROJECT-ID",
        "error",
        "project.id",
        "Project ID contains unsupported characters.",
        "Use letters, digits, dots, underscores, and hyphens.",
      ),
    );
  }
  throwIfBlocked(diagnostics);

  const documentText = normalized.text;
  const changed = !Buffer.from(documentText, "utf8").equals(bytes);
  const manifest = serializeManifest({
    project: { id: projectId, language: metadata.language },
    metadata,
    bibliography,
    templateId: metadata.templateId,
  });
  return Object.freeze({
    schema: "docforge.import-plan.v1",
    source,
    sourceRoot,
    sourceName: path.basename(source),
    destination,
    projectId,
    documentText,
    originalBytes: bytes,
    originalSha256: sha256(bytes),
    documentSha256: sha256(Buffer.from(documentText, "utf8")),
    changed,
    manifest,
    resources: Object.freeze(normalized.resources),
    bibliography,
    rewrites: Object.freeze([
      ...(frontMatter.changed ? [{ kind: "front-matter", keys: Object.keys(frontMatter.values) }] : []),
      ...normalized.rewrites,
    ]),
    diagnostics: Object.freeze(diagnostics),
  });
}

function publicPlan(plan) {
  return {
    schema: plan.schema,
    source: plan.sourceName,
    destination: path.basename(plan.destination),
    projectId: plan.projectId,
    changed: plan.changed,
    originalSha256: plan.originalSha256,
    documentSha256: plan.documentSha256,
    rewrites: plan.rewrites,
    resources: plan.resources.map((resource) => ({
      source: resource.sourceRelative,
      destination: resource.destination,
      sha256: resource.sha256,
    })),
    bibliography: plan.bibliography
      ? {
          source: plan.bibliography.sourceRelative,
          destination: plan.bibliography.destination,
          sha256: plan.bibliography.sha256,
        }
      : null,
    diagnostics: plan.diagnostics,
  };
}

async function writeStage(plan, stage) {
  await mkdir(stage, { recursive: false });
  await Promise.all([
    mkdir(path.join(stage, "assets"), { recursive: true }),
    mkdir(path.join(stage, "build"), { recursive: true }),
    mkdir(path.join(stage, "review"), { recursive: true }),
  ]);
  await writeFile(path.join(stage, "docforge.yaml"), plan.manifest, "utf8");
  await writeFile(path.join(stage, "document.md"), plan.documentText, "utf8");
  for (const resource of plan.resources) {
    const target = path.join(stage, ...resource.destination.split("/"));
    await mkdir(path.dirname(target), { recursive: true });
    await copyFile(resource.source, target);
  }
  if (plan.bibliography) {
    await copyFile(plan.bibliography.source, path.join(stage, "references.bib"));
  }
  if (plan.changed) {
    await mkdir(path.join(stage, "source"), { recursive: true });
    await writeFile(path.join(stage, "source", "original.md"), plan.originalBytes);
  }
  await writeFile(
    path.join(stage, "import-report.json"),
    `${JSON.stringify({ ...publicPlan(plan), verification: { inspect: "pending", validate: "pending" } }, null, 2)}\n`,
    "utf8",
  );
}

function verificationFailure(code, target, result, action) {
  const detail = [result.stderr, result.stdout].filter(Boolean).join("\n").trim();
  return new DiagnosticError(`${target} failed`, [
    diagnostic(
      code,
      "error",
      target,
      detail || `${target} exited with status ${result.status ?? "unknown"}.`,
      action,
    ),
  ]);
}

export async function publishImport(plan, options = {}) {
  await resolveDocForge(options.docforgeBin);
  if (await exists(plan.destination)) {
    throw new DiagnosticError("Destination already exists", [
      diagnostic(
        "DFP-DESTINATION-EXISTS",
        "error",
        path.basename(plan.destination),
        "Destination appeared after planning and will not be overwritten.",
        "Choose a new destination and create a fresh plan.",
      ),
    ]);
  }

  const token = randomBytes(6).toString("hex");
  const stage = path.join(path.dirname(plan.destination), `.${path.basename(plan.destination)}.docforge-stage-${token}`);
  const roots = [plan.sourceRoot, stage, plan.destination];
  try {
    await writeStage(plan, stage);
    const inspect = runDocForge(options.docforgeBin ?? "docforge", ["inspect", stage], roots);
    if (inspect.error || inspect.status !== 0) {
      throw verificationFailure(
        "DFP-DOCFORGE-INSPECT",
        "docforge inspect",
        inspect,
        "Run docforge inspect on the source project and correct the reported syntax.",
      );
    }
    const validate = runDocForge(
      options.docforgeBin ?? "docforge",
      ["validate", stage, "--json"],
      roots,
    );
    if (validate.error || validate.status !== 0) {
      throw verificationFailure(
        "DFP-DOCFORGE-VALIDATE",
        "docforge validate",
        validate,
        "Correct the reported project or document diagnostics and import again.",
      );
    }
    await writeFile(
      path.join(stage, "import-report.json"),
      `${JSON.stringify(
        {
          ...publicPlan(plan),
          verification: {
            inspect: "passed",
            validate: "passed",
            build: options.build ? "pending" : "not-requested",
          },
        },
        null,
        2,
      )}\n`,
      "utf8",
    );
    await rename(stage, plan.destination);
  } catch (error) {
    await rm(stage, { recursive: true, force: true });
    throw error;
  }

  let build = "not-requested";
  if (options.build) {
    const result = runDocForge(
      options.docforgeBin ?? "docforge",
      ["build", plan.destination],
      [plan.sourceRoot, plan.destination],
    );
    if (result.error || result.status !== 0) {
      throw verificationFailure(
        "DFP-DOCFORGE-BUILD",
        "docforge build",
        result,
        "Open the published project, correct build diagnostics, and run docforge build again.",
      );
    }
    build = "passed";
    const reportPath = path.join(plan.destination, "import-report.json");
    const report = JSON.parse(await readFile(reportPath, "utf8"));
    report.verification.build = build;
    await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  }

  return {
    ...publicPlan(plan),
    destination: plan.destination,
    verification: {
      inspect: "passed",
      validate: "passed",
      build,
    },
  };
}

export function serializePublicPlan(plan) {
  return publicPlan(plan);
}
