# DocForge Project Skill

`docforge-project` converts one UTF-8 Markdown file and its confined local
resources into a new DocForge Project Format V1 directory.

The Skill does not generate Word documents directly, write thesis content,
download remote resources, or modify an existing DocForge project. A successful
import must pass the installed `docforge inspect` and `docforge validate`
commands. `docforge build` runs only when build verification is explicitly
requested.

## Agent Use

Read `SKILL.md` for routing and workflow instructions. The deterministic
implementation is exposed through:

```bash
python3 scripts/docforge_project.py --help
```

The importer accepts `plan` and `import`; installation and rollback remain
explicit operations. See `references/project-format-v1.md`,
`references/security-boundary.md`, and `references/diagnostics.md` for the
format, trust boundary, and stable diagnostic contract.

## Runtime Boundary

- Node.js 20 or newer
- A local `docforge` executable, or an explicit `--docforge-bin`
- Local files only; network access is forbidden
- New destinations only; existing projects are never merged or overwritten
- Managed Skill updates create a reported sibling backup before replacement

The package's trust report covers the Python bridge. The JavaScript importer is
also constrained by tests and the declared permission policy, but Yao 2.1.0
does not provide complete transitive static analysis for `.mjs` files. See
`reports/trust-supplement.md` for that limitation.
