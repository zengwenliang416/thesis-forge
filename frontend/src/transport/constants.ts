export const MANIFEST_FILENAME = "docforge.yaml" as const;
export const PROJECT_SCHEMA_VERSION = "docforge.project.v1" as const;
export const DEFAULT_SOURCE_FILENAME = "document.md" as const;

export const DEFAULT_OUTPUT_DIRECTORY = "build" as const;
export const DEFAULT_DOCX_FILENAME = "document.docx" as const;
export const DEFAULT_DOCX_PATH =
  `${DEFAULT_OUTPUT_DIRECTORY}/${DEFAULT_DOCX_FILENAME}` as const;

export const DEFAULT_REVIEW_DIRECTORY = "review" as const;
export const DEFAULT_REVIEW_MARKDOWN_FILENAME = "document.review.md" as const;
export const DEFAULT_REVIEW_MARKDOWN_PATH =
  `${DEFAULT_REVIEW_DIRECTORY}/${DEFAULT_REVIEW_MARKDOWN_FILENAME}` as const;
export const DEFAULT_REVIEW_MAP_FILENAME = "document.review-map.json" as const;
export const DEFAULT_REVIEW_MAP_PATH =
  `${DEFAULT_REVIEW_DIRECTORY}/${DEFAULT_REVIEW_MAP_FILENAME}` as const;

export const PROTOCOL_VERSION = "docforge.workbench.v1" as const;
export const BUILD_REPORT_SCHEMA_VERSION = "docforge.build-report.v2" as const;

export const OBSOLETE_PROTOCOL_VERSION = "thesisforge.workbench.v1" as const;
export const OBSOLETE_BUILD_REPORT_SCHEMA_VERSION =
  "thesisforge.build-report.v2" as const;
