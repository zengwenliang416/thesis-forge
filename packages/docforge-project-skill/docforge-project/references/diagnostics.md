# Diagnostics

## Metadata

- `DFP-METADATA-TITLE-LOCALIZED`: an unlocalized Front Matter title was
  preserved in a deterministic localized title slot.
- `DFP-METADATA-TITLE-FROM-H1`: the first level-one heading was preserved as
  required cover metadata.
- `DFP-METADATA-TITLE-FROM-FILENAME`: a document without title metadata or an
  H1 uses the Markdown filename as required cover metadata.

Every failure has a stable `code`, `severity`, bounded `target`, `message`, and
`action`. Error diagnostics block publication.

Common blocking families:

- `DFP-INPUT-*`: missing input, wrong extension, invalid UTF-8, or source escape.
- `DFP-DESTINATION-*`: an existing destination or unusable parent.
- `DFP-RESOURCE-*`: missing, remote, absolute, traversal, device, or symlink
  escape.
- `DFP-MARKDOWN-*`: inline images, executable/MDX/HTML constructs, malformed
  Front Matter, or duplicate semantic IDs that cannot be changed safely.
- `DFP-BIBLIOGRAPHY-*`: citations without an explicitly supplied local BibTeX.
- `DFP-DOCFORGE-*`: missing executable or failed inspect, validate, or build.
- `DFP-INSTALL-*`: unmanaged target, invalid packaged Skill, update, backup, or
  rollback failure.

Do not replace an error with a best-effort rewrite. Correct the input or provide
the missing explicit option, run `plan` again, then import.
