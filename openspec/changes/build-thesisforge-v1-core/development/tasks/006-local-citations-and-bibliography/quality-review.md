# Quality Review: 006-local-citations-and-bibliography

## Verdict

approved

Both prior quality findings are closed: footnote citation ordinals now follow
first rendered use, and reused `ValidationContext` instances no longer leak a
stale `bibliography_database` when the active rule set changes.

## Separation Of Concerns

- The footnote first-use fix is now owned in Compiler, which is the correct
  layer for citation-order semantics. `_initial_citation_numbers()` walks
  rendered block order, expands a footnote definition when its
  `FootnoteReference` is first encountered, and only falls back to
  `document.citations` for any still-unseen citations
  (`src/thesis_forge/core/compiler.py:549-604`). This removes the prior
  dependence on parser definition-block order without pushing ordering logic
  into Parser or Renderer.
- The stale-context fix is localized to validation lifecycle management:
  `validate_document()` clears the derived `bibliography_database` before
  executing the active rule set
  (`src/thesis_forge/core/validator.py:465-481`). That keeps bibliography state
  as per-run derived data instead of an implicit cross-run cache.
- I found no new architecture regression against the task packet boundaries.
  Bibliography loading/formatting remains DOCX-free, Parser still records
  structure only, Compiler emits renderer-neutral instructions, and DOCX
  rendering consumes resolved text.

## Component Cohesion / Coupling

- The citation-order repair is cohesive: the entire change lives inside the
  existing compilation helper that already owns ordinal assignment, using local
  `definitions`, `referenced_labels`, `expanded_footnotes`, and `seen_citations`
  state rather than introducing new cross-module coordination
  (`src/thesis_forge/core/compiler.py:549-604`).
- The validation-state repair reduces temporal coupling. Callers can now reuse a
  `ValidationContext` with different `rules` values without depending on
  `_validate_bibliography()` being present to repair stale state
  (`src/thesis_forge/core/validator.py:443-481`).
- I did not find new coupling from these fixes into CLI, Parser, bibliography
  engine, or DOCX internals.

## Test Quality

- The two prior quality findings now have direct regression coverage:
  `tests/test_compiler.py:197-242` proves first-use ordinals are assigned from
  footnote reference position even when `document.citations` still reflects the
  old parser registration order, and
  `tests/test_validator.py:368-408` proves a reused `ValidationContext` no
  longer leaks `bibliography_database` across runs when `rules` changes.
- Downstream rendering is also verified at the OOXML text surface:
  `tests/test_docx_renderer.py:746-796` asserts resolved citation text in body,
  footnote, and bibliography paragraphs, confirming the compiler fix survives
  rendering.
- I re-ran the targeted tests, a focused bibliography/compiler/validator/DOCX
  subset, the full pytest suite, and Ruff. All were green. There is still no
  finding-specific CLI assertion for the footnote-order case, but given the
  compiler-level regression, DOCX-level regression, and passing full CLI suite,
  I do not consider that a blocker for approval.

## Error Handling

- The previous silent stale-state failure is closed. When bibliography
  validation is skipped on a reused context, the state is now explicitly reset
  before rule execution (`src/thesis_forge/core/validator.py:469-475`), so
  downstream consumers cannot observe an old database by accident.
- The previous silent footnote-order failure is also closed. A direct runtime
  probe now yields `citation_order == ('smith2025', 'doe2024')`,
  `footnote_ordinals == (1,)`, and `body_ordinals == (2,)`, matching first
  rendered occurrence rather than definition placement.
- No new swallowed-error or generic-error pattern was introduced by these
  changes.

## Reuse / Duplication

- The fixes reuse existing compiler traversal and validation entrypoints instead
  of duplicating bibliography resolution or adding a second citation-ordering
  pass elsewhere.
- No new duplicated test scaffolding or parallel implementation path was added;
  the new tests sit in the owning compiler and validator suites and reuse the
  task fixtures already under the allowlist.

## Complexity Delta

- The compiler change adds a small amount of stateful traversal logic, but it is
  contained inside one helper and directly models the required first-use
  semantics. It replaces a wrong global assumption with a localized expansion
  rule rather than spreading conditional logic across Parser, Compiler, and
  Renderer.
- The validator change is minimal: one reset line at function entry plus a
  focused regression test. That is a net complexity reduction because correctness
  no longer depends on a specific rule being present.
- `src/thesis_forge/core/compiler.py` is still a large file at 799 lines, but
  this re-review did not find a material complexity regression attributable to
  the fix itself.

## Required Fixes

No additional fixes are required. The two previously reported quality findings
were re-tested and are closed in the current checkout.

## Reviewer Commands

- `.venv/bin/python -m pytest tests/test_compiler.py -k footnote_citation_at_reference_position` -> `1 passed`.
- `.venv/bin/python -m pytest tests/test_validator.py -k stale_bibliography_when_rules_change` -> `1 passed`.
- `.venv/bin/python -m pytest tests/test_docx_renderer.py -k body_footnote_and_bibliography_text` -> `1 passed`.
- `.venv/bin/python -c '...'` footnote-order probe -> `{'citation_order': ('smith2025', 'doe2024'), 'body_ordinals': (2,), 'footnote_ordinals': (1,)}`.
- `.venv/bin/python -c '...'` reused-context probe -> `{'first_issues': 0, 'after_first_loaded': True, 'second_issues': 0, 'after_second_cleared': True}`.
- `.venv/bin/python -m pytest tests/test_bibliography.py tests/test_validator.py tests/test_compiler.py tests/test_docx_renderer.py` -> `45 passed`.
- `.venv/bin/python -m pytest -p no:cacheprovider` -> `90 passed`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
