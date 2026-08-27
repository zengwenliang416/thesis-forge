# Spec Review: 008-end-to-end-verification

## Verdict

blocked

## Missing Requirements

- No implementation or acceptance-scope requirement is missing for items 8.1
  through 8.5. The full Python, frontend, Rust, E2E, OOXML, distribution,
  deterministic-output, facticity, installed macOS, and Microsoft Word
  evidence is present.
- Item 8.6 remains open because the locked project-scoped SpecNav Verification
  Runtime `2.0.0-alpha.2` is not installed. The project configuration requires
  `runtime_scope: project`, and no fallback runtime receipt may substitute for
  it.

## Extra Behavior

- No arbitrary-Markdown importer or npm Agent Skill work was started.
- No external publication, deployment, tag upload, or release mutation was
  performed. Local release and installed-application evidence is reported only
  as local evidence.
- Historical failed attempts remain append-only and are not rewritten to make
  the current run appear green.

## Misunderstood Requirements

- The system-executed and sensory results below are pre-Runtime supporting
  evidence. They do not close the change-level acceptance ledger by themselves.
- `acceptance.json` still contains `failing` statuses with null evidence
  references. This review does not edit that ledger or claim authoritative
  A1-A10 closure.
- The browser matrix used isolated port `4174` because an unrelated process
  occupied `4173`; the isolated run completed with intentional viewport skips
  and no failures. This is an environment caveat, not a product requirement
  change.

## Cannot Verify From Diff

- The locked SpecNav Verification Runtime and its project-scoped six-domain
  receipts are absent from `.specnav/runtime/verification/2.0.0-alpha.2`.
  Installation requires separate explicit approval.
- Fresh authoritative receipts cannot be bound to the final committed HEAD
  while the implementation remains an uncommitted working-tree state. The
  pre-Runtime evidence is still useful for review, but it is not a substitute
  for clean-HEAD receipt binding.
- The current macOS host does not provide a native Windows WebView2 installed
  receipt. The required sensory gate for this change is the installed macOS
  workbench and Microsoft Word flow; Windows remains broader platform evidence.

## Acceptance Assertions Verified (Pre-Runtime Evidence)

- `A1`: The real Python HTTP acceptance passed through DocForge workspace
  creation and build dispatch, and
  `development/tasks/006-workbench-desktop/evidence/macos-native-acceptance.json`
  records the installed `DocForge.app` opening a project containing
  `docforge.yaml` and `document.md`. Rust project tests also cover directory
  and explicit-manifest opening. These are supporting receipts, not final
  change-level closure.
- `A2`: The isolated distribution verifier completed `inspect`, `validate`,
  `review`, and `build` for `docforge-general`; visible DOCX checks found the
  common metadata and no academic-only labels. The real HTTP and CLI flows
  exercise the same neutral `document.md` and `docforge-standard` project
  contract.
- `A3`: The isolated distribution and template/compiler suites cover the
  academic fixture with its typed optional `academic` profile and academic
  template, alongside a general fixture that validates and builds without
  university, degree, advisor, student ID, or completion requirements.
- `A4`: Facticity reports zero active obsolete-identity findings after
  classifying historical and explicit-negative references. Focused tests reject
  obsolete manifest, package, BuildReport, workbench protocol, and
  `ThesisDocument` contracts without compatibility aliases or dispatch.
- `A5`: Python, TypeScript, and Rust identity constants and contract tests
  define `document.md`, `build/document.docx`,
  `review/document.review.md`, and
  `review/document.review-map.json`; the real HTTP and installed macOS
  receipts exercise the source and DOCX defaults.
- `A6`: Project-loader, application, and Rust boundary tests cover rejection of
  absolute, remote, traversal, and symlink-escape paths while accepting safe
  project-relative resources.
- `A7`: The full Python suite and direct OOXML/deterministic-output tests cover
  the Markdown-to-`ForgeDocument` pipeline, renderer boundaries, fields,
  bookmarks, OMML, sections, relationships, atomic replacement, and failure
  retention. Runtime and desktop tests additionally verify ordered
  `parse -> validate -> compile -> render -> finalize` stages, cancellation,
  stale-result behavior, and preservation of the previous output.
- `A8`: Python, TypeScript, HTTP, sidecar, Tauri, and frontend tests use the
  versioned DocForge protocol and BuildReport identities. The real HTTP test
  passed, and Rust project/protocol suites passed with `14` project tests and
  `32` protocol-contract tests, including obsolete-identity rejection.
- `A9`: The installed macOS receipt records neutral DocForge project identity,
  filenames, diagnostics, accessibility labels, the three-pane workbench,
  successful `document.docx` output, and Microsoft Word 16.112 generation and
  display of a valid `document.preview.pdf`.
- `A10`: The repository facticity scan reports zero active findings across
  examples, fixtures, documentation, package surfaces, CI, and release
  configuration. Distribution, release, and Task 007 repository-delivery
  evidence confirms active surfaces use the DocForge project contract and
  neutral filenames.

## Required Fixes

- One blocker remains: obtain explicit approval, install the locked
  project-scoped SpecNav Verification Runtime `2.0.0-alpha.2`, then rerun the
  development, six-domain verification, installation, promotion, and archive
  contracts with `fallback_used: false` and bind fresh A1-A10 receipts to the
  final committed HEAD. Preserve existing failed receipts append-only; do not
  fabricate or manually promote pre-Runtime evidence.
