import path from "node:path";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

import { diagnostic } from "./diagnostics.mjs";
import { resolveConfinedFile, toPosix } from "./path-safety.mjs";

const IMAGE_RE =
  /^(?<indent>\s*)!\[(?<caption>[^\]]*)\]\((?<destination><[^>]+>|[^\s)]+)(?:\s+(?:"[^"]*"|'[^']*'))?\)(?<attribute>\{#fig:[A-Za-z0-9_.:-]+\})?\s*$/;
const ANY_IMAGE_RE = /!\[[^\]]*\]\([^)]+\)/;
const FIGURE_ID_RE = /\{#(?<id>fig:[A-Za-z0-9_.:-]+)\}/g;
const CITATION_RE = /\[@[A-Za-z0-9_:.+-]+(?:[^\]]*)\]/;
const BLOCKED_HTML_RE = /^\s*<\/?(?:script|style|iframe|object|embed|form|input|button|video|audio|canvas|svg|math|details|summary|table|div|section|article|aside|header|footer|nav|main)\b/i;
const MDX_RE = /^\s*(?:import|export)\s+.+\s+from\s+["'][^"']+["'];?\s*$|^\s*<[A-Z][A-Za-z0-9.]*(?:\s|>|\/>)/;
const THEMATIC_BREAK_RE =
  /^(?<indent> {0,3})(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$/;

function hash(value) {
  return createHash("sha256").update(value).digest("hex");
}

function slug(value) {
  const normalized = value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || "image";
}

function withoutAngleBrackets(value) {
  return value.startsWith("<") && value.endsWith(">") ? value.slice(1, -1) : value;
}

export function planAssetDestination(relative, contentHash, usedDestinations) {
  const portableRelative = relative.replaceAll("\\", "/");
  const parsed = path.posix.parse(portableRelative);
  let candidate = path.posix.join("assets", portableRelative);
  const collisionKey = candidate.toLowerCase();
  const existing = usedDestinations.get(collisionKey);
  if (existing && existing !== contentHash) {
    candidate = path.posix.join(
      "assets",
      parsed.dir,
      `${parsed.name}-${contentHash.slice(0, 8)}${parsed.ext}`,
    );
  }
  usedDestinations.set(candidate.toLowerCase(), contentHash);
  return candidate;
}

function assetDestination(sourceRoot, resolved, contentHash, usedDestinations) {
  return planAssetDestination(
    toPosix(path.relative(sourceRoot, resolved)),
    contentHash,
    usedDestinations,
  );
}

export async function normalizeMarkdown(text, sourceRoot) {
  const lines = text.split(/\r?\n/);
  const output = [];
  const diagnostics = [];
  const rewrites = [];
  const resources = [];
  const usedIds = new Set();
  const usedDestinations = new Map();
  let fence = null;
  let hasCitation = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const fenceMatch = /^\s*(`{3,}|~{3,})/.exec(line);
    if (fenceMatch) {
      const marker = fenceMatch[1];
      if (!fence) {
        fence = marker[0];
      } else if (marker[0] === fence) {
        fence = null;
      }
      output.push(line);
      continue;
    }
    if (fence) {
      output.push(line);
      continue;
    }

    const thematicBreak = THEMATIC_BREAK_RE.exec(line);
    if (thematicBreak) {
      const rewritten = `${thematicBreak.groups.indent}———`;
      output.push(rewritten);
      rewrites.push({
        kind: "thematic-break",
        line: index + 1,
        from: line.trim(),
        to: "———",
      });
      continue;
    }

    if (MDX_RE.test(line)) {
      diagnostics.push(
        diagnostic(
          "DFP-MARKDOWN-MDX",
          "error",
          `line:${index + 1}`,
          "Executable MDX or component syntax is outside the import contract.",
          "Replace it with static Markdown supported by DocForge.",
          index + 1,
        ),
      );
    } else if (BLOCKED_HTML_RE.test(line)) {
      diagnostics.push(
        diagnostic(
          "DFP-MARKDOWN-HTML",
          "error",
          `line:${index + 1}`,
          "Raw HTML blocks are not interpreted or executed.",
          "Replace the block with supported Markdown.",
          index + 1,
        ),
      );
    }

    hasCitation ||= CITATION_RE.test(line);
    for (const match of line.matchAll(FIGURE_ID_RE)) {
      if (usedIds.has(match.groups.id)) {
        diagnostics.push(
          diagnostic(
            "DFP-MARKDOWN-DUPLICATE-FIGURE-ID",
            "error",
            match.groups.id,
            "Figure IDs must be unique.",
            "Assign a unique fig: ID before importing.",
            index + 1,
          ),
        );
      }
      usedIds.add(match.groups.id);
    }

    const image = IMAGE_RE.exec(line);
    if (!image) {
      if (ANY_IMAGE_RE.test(line)) {
        diagnostics.push(
          diagnostic(
            "DFP-MARKDOWN-INLINE-IMAGE",
            "error",
            `line:${index + 1}`,
            "DocForge figures must be standalone Markdown image paragraphs.",
            "Move the image onto its own line.",
            index + 1,
          ),
        );
      }
      output.push(line);
      continue;
    }

    const rawDestination = withoutAngleBrackets(image.groups.destination);
    const resolved = await resolveConfinedFile(
      sourceRoot,
      rawDestination,
      rawDestination,
      index + 1,
    );
    if (resolved.diagnostic) {
      diagnostics.push(resolved.diagnostic);
      output.push(line);
      continue;
    }

    const bytes = await readFile(resolved.path);
    const contentHash = hash(bytes);
    const destination = assetDestination(
      sourceRoot,
      resolved.path,
      contentHash,
      usedDestinations,
    );
    let attribute = image.groups.attribute;
    if (!attribute) {
      let id = `fig:${slug(path.basename(rawDestination, path.extname(rawDestination)))}-${hash(`${rawDestination}\0${image.groups.caption}`).slice(0, 8)}`;
      let ordinal = 2;
      while (usedIds.has(id)) {
        id = `${id}-${ordinal}`;
        ordinal += 1;
      }
      usedIds.add(id);
      attribute = `{#${id}}`;
      rewrites.push({
        kind: "figure-id",
        line: index + 1,
        target: id,
      });
    }
    const rewritten = `${image.groups.indent}![${image.groups.caption}](${destination})${attribute}`;
    if (rewritten !== line) {
      rewrites.push({
        kind: "asset-path",
        line: index + 1,
        from: rawDestination,
        to: destination,
      });
    }
    resources.push({
      source: resolved.path,
      sourceRelative: toPosix(path.relative(sourceRoot, resolved.path)),
      destination,
      sha256: contentHash,
    });
    output.push(rewritten);
  }

  const lineEnding = text.includes("\r\n") ? "\r\n" : "\n";
  return {
    text: output.join(lineEnding),
    diagnostics,
    rewrites,
    resources,
    hasCitation,
  };
}
