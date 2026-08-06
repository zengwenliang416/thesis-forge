# Spec Review: 003-semantic-roles

## Verdict

approved

Task 003 is approved at its own semantic-role boundary. The prior
inherited-`em` defect is fixed: partial semantic title/body policies can omit
`size`, use `em` spacing/indentation/fixed line spacing, and convert against
the effective Heading or body/Normal size without emitting an unintended child
font-size override.

## Missing Requirements

None found within tasks 3.1-3.7.

- `ParagraphRole` is closed and renderer-neutral; heading and paragraph
  instructions retain compatible defaults.
- Compiler state is compile-scoped, uses stable heading IDs, preserves
  abstract context across nested headings, exits at the next H1 boundary, and
  restricts keyword labels to the matching abstract and paragraph start.
- Missing semantic policies use deterministic Heading/body fallback.
- DOCX role lookup creates stable internal styles and keeps Word style IDs out
  of RenderPlan.
- Partial semantic styles use `em_size_pt` only as a conversion base. When
  `size` is omitted, `apply_font()` receives no size, so `styles.xml` has no
  unintended child `w:sz` or `w:szCs`.

## Extra Behavior

None found in the allowed implementation/test scope. The acceptance test
change replaces a stale direct-`Heading1` assertion with the required
semantic title style and is listed in the task allowlist.

## Misunderstood Requirements

None found. Compiler owns semantic resolution, RenderPlan remains free of
DOCX/OOXML implementation objects, and the renderer owns template-policy
translation. Heading-based semantic roles inherit the effective Heading style;
body, keyword and bibliography-entry roles inherit Normal/body policy.

## Cannot Verify From Diff

- Change-level A8 offline CLI completion, full P0 build coverage and Office
  sensory review remain downstream tasks and are not claimed for task 003.
- `acceptance.json` still records change-level A1-A10 statuses as `failing`;
  this task review does not mutate that ledger.
- The required change-level handoff probe returned `ok:false` before this final
  review write because the active change still has incomplete later-task
  checkboxes/statuses and global scaffold/migration blockers. Those blockers
  are outside task 003 and cannot be repaired under the instruction to write
  only this review file.
- The task-specific entry probe returned `ok:true`; CodeGraph guard returned
  `ok:true`; `ev-mscvzqsv` matched task 003 with no blockers. No post-write
  handoff rerun is claimed.

## Acceptance Assertions Verified

- **A3**: Verified for this slice. The focused suite and saved-package
  assertions cover independent Chinese/English abstract title/body/keyword
  roles, stable semantic `w:pStyle` bindings, Heading/Normal inheritance,
  `em` spacing/indentation/fixed line spacing, and absence of child font-size
  elements for partial policies.
- **A7**: Verified. RenderPlan/compiler architecture tests and source
  inspection prove semantic roles are resolved before rendering and core and
  RenderPlan remain free of DOCX/OOXML implementation dependencies.
- **A8**: Verified for the task-scoped clauses. Renderer inspection,
  architecture tests, repeated-compile coverage, Ruff and whitespace checks
  show no school-specific renderer constants, correct dependency direction and
  deterministic semantic compilation. Broader offline CLI and sensory clauses
  remain downstream and unclaimed.

## Required Fixes

None for task 003.

## Independent Evidence

- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py tests/test_architecture.py tests/test_acceptance.py -q`
  -> `79 passed in 10.25s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `git diff --check` -> exit 0 with no output.
- `node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode entry --json`
  -> `ok:true`, active change `template-driven-thesis-formatting-p0`,
  no blockers.
- `codegraph/guard-report.json` -> `ok:true`, active change
  `template-driven-thesis-formatting-p0`, no blockers.
- `codegraph/evidence.jsonl` -> `ev-mscvzqsv`, task
  `003-semantic-roles`, `confidence: matched`, `blockers: []`.
- `development/validation-log.jsonl` contains matching task-003
  `attestation: "system-executed"` entries for the focused suite, Ruff and
  `git diff --check`.
