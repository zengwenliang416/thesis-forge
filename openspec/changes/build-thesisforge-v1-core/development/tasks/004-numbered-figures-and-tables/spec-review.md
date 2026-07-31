# Spec Review: 004-numbered-figures-and-tables

## Verdict

approved

## Missing Requirements

- None after review fixes.
- `4.1`: Compiler resolves validated source-relative assets and explicit,
  template-default and intrinsic figure width policies; Renderer creates real
  image relationships and drawings.
- `4.2`: Compiler supplies chapter-aware labels and Word-safe names; captions
  contain real matching bookmark start/end elements.
- `4.3`: Compiler produces typed header/body rows and cells with column
  alignment and rejects malformed column counts.
- `4.4`: Renderer creates real table objects, honors top/bottom caption
  placement, and emits tested `three_line`, `grid` and `plain` borders.
- `4.5`: tests directly inspect numbering text, image relationships, media
  parts, drawings, bookmarks, table objects, caption order and border XML.

## Extra Behavior

- No out-of-scope 005 implementation was added.
- Static reference, equation and footnote fallback output is inherited from the
  approved 003 baseline. This task neither changes it nor claims it as real
  `REF`, OMML or footnote behavior.
- Invalid image error normalization is within the 004 figure build error
  boundary and does not implement task 007 atomic replacement.

## Misunderstood Requirements

- The initial task brief incorrectly suggested that build could continue when a
  used figure/table template section was absent. The brief now matches the
  parent contract: fatal validation blocks that build.
- Renderer fallback defaults are defensive direct-call behavior and do not
  authorize bypassing Validator.

## Cannot Verify From Diff

- Word and WPS were not opened interactively. LibreOffice successfully opened
  and converted a generated DOCX containing a real figure, bookmarks and table.
- Full A5 is not verifiable in task 004 because TOC, SEQ, REF, PAGE, OMML,
  footnote, section, header and footer objects are assigned to task 005.

## Acceptance Assertions Verified

- `A4`: Compiler resolves deterministic figure/table numbering and bookmark
  names before rendering; Renderer only consumes typed resolved values.
- `A5`: verified only for the allocated real figure/table bookmark subset.
  Other A5 structures remain open for task 005.
- `A8`: full tests, static checks, architecture checks, direct package/XML
  assertions, package reload and LibreOffice conversion passed.

## Required Fixes

- None. The missing-template task wording, empty-table coverage and invalid
  image error path found during the first review were fixed and re-reviewed.

## Reviewer Commands

- `.venv/bin/python -m pytest` -> `54 passed`.
- `.venv/bin/ruff check .` -> passed.
- `.venv/bin/python -m pip check` -> passed.
- Offline example build and package inspection -> passed.
- Direct figure/table package inspection and python-docx reload -> passed.
- LibreOffice headless PDF conversion -> passed.
