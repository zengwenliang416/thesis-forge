# DocForge Project Format V1

The importer creates this neutral project shape:

```text
<project>/
├── docforge.yaml
├── document.md
├── assets/
├── build/
├── review/
├── import-report.json
├── references.bib       # only when explicitly supplied
└── source/original.md   # only when document.md changed
```

The minimal manifest uses:

```yaml
schema: docforge.project.v1
project:
  id: <deterministic-valid-id>
  language: und
document:
  source: document.md
  type: general
resources:
  root: .
  assets: assets
render:
  template_id: docforge-standard
```

Output and Review paths are omitted so DocForge remains authoritative for
`build/document.docx`, `review/document.review.md`, and
`review/document.review-map.json`.

Only explicit neutral metadata may be added. Academic fields are never inferred.
Project validity is established by the installed CLI, not by this reference.
