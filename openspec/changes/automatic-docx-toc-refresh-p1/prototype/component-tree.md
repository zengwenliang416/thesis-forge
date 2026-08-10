# Component Seam Prototype

## Component Tree

```text
RenderPlan
└── TocInstruction

DocxRenderer
└── render TOC instruction
    ├── standalone toc.title paragraph ("目录")
    └── following real dirty TOC complex field paragraph

ApplicationDependencies
└── DocumentRefresher
    └── LibreOfficeDocumentRefresher
        ├── cross-platform executable discovery
        ├── isolated user profile and private UNO endpoint
        ├── hidden document load
        ├── document index / text field refresh
        ├── store back to temporary DOCX
        └── bounded process and profile cleanup

build_service finalization
├── render temporary DOCX
├── optional document refresh
├── validate DOCX package
└── atomic replace final output
```

## Cohesion Check

- One reason to change: Renderer changes only for OOXML structure; Office refresher changes only for
  local layout-engine automation; application service changes only for pipeline orchestration.
- State owner: `TocInstruction` owns TOC semantics; DOCX owns field/cache state; the refresher owns
  only its isolated process/profile lifecycle.
- Side effects: Renderer writes the explicit temporary DOCX; refresher may modify only that file and
  owned temporary profile; atomic replace remains the final publication side effect.

## Coupling Check

- Allowed imports: application refresher may use pathlib, tempfile, subprocess and platform/env
  inspection; application service may depend on the refresher protocol.
- Forbidden imports: Parser/Domain/Compiler/RenderPlan to Office or subprocess; DOCX Renderer to
  subprocess/UNO; CLI/Web/Tauri adapters to duplicated Office automation.
- Public API: existing `DocxRenderer.render` and `build_service` contracts stay stable;
  `ApplicationDependencies` gains an injectable refresher.
- Extraction target: one cross-platform executable resolver, one isolated refresh runner and one
  shared application hook; no platform branches in adapters.
