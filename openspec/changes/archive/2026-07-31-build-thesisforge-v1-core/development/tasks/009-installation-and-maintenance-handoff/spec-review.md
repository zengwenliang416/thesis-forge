# Spec Review: 009-installation-and-maintenance-handoff

## Verdict

approved

The final checkout satisfies task `009-installation-and-maintenance-handoff`.
The reviewer independently reread the distribution verifier, focused
regression, package metadata, maintainer documentation, task packet, CodeGraph
evidence and validation logs, then reran the current maintainer gate.

The implemented contract is evidence-backed: temporary prefix installation,
`--no-index --no-deps --ignore-installed`, recursive PEP 508 marker-aware
runtime dependency copying, `python -S` console-script execution, explicit
parent/check-out path rejection, seven key-module provenance checks, blocked
sockets, bundled-template resolution and parent editable preservation.

## Missing Requirements

- None.
- Tasks `9.1` through `9.4` have direct implementation, command, review and
  handoff evidence.

## Extra Behavior

- The verifier copies the active recursive runtime dependency closure instead
  of depending on package-index resolution or parent site-packages.
- It rejects parent purelib/platlib, checkout `sys.path` and key module
  provenance escapes.
- The focused regression proves the parent interpreter's ThesisForge import
  path is unchanged before and after verification.

## Misunderstood Requirements

- None.
- Local installation and maintenance verification is not represented as public
  release approval; the no-license publication boundary remains explicit.

## Cannot Verify From Diff

- The reviewer freshly reran the complete gate on Python 3.14.4. Python 3.11.11
  and 3.12.9 are supported by system-executed validation-log evidence rather
  than fresh runs in the isolated reviewer session.
- Supported Office-client opening remains task-008 evidence; task 009 does not
  claim a new Office sensory run.

## Acceptance Assertions Verified

- `A1`: the reviewer reproduced offline installed-wheel `inspect`, `validate`
  and `build` with sockets blocked and provider/proxy variables removed.
- `A8`: the reviewer reproduced `124` tests, Ruff, pip check, wheel/sdist,
  hermetic distribution verification, strict OpenSpec and `git diff --check`;
  CodeGraph evidence `ev-ms8ykosi` is matched with no blockers.

## Required Fixes

- No implementation, test, documentation or evidence fix is required for task
  009. The final maintainer gate, hermetic distribution boundary, A1/A8
  evidence and development handoff artifacts satisfy the reviewed contract.
