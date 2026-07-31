# Verification Plan: build-thesisforge-v1-core

## Verification Scope

- Active change: `build-thesisforge-v1-core`
- Development handoff: `openspec/changes/build-thesisforge-v1-core/development/handoff-to-verify.md`
- Git baseline: `00910ee` (`chore: establish ThesisForge development baseline`)
- Verification target: `eb05612` (`chore: complete installation and maintenance handoff`)
- Scope: V1 offline CLI/compiler, template-driven DOCX, safe builds,
  distribution installation, maintainer handoff, and the approved review-only
  HTML prototype.
- Non-goals: production desktop UI, AI authoring, cloud services, database
  migrations, package-index publication, and public release.

## Required Domains

1. Facticity
2. Static
3. Unit
4. Redteam
5. E2E
6. Sensory

## Evidence Plan

- Direct repository evidence beats summaries.
- Every green verdict requires command, file, runtime, screenshot, trace, or
  review evidence.
- Missing evidence is a blocker, not a warning.
- The 36 changed files between the baseline and target commits are mapped in
  `traceability-matrix.json`.
- Product runtime evidence uses the offline CLI and generated DOCX package.
- Browser evidence uses a fresh local Chrome run against the approved static
  prototype; prototype fixtures are not represented as live backend data.
- `verify/runtime-evidence.json` must record runtime and browser execution
  evidence. If `development/migrations/manifest.json` has `required=true`, it
  must also record database evidence.

## User-Aligned Test Case Gate

- Generate `verify/user-test-cases.md` and `verify/user-test-cases.json` from
  requirements, acceptance, prototype handoff, development tasks, and handoff.
- Ask the user to approve, edit, remove, or add cases.
- Freeze approval in `verify/user-test-case-signoff.json`.
- Map every approved case across all six domains in
  `verify/domain-case-matrix.json`.
- Six-domain verification is blocked until the signoff status is `approved`.
- The approval set contains 20 independently executable cases instead of six
  broad themes. They preserve the detailed 001-009 development slices and
  separately cover parser, validation, templates, compiler/RenderPlan, DOCX
  structures, safe builds, complete acceptance, distribution, maintenance and
  prototype review.

## Runtime Evidence Gate

- Start the application or relevant service and record the command, output,
  logs, or health check under the `runtime` surface.
- Run the approved user test cases in a real browser or equivalent automation
  and record screenshots, traces, or transcripts under the `browser` surface.
- When migrations are required, run database verification queries and record
  them under the `database` surface.
- A green domain report without matching runtime evidence is invalid.

## Planned Commands

- `make verify`
- Offline `inspect`, `validate`, and `build` with provider credentials removed,
  proxy variables cleared, and sockets blocked where the harness supports it.
- Focused architecture, validation, compiler, DOCX, application, acceptance,
  prototype, and distribution pytest suites.
- DOCX ZIP/CRC/XML inspection, `python-docx` reload, and LibreOffice
  DOCX-to-PDF conversion.
- Prototype logic harness and fresh Chrome desktop/mobile/state verification.
- CodeGraph verification-stage context/claims and SpecNav aggregate validation.

## Manual Reviews

- Inspect the generated DOCX/PDF for cover, abstracts, headings, figure, table,
  equation, citations, bibliography, acknowledgements, appendix, and page
  structures.
- Review prototype desktop/mobile layouts, all required states, keyboard/focus
  behavior, readability, and the explicit review-only boundary.
- Review maintainer documentation against the executed installation,
  packaging, and verification behavior.
