# docforge-project-skill

`docforge-project-skill` packages the `docforge-project` Agent Skill and its
deterministic importer. It creates a new DocForge Project Format V1 directory
from one Markdown file and confined local resources.

It does not generate DOCX directly. A successful import is accepted only after
the installed `docforge` CLI passes `inspect` and `validate`.

## Import

```bash
npx docforge-project-skill import notes.md ./notes-project
```

Use `--bibtex references.bib` when the Markdown contains citations. Add
`--build` only when you also want the installed DocForge runtime to verify DOCX
generation.

## Install Into Codex

```bash
npx docforge-project-skill install --target codex
```

Installation is explicit. The package has no npm lifecycle installer. Existing
unmanaged Skill directories are never overwritten; a managed update requires
`--update` and creates a recoverable sibling backup. Restart Codex or reload
its Skill registry before first use.

## Runtime

- Node.js 20 or newer
- A local `docforge` executable on `PATH`, or `--docforge-bin <path>`
- No network, AI provider, Office application, or database is required for
  project creation
