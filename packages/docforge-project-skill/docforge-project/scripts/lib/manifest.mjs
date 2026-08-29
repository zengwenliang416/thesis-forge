function yamlScalar(value) {
  return JSON.stringify(String(value));
}

function emitLocalized(lines, key, value) {
  if (!value) {
    return;
  }
  lines.push(`  ${key}:`);
  if (value.zh) {
    lines.push(`    zh: ${yamlScalar(value.zh)}`);
  }
  if (value.en) {
    lines.push(`    en: ${yamlScalar(value.en)}`);
  }
}

export function serializeManifest(model) {
  const lines = [
    "schema: docforge.project.v1",
    "project:",
    `  id: ${yamlScalar(model.project.id)}`,
    `  language: ${yamlScalar(model.project.language)}`,
    "document:",
    "  source: document.md",
    "  type: general",
  ];

  const metadata = model.metadata;
  if (
    metadata.title ||
    metadata.subtitle ||
    metadata.authors.length > 0 ||
    metadata.organization ||
    metadata.date ||
    metadata.version ||
    metadata.keywords.length > 0
  ) {
    lines.push("metadata:");
    emitLocalized(lines, "title", metadata.title);
    emitLocalized(lines, "subtitle", metadata.subtitle);
    if (metadata.authors.length > 0) {
      lines.push("  authors:");
      for (const author of metadata.authors) {
        lines.push(`    - name: ${yamlScalar(author)}`);
      }
    }
    if (metadata.organization) {
      lines.push(`  organization: ${yamlScalar(metadata.organization)}`);
    }
    if (metadata.date) {
      lines.push(`  date: ${yamlScalar(metadata.date)}`);
    }
    if (metadata.version) {
      lines.push(`  version: ${yamlScalar(metadata.version)}`);
    }
    if (metadata.keywords.length > 0) {
      lines.push("  keywords:");
      for (const keyword of metadata.keywords) {
        lines.push(`    - ${yamlScalar(keyword)}`);
      }
    }
  }

  lines.push("resources:", "  root: .", "  assets: assets");
  if (model.bibliography) {
    lines.push("  bibliography: references.bib");
  }
  lines.push("render:", `  template_id: ${yamlScalar(model.templateId)}`);
  return `${lines.join("\n")}\n`;
}
