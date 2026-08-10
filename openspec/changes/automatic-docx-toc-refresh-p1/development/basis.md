# Development Basis: automatic-docx-toc-refresh-p1

## Requirements Reference

- `openspec/changes/automatic-docx-toc-refresh-p1/requirements.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/acceptance.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/spec-map.json`
- `openspec/changes/automatic-docx-toc-refresh-p1/component-impact-map.json`

## Prototype Reference

- `openspec/changes/automatic-docx-toc-refresh-p1/prototype/handoff.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/prototype/decision.json`
- `openspec/changes/automatic-docx-toc-refresh-p1/prototype/component/component-map.md`

## Foundation Spec Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Handoff Reference

- Prototype contract returned `ok:true` after user approval of
  `toc-field-office-refresh-seam-v1`.
- Production implementation starts from Git baseline `5277fb7`, which tracks the approved
  prototype decision and the unchanged 11-task `tasks.md` baseline.
- Scope is locked by `openspec/changes/automatic-docx-toc-refresh-p1/scope.json`.

## Implementation Boundary

- Renderer emits a standalone `toc.title` paragraph and a following real dirty TOC field.
- Application finalization owns optional local Office refresh orchestration.
- LibreOffice discovery, UNO automation, timeout and cleanup remain in
  `application/office_refresh.py`.
- Parser, Domain, Compiler and RenderPlan remain unchanged and Office-independent.
- Package validation and atomic output replacement remain mandatory after optional refresh.

## Component Architecture Constraint

- Reuse `add_complex_field`, `set_update_fields`, `temporary_output_path`,
  `validate_docx_package` and `replace_output`.
- Keep one `DocumentRefresher` application hook and one default LibreOffice implementation.
- Keep executable discovery cross-platform but centralized.
- Do not duplicate Office automation in CLI, Web, Tauri or DOCX Renderer.
- Do not introduce UI, database, network, AI or mandatory external runtime dependencies.
