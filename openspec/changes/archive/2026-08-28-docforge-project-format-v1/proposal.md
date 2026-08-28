## Why

The product is now a general Markdown-based document workbench, but its public
project contract, CLI, runtime protocol, domain model, default filenames, and
metadata remain thesis-specific. This mismatch blocks a credible generic
Markdown project importer and misrepresents DocForge as an academic-only tool.

## What Changes

- **BREAKING** Replace `thesisforge.yaml` with `docforge.yaml` as the only
  accepted project manifest.
- **BREAKING** Replace `thesisforge.project.v2` with `docforge.project.v1`.
- **BREAKING** Replace default source and generated filenames based on
  `thesis` with neutral `document` names.
- **BREAKING** Rename the public CLI, Python package/runtime identifiers,
  workbench protocol, and core `ThesisDocument` domain type to DocForge terms.
- Introduce a generic document type and common metadata model.
- Move student, institution, degree, and advisor data into an optional,
  explicitly academic profile.
- Introduce a `docforge-standard` template that builds ordinary documents
  without fabricated academic metadata.
- Preserve the deterministic
  `Markdown -> domain document -> validation -> template -> RenderPlan -> DOCX`
  architecture and all path-security boundaries.
- Convert repository-owned fixtures, examples, documentation, desktop
  packaging, CI checks, and runtime contracts to the new format.
- Reject obsolete ThesisForge manifests and protocol identifiers with stable,
  actionable diagnostics; do not maintain dual loaders or compatibility aliases.

## Capabilities

### New Capabilities

- `docforge-project-format`: Generic project directory, manifest, path, output,
  review, metadata, and document-type contracts.
- `document-markdown-model`: Generic Markdown-backed domain document and stable
  semantic object model.
- `docforge-runtime-contract`: DocForge CLI, Python package, sidecar, transport,
  and workbench protocol identity.
- `generic-document-template`: A bundled template for non-academic documents
  with no thesis-only metadata requirements.

### Modified Capabilities

- `offline-cli-pipeline`: Accept DocForge projects and expose the `docforge`
  command while preserving the deterministic offline pipeline.
- `desktop-workbench`: Open `docforge.yaml` projects and present neutral
  document terminology.
- `validation-template-resolution`: Validate the new manifest, generic metadata,
  academic profile, template compatibility, and project-relative resources.
- `render-plan-docx`: Use neutral document output identities without changing
  the renderer-neutral plan or true OOXML behavior.
- `bibliography-citations`: Resolve optional bibliography resources from the
  DocForge manifest.

## Impact

- Python package layout, CLI entrypoint, imports, project/domain models,
  diagnostics, template metadata mapping, application services, and tests.
- Frontend transport protocol constants, DTO fixtures, product copy, project
  picker filters, and workspace identity.
- Tauri package/sidecar names, commands, distribution verification, and release
  configuration.
- Repository examples, canonical fixtures, documentation, CI scripts, and
  packaged templates.
- Existing ThesisForge project directories become invalid after the cutover;
  repository-owned projects are converted in the same change.
