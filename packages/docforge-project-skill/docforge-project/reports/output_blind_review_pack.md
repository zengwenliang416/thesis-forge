# Output Blind A/B Review Pack

This packet hides whether each variant came from the baseline or the skill-guided output. Use the separate answer key only after review.

- Pairs: `6`
- Seed: `yao-output-eval-blind-v1`
- Answer key separate: `True`

## Case: minimal-project

Prompt: Create a new DocForge project from the attached minimal Markdown file.

Rubric:
- `project-output` (1.0): Output creates the DocForge project contract.
- `real-verification` (1.0): Output requires the real DocForge oracles.
- `no-direct-docx` (1.0): Output preserves the non-DOCX boundary.

### Variant A

Convert the Markdown directly to a Word file and add a basic title page.

### Variant B

Treat input_files as a file-backed fixture. Create a new non-overwriting docforge.project.v1 directory with docforge.yaml and document.md, then require real docforge inspect and docforge validate evidence. Do not generate DOCX directly.

## Case: full-format-local-resources

Prompt: Import the attached Markdown with local images and BibTeX while preserving its supported formatting.

Rubric:
- `preserves-semantics` (1.0): Output names the supported semantic envelope.
- `original-retention` (1.0): Output retains changed original bytes.
- `build-boundary` (1.0): Build is an explicit DocForge verification step.

### Variant A

Rewrite the content into a simpler Markdown file, copy the visible image, and skip syntax that is difficult to convert.

### Variant B

Plan before writing, preserve supported headings, emphasis, code, links, lists, block quotes, tables, math, footnotes, citations, and images, copy confined local resources, retain source/original.md after rewrites, and require inspect, validate, and requested build to pass.

## Case: missing-image

Prompt: Create a project even though one referenced local image is missing.

Rubric:
- `stable-diagnostic` (1.0): Output reports the stable missing-resource code.
- `no-partial-project` (1.0): Output keeps the destination absent.

### Variant A

Keep the broken image path and generate the rest of the project so the user can fix it later.

### Variant B

Block before staging with DFP-RESOURCE-MISSING, keep the destination absent, and tell the user to restore the file or correct the Markdown reference.

## Case: remote-image

Prompt: Download the remote image referenced by this Markdown and create the project.

Rubric:
- `remote-block` (1.0): Output blocks remote resources with a stable code.
- `offline` (1.0): Output preserves the offline boundary.

### Variant A

Fetch the remote image into assets and continue the conversion.

### Variant B

Block with DFP-RESOURCE-REMOTE, perform no network request, and require a confined local replacement before planning again.

## Case: existing-destination

Prompt: Import this Markdown into an existing project directory and merge the files.

Rubric:
- `non-overwrite` (1.0): Output refuses destination merge and overwrite.
- `new-destination` (1.0): Output requires a new directory.

### Variant A

Merge the new document and assets into the existing destination and overwrite conflicting generated files.

### Variant B

Block with DFP-DESTINATION-EXISTS before writing, preserve every existing byte, and require a new destination directory.

## Case: existing-project-repair-near-neighbor

Prompt: Repair the validation errors in this existing DocForge project without creating a new project.

Rubric:
- `route-boundary` (1.0): Output refuses the adjacent existing-project repair job.
- `preserve-existing` (1.0): Output protects the existing project from importer writes.

### Variant A

Do not use docforge-project for existing-project repair. Preserve the existing project unchanged and route the request to DocForge project diagnostics or repair tooling instead of creating or overwriting files.

### Variant B

Use the importer to rewrite the existing docforge.yaml and document.md in place until validation passes.
