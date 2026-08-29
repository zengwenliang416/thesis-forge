# Failure Cases

### Missing Neutral Citation Style

The first comprehensive real DocForge build failed because
`docforge-standard` did not declare a citation style. The failure was retained
in `2026-08-29-initial-governed-baseline.json`; the neutral template now uses
`GB-T-7714-2025`, and the later snapshot records inspect, validate, and build
success.

### Missing Required Title Metadata

The first clean tarball import of ordinary Markdown without Front Matter failed
because the neutral template requires `metadata.title`. The importer now
deterministically reuses an explicit localized title, an existing Front Matter
title, the first real H1, or the Markdown filename. It does not rewrite source
bytes or invent academic metadata.

### Existing Project Near Neighbor

Requests to repair or merge into an existing DocForge project are intentionally
rejected. The output evaluation keeps this adjacent job visible so future
description or importer changes cannot silently expand into in-place mutation.

### Evidence Boundaries

- Provider-backed output evaluation: `missing evidence`.
- Real human blind review: `missing evidence`.
- Target-native permission enforcement: `missing evidence`.
- Real external-client telemetry: `missing evidence`.
- npm package-name availability and publisher authority: `missing evidence`.
