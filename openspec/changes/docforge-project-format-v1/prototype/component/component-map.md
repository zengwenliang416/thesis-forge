# Component Map

## Proposed Shared Components

- `DocForgeProjectConstants` per language boundary owns `docforge.yaml`,
  `docforge.project.v1`, `document.md`, neutral output and Review defaults,
  `docforge.workbench.v1`, and `docforge.build-report.v2`.
- `DocForgeProjectManifest` owns strict project, document, generic metadata,
  optional academic profile, resources, render, layout, output, and Review
  values.
- `ForgeDocument` replaces `ThesisDocument` as the only core aggregate while
  retaining semantic block, inline, location, stable-ID, reference, citation,
  and bibliography structures.
- `DocForgeProtocolFixtures` define shared request, response, progress,
  diagnostic, build report, output, and final-preview identities consumed by
  Python, TypeScript, and Rust tests.
- `docforge-standard` supplies generic template bindings without academic
  placeholders.

## Reused Components

- Existing project-relative path normalization and symlink containment checks.
- Existing Markdown parser and semantic block and inline models.
- Existing validation issue pipeline and template resolver.
- Existing compiler, numbering, reference, bibliography, and RenderPlan
  services.
- Existing DOCX renderer, finalization, postflight, Review, preview,
  cancellation, and atomic output services.
- Existing `WorkbenchTransport`, workspace state, HTTP adapter, and Tauri
  command bridge.

## Hooks

- Reuse workspace operation generation and stale-result suppression.
- Reuse cooperative build cancellation and progress event handling.
- Reuse diagnostic activation and source-line focus behavior.
- Do not add profile-specific React hooks; profile values arrive through shared
  project and preview DTOs.

## Utilities / Services

- `load_docforge_project(entrypoint) -> ResolvedDocForgeProject`
- `parse_markdown(path_or_snapshot) -> ForgeDocument`
- `validate_document(project, document, template) -> ValidationIssue[]`
- `compile_document(project, document, template, bibliography) -> RenderPlan`
- `render_document(plan, output) -> Path`
- Shared `inspect`, `validate`, `review`, and `build` application services.
- Per-language protocol validators backed by matching contract fixtures.

## Public API Boundary

```text
directory | docforge.yaml
  -> DocForgeProjectLoader
  -> ResolvedDocForgeProject
  -> MarkdownParser
  -> ForgeDocument
  -> Validator + TemplateResolver + Bibliography
  -> Compiler
  -> RenderPlan
  -> DOCX Renderer
  -> Finalize + Postflight + Preview
```

Adapters may submit typed intents and serialize results, but they do not own a
second project, document, validation, compiler, or renderer model.

## Rejection Boundary

- `DocForgeProjectLoader` rejects bare Markdown, `thesisforge.yaml`,
  `thesisforge.project.v2`, unknown fields, and unsafe project paths.
- Protocol validators reject `thesisforge.workbench.v1` and
  `thesisforge.build-report.v2` before application dispatch or output
  authorization.
- Template validation rejects missing template-declared profile data.
- Validator failures stop before Compiler and Renderer.

## Prototype Execution

Run `node prototype/component/verify.mjs` from the change directory. The
checker loads `component/contract-fixtures.json`, verifies component ownership
and forbidden dependencies, and executes the general, academic, obsolete
contract, unsafe path, and old protocol cases.
