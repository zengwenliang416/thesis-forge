# Tasks: docforge-workbench-ui-redesign

## 1. Development Baseline

- [x] 1.1 Create and validate SpecNav requirements, approved UI prototype, proposal, design, delta spec, and task baseline.
- [ ] 1.2 Record the development entry basis, prototype promotion map, scope, ownership, task graph, and acceptance freeze.

## 2. DocForge Product Command Surface

- [ ] 2.1 Update visible brand, generic document status copy, accessibility labels, template labels, preview labels, and output feedback.
- [ ] 2.2 Move Word template selection into the product command bar while preserving existing template IDs and callbacks.
- [ ] 2.3 Add or update focused ProductBar, StatusStrip, Preview, Outline, and output component tests.

## 3. Dual-Canvas Workbench Layout

- [ ] 3.1 Recompose WorkbenchShell into command/status, outline/editor/preview canvas, bottom diagnostics drawer, and narrow output status.
- [ ] 3.2 Rebuild frontend CSS to match the approved DocForge light editorial workshop while preserving resizers, focus states, and runtime states.
- [ ] 3.3 Preserve and validate mobile outline/editor/preview/diagnostics panel navigation and minimum-window behavior.

## 4. Regression And Visual Verification

- [ ] 4.1 Update unit and Playwright expectations affected by copy, DOM hierarchy, and responsive layout.
- [ ] 4.2 Run frontend lint, typecheck, unit tests, production build, browser E2E, and real HTTP E2E.
- [ ] 4.3 Capture 1440x1024 and mobile production screenshots, compare them with the approved reference, and complete `design-qa.md` with a passed result.

## 5. Desktop Packaging

- [ ] 5.1 Build the macOS desktop application with the existing release workflow.
- [ ] 5.2 Install the rebuilt application to `/Applications/ThesisForge.app` and verify the visible DocForge UI plus Microsoft Word preview path.
- [ ] 5.3 Complete SpecNav verification evidence and record remaining risks without modifying unrelated OpenSpec work.
