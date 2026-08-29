import { diagnostic } from "./diagnostics.mjs";

function unquote(value) {
  const trimmed = value.trim();
  if (
    trimmed.length >= 2 &&
    ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
      (trimmed.startsWith("'") && trimmed.endsWith("'")))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseList(value) {
  const trimmed = value.trim();
  if (!trimmed.startsWith("[") || !trimmed.endsWith("]")) {
    return null;
  }
  const body = trimmed.slice(1, -1).trim();
  if (!body) {
    return [];
  }
  return body.split(",").map((item) => unquote(item).trim()).filter(Boolean);
}

export function extractFrontMatter(text) {
  if (!text.startsWith("---\n") && !text.startsWith("---\r\n")) {
    return {
      body: text,
      values: {},
      unknownKeys: [],
      diagnostics: [],
      changed: false,
    };
  }

  const lines = text.split(/\r?\n/);
  const closeIndex = lines.findIndex((line, index) => index > 0 && line.trim() === "---");
  if (closeIndex < 0) {
    return {
      body: text,
      values: {},
      unknownKeys: [],
      diagnostics: [
        diagnostic(
          "DFP-MARKDOWN-FRONTMATTER-UNCLOSED",
          "error",
          "front-matter",
          "YAML Front Matter is not closed.",
          "Add a closing --- delimiter or remove the opening delimiter.",
          1,
        ),
      ],
      changed: false,
    };
  }

  const values = {};
  const unknownKeys = [];
  const diagnostics = [];
  const known = new Set([
    "language",
    "lang",
    "title",
    "title_zh",
    "title_en",
    "author",
    "authors",
    "organization",
    "date",
    "version",
    "keywords",
    "template_id",
  ]);

  for (let index = 1; index < closeIndex; index += 1) {
    const line = lines[index];
    if (!line.trim() || line.trimStart().startsWith("#")) {
      continue;
    }
    const match = /^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$/.exec(line);
    if (!match) {
      diagnostics.push(
        diagnostic(
          "DFP-MARKDOWN-FRONTMATTER-UNSUPPORTED",
          "error",
          `line:${index + 1}`,
          "Front Matter must use flat scalar fields or inline scalar lists.",
          "Flatten the metadata or pass supported values as CLI options.",
          index + 1,
        ),
      );
      continue;
    }
    const [, key, rawValue] = match;
    if (!known.has(key)) {
      unknownKeys.push(key);
      continue;
    }
    const list = parseList(rawValue);
    values[key] = list ?? unquote(rawValue);
  }

  const separator = text.includes("\r\n") ? "\r\n" : "\n";
  const body = lines.slice(closeIndex + 1).join(separator).replace(/^(?:\r?\n)+/, "");
  return { body, values, unknownKeys, diagnostics, changed: true };
}
