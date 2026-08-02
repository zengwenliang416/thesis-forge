# Unit Coverage Notes

- Python tests cover application services, adapters, filesystem semantics, controller states, presentation mapping, package/distribution verification, architecture, and the deterministic compiler.
- Vitest covers reducers, components, diagnostics, preview DTOs, transports, progress, cancellation, and stale-result suppression.
- Rust tests cover protocol envelopes, native source boundaries, WebView2 acceptance configuration, and the explicit Windows picker seam.
- Playwright is reported in E2E but contributes behavior coverage for responsive and accessibility states.
- Line coverage percentage is not collected; sufficiency is judged by A1-A12 behavior mapping, hostile paths, and direct native evidence.
