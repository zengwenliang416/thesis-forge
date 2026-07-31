# Unit Coverage Notes

- Pytest collects 124 tests from 14 modules.
- All 20 approved user test cases map to behavior-facing tests in `test-map.json`.
- Focused runs cover 46 architecture/validation/compiler/DOCX tests, 29 application/acceptance/prototype/distribution tests, and 49 parser/template/bibliography/math/RenderPlan/CLI tests.
- OOXML assertions inspect package parts, relationships, fields, bookmarks, drawings, tables, OMML, footnotes, sections, headers, and footers rather than checking file existence only.
- Adversarial package checks cover CRC corruption, duplicate ZIP parts, malformed core semantics, stage failures, output preservation, and temporary cleanup.
- CodeGraph may not infer coverage for private XML helpers, but those helpers are exercised through public renderer and package behavior with direct XML assertions.
