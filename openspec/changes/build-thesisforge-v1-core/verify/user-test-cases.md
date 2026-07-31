# User-Aligned Test Cases: build-thesisforge-v1-core

## User Test Case Scope

- Source requirements: `openspec/changes/build-thesisforge-v1-core/requirements.md`
- Acceptance criteria: `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- Prototype handoff: `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`
- Development handoff: `openspec/changes/build-thesisforge-v1-core/development/handoff-to-verify.md`
- Detail policy: preserve all 001-009 vertical slices and verify distinct
  behaviors independently instead of collapsing them into broad themes.

## Aligned Test Cases

| ID | Actor | Independently verified outcome | Primary acceptance |
| --- | --- | --- | --- |
| `utc-01-inspect-semantic-inventory` | 论文作者 | inspect reports every V1 object and source location without writes | A1, A2 |
| `utc-02-parser-malformed-and-boundaries` | 开发者 | malformed syntax fails deterministically; Parser/Domain boundaries hold | A2, A8 |
| `utc-03-validation-diagnostic-coverage` | 论文作者 | all required structured diagnostics are reported | A3 |
| `utc-04-validation-exit-and-ordering` | 作者/自动化调用者 | exit codes, warning policy and issue ordering remain stable | A3, A8 |
| `utc-05-template-resolution-and-schema` | 模板维护者 | path/template_id resolution and typed schema errors are correct | A3, A8 |
| `utc-06-compiler-renderplan-determinism` | 开发者 | numbering, bookmarks, references, citations and sections compile before render | A4, A8 |
| `utc-07-basic-docx-layout` | 作者/模板维护者 | page, fonts, paragraphs and headings are template-driven | A4, A5 |
| `utc-08-numbered-figures-and-tables` | 论文作者 | images, captions, bookmarks and tables are real editable objects | A4, A5 |
| `utc-09-equations-fields-and-crossrefs` | 作者/审核者 | OMML, TOC, SEQ, REF and bookmarks are real Word objects | A4, A5 |
| `utc-10-footnotes-sections-and-pagination` | 作者/审核者 | footnotes, sections, headers, footers and page fields are real structures | A4, A5 |
| `utc-11-local-citations-and-bibliography` | 论文作者 | local BibTeX validation and deterministic citation output work offline | A3, A4, A5 |
| `utc-12-failed-build-preserves-output` | 论文作者 | every failed stage preserves the previous valid DOCX | A7 |
| `utc-13-repeatable-semantic-builds` | 作者/维护者 | repeated builds preserve normalized semantic equivalence | A4, A7, A8 |
| `utc-14-complete-offline-example` | 作者/验收者 | complete example passes inspect/validate/build without network or credentials | A1, A5, A8 |
| `utc-15-docx-package-and-office-acceptance` | 文档审核者 | package is valid and opens with visible, editable content | A5, A6 |
| `utc-16-wheel-sdist-content` | 新贡献者/维护者 | distribution contents, metadata and contamination policy are correct | A8 |
| `utc-17-hermetic-installed-wheel` | 新贡献者/维护者 | installed wheel runs offline outside checkout without parent leakage | A1, A8 |
| `utc-18-maintainer-documentation-and-evidence` | 贡献者/最终审核者 | docs, task packets, reviews and ledgers match current behavior | A8 |
| `utc-19-prototype-desktop-workbench` | 产品/文档审核者 | desktop workbench presents all required panels and controls | A9 |
| `utc-20-prototype-mobile-states-accessibility` | 产品/无障碍审核者 | mobile navigation, six states, focus, ARIA and reduced-motion are covered | A9 |

Detailed preconditions, steps, expected results, boundary cases, acceptance
references and source references are authoritative in
`verify/user-test-cases.json`.

## User Signoff

Status: `approved`

The user approved all 20 cases on July 31, 2026. No cases were rejected or
removed.

## Domain Mapping

Every proposed case is independently mapped in `domain-case-matrix.json` to
facticity, static, unit, redteam, e2e and sensory. Approval activates the
entire detailed set; a domain cannot substitute one broad run for these
case-level checks.
