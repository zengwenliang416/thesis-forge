# Security And Permission Boundary

The Skill is offline but not read-only.

Approved capabilities:

- `file_write`: one sibling staging directory, one new project destination,
  explicit managed Skill installation/update paths, and reported backups.
- `subprocess`: the local Node runtime and the installed `docforge` CLI for
  `inspect`, `validate`, and explicitly requested `build`.

Forbidden capabilities:

- network requests and remote resource downloads;
- shell-string execution;
- writes into the Yao engine;
- writes outside the explicit destination, its owned staging sibling, or an
  explicit managed Skill installation path;
- direct DOCX rendering, Office automation, AI providers, and databases.

Yao 2.1.0 inventories `.py`, `.sh`, `.js`, and `.ts` resources in Skill IR but
its trust scanner statically analyzes only top-level `.py` files. The Python
bridge makes subprocess use visible. The governed permission policy also
declares the transitive `file_write` performed by the canonical `.mjs`
importer. This limitation remains reviewer-visible and is not presented as
native host enforcement.
