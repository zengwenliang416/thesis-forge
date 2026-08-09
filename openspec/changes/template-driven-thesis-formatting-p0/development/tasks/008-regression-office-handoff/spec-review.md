# Spec Review: 008-regression-office-handoff

## Verdict

approved

## Missing Requirements

- None.
- The user-requested Heading 1-3 policy is present in
  `templates/schools/hunan-university-of-technology/master-2026.yaml`: each
  level declares `color: "000000"`, `alignment: left`, `left_indent: 0pt`,
  `right_indent: 0pt` and `first_line_indent: 0pt`.
- `ParagraphStyleSpec` validates `color` as `auto` or six hexadecimal digits,
  while alignment and indentation continue to use the existing typed common
  paragraph policy.
- The shared DOCX paragraph-style translator passes template color through the
  renderer-owned font helper, writes real `w:color`, removes stale
  `themeColor`/`themeTint`/`themeShade`, and writes alignment and indentation
  through the existing paragraph formatter.
- Independent package inspection of the current `f59c81f` artifact confirmed
  Heading1, Heading2 and Heading3 each contain `w:color w:val="000000"`,
  `w:jc w:val="left"` and `w:ind` with `left`, `right` and `firstLine` all
  equal to `0`.
- Parser, ThesisDocument, Compiler and RenderPlan were not changed by
  `7fe89f7..f59c81f`; architecture tests confirm those layers remain free of
  DOCX/OOXML implementation dependencies.

## Extra Behavior

- None.
- The production correction is limited to the already approved common
  `ParagraphStyleSpec -> shared DOCX paragraph translator` seam, HUT YAML,
  documentation and focused tests.
- The reusable color property applies to the same body, heading, semantic, TOC,
  bibliography and header/footer paragraph-policy contract rather than adding
  a school-specific renderer branch.
- No UI, transport, database, network, AI, CI, release or deployment behavior
  was added.

## Misunderstood Requirements

- None.
- Heading color, alignment and left/right/first-line indentation are treated as
  YAML-owned policy, not renderer constants.
- Explicit black clears Word theme-color inheritance instead of relying on
  visual defaults.
- WPS is the primary Office acceptance client. Microsoft Word did not open the
  artifact and no Word rendering claim is made. LibreOffice remains
  compatibility-only evidence.
- The current WPS artifact successfully updated its real TOC through
  `引用 -> 更新目录`, increasing the word count from `1199` to `1299`.
  `wps-current-toc-updated.png` directly shows hierarchical entries, dot
  leaders and right-aligned page numbers.

## Cannot Verify From Diff

- Microsoft Word layout was not verified because automated file selection timed
  out. This is non-blocking because A10 requires Microsoft Word or WPS and the
  byte-identical current artifact was directly reviewed in WPS.
- Pixel-identical pagination across WPS and LibreOffice is not verified and is
  explicitly out of scope.
- CI and release deployment were not verified because task 008 defines local
  system-executed validation as authoritative and excludes release work.
- The recorded full frontend, browser, Rust, package and Office commands were
  reviewed from append-only `validation-log.jsonl` entries with
  `attestation: "system-executed"`. Independent replay in this review focused
  on the specification-critical Python, OOXML and architecture surfaces.

## Acceptance Assertions Verified

- A1: verified typed YAML paragraph policy and current Heading1-3
  `w:color`/`w:jc`/`w:ind` output; body spacing, indentation, line spacing and
  pagination assertions remain covered by the complete acceptance test.
- A2: verified omitted color remains `None`, invalid colors are rejected, and
  the current full regression retains legacy-template coverage.
- A3: verified independent Chinese/English abstract and keyword styles remain
  present in the complete DOCX and current WPS artifact.
- A4: verified the real TOC field plus TOC 1-3 indentation, spacing, right tabs
  and leaders through direct OOXML tests; WPS `引用 -> 更新目录` successfully
  updated the current artifact from `1199` to `1299` words, and
  `wps-current-toc-updated.png` shows hierarchical entries, dot leaders and
  right-aligned page numbers.
- A5: verified citation superscript and bibliography hanging-indent/spacing
  assertions remain in the current acceptance package and WPS review.
- A6: verified first/default/even header/footer relationships, distances,
  borders and page fields remain covered and visible in the current WPS
  evidence.
- A7: verified architecture tests preserve semantic resolution before
  rendering and keep RenderPlan free of DOCX/OOXML objects.
- A8: verified HUT values originate in YAML, renderer sources contain no HUT
  constants, and current deterministic/offline tests pass.
- A9: verified the current complete artifact is a valid editable DOCX with
  focused package and OOXML assertions; source and WPS-copy SHA-256 values both
  equal `14cc3a07788bae9f1f5d69e27713f8bcc9bd57cca459d366d136eb29571e3325`.
- A10: verified the current artifact opened editable in WPS and direct sensory
  evidence covers abstracts, Heading 1-3, body, figure, table, equation,
  bibliography, headers and page numbering; the current real TOC also updated
  successfully to populated hierarchical dot-leader entries with right-aligned
  page numbers.

## Required Fixes

- None.
- Independent validation executed:
  `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider
  tests/test_template.py tests/test_docx_renderer.py tests/test_acceptance.py
  tests/test_architecture.py -q` -> `141 passed in 7.53s`.
- Independent `.venv/bin/ruff check .` and `git diff --check` passed.
