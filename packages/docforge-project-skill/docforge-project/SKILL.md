---
name: docforge-project
description: Convert one ordinary Markdown file and confined local resources into a new, verified DocForge Project Format V1 directory. Use for creating an importable DocForge project. Do not use for direct Markdown-to-Word conversion, thesis writing, translation, summaries, format explanations, remote downloads, or editing an existing DocForge project.
---

# DocForge Project

Create a new DocForge project with the deterministic importer. Do not recreate
its path checks, Markdown rewrites, manifest serialization, or verification
steps manually.

## Required Inputs

- One UTF-8 `.md` or `.markdown` file.
- One destination directory that does not exist.
- Optional local images referenced by the Markdown.
- Optional local BibTeX supplied with `--bibtex`.
- A local `docforge` executable on `PATH` or supplied with `--docforge-bin`.

Ask one focused question only when the source file or destination is unknown.
Do not ask for metadata that can safely remain unset.

## Workflow

1. Confirm the destination does not exist and the request is project creation,
   not direct Word conversion or an edit to an existing project.
2. Run a plan first:

   ```bash
   python3 "$SKILL_ROOT/scripts/docforge_project.py" plan <source.md> <destination>
   ```

3. Resolve every blocking diagnostic. Never bypass a path, encoding, remote
   resource, unsupported syntax, missing bibliography, or runtime failure.
4. Import through the same script:

   ```bash
   python3 "$SKILL_ROOT/scripts/docforge_project.py" import <source.md> <destination>
   ```

5. Add `--bibtex <local.bib>` for citations. Add `--build` only when the user
   requests DOCX build verification.
6. Report the new project path, project ID, rewrites, copied resources, and
   completed `inspect`/`validate` checks. State build status separately.

## Non-Negotiable Boundaries

- Never write a DOCX directly. Only `docforge build` may do that.
- Never fetch remote resources, execute Markdown, or call an AI provider.
- Never merge into or overwrite an existing destination.
- Never invent author, student, institution, degree, advisor, or thesis data.
- Keep the source boundary confined; reject traversal and symlink escape.
- Preserve `source/original.md` whenever `document.md` changes.
- Treat `docforge inspect` and `docforge validate --json` as completion oracles.

Read [project-format-v1.md](references/project-format-v1.md) for the output
tree, [diagnostics.md](references/diagnostics.md) for blocking failures, and
[security-boundary.md](references/security-boundary.md) for permissions.
Maintainers must run the trigger, boundary, and output cases under `evals/`
before promotion; unavailable human or provider evidence remains explicitly
`missing evidence`.
