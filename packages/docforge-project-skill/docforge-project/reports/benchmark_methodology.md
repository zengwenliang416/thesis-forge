# Benchmark Methodology

## Benchmark Types

The local benchmark combines deterministic trigger routing, assertion-based
output comparison, package contract tests, importer and installer unit tests,
real DocForge inspect/validate/build checks, cross-target conformance, trust
inspection, permission probes, package verification, install simulation, and
upgrade simulation.

## Sample Sources

Trigger samples cover positive, negative, and near-neighbor requests in Chinese
and English. Output samples are labeled `file-backed fixture` and cover a
minimal project, comprehensive formatting, missing and remote resources,
existing destinations, and existing-project repair.

## Evaluation Dimensions

- Correct new-project output contract.
- Supported Markdown semantic preservation.
- Non-overwrite and path-confinement safety.
- Offline behavior and no direct DOCX generation.
- Real DocForge inspect, validate, and optional build verification.
- Explicit installer update, backup, and rollback behavior.
- Routing precision, recall, boundary, and near-neighbor coverage.
- Package, target, trust, permission, registry, and upgrade integrity.

## Weighting Rule

Each output assertion has a positive numeric weight. A variant score is the
passed weight divided by total weight. Promotion requires the with-Skill pass
rate to exceed baseline, no regression, at least five cases, and explicit
boundary plus near-neighbor coverage.

## Failure Disclosure

Representative failures remain in `evals/failure-cases.md` and
`evals/history/`. A later passing snapshot supersedes only the named failed
surface; it does not delete the original failure. Missing provider, human,
native-client, telemetry, package-name, and publisher facts remain literal
`missing evidence`.

## Reproduction

Run the package checks and tests from `packages/docforge-project-skill/`, then
run Yao output, trigger, trust, conformance, permission, package, install, and
upgrade checks against `docforge-project/`. Run the repository Python tests and
Ruff from the repository root. The recorded output execution is fixture-backed
and must not be described as provider or model execution.
