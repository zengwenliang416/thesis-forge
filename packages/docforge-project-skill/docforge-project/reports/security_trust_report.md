# Security Trust Report

- OK: `True`
- Scanned files: `23`
- Scripts: `1`
- Internal script modules: `0`
- Secret findings: `0`
- Network-capable scripts: `0`
- Network policy covered scripts: `0`
- Network policy missing scripts: `0`
- File-write scripts: `0`
- Permission approvals: `1 / 1`
- Permission approval gaps: `0`
- CLI help smoke checked: `1`
- CLI help smoke failures: `0`
- Interactive scripts: `0`
- Package hash scope: `source-contract-without-generated-reports`
- Package hash files: `23`
- Package SHA256: `9f99e3b37b1266b45dc3009f4a7d5833aff004c0d1635a311dde63e094ea7972`

## Failures

- None

## Warnings

- No dependency or lock file detected

## Dependency Evidence

- Files: `none`
- Pinned entries: `0`
- Unpinned entries: `0`

## Network Policy

- Policy file: `security/network_policy.json`
- Present: `True`
- Covered scripts: `0`
- Missing scripts: `none`
- Mismatches: `0`

## Permission Governance

- Policy file: `security/permission_policy.json`
- Present: `True`
- Required capabilities: `subprocess`
- Approved capabilities: `subprocess`
- Missing approvals: `none`
- Invalid approvals: `none`
- Expired approvals: `none`

## CLI Help Smoke

- Enabled: `True`
- Timeout seconds: `5.0`
- Checked scripts: `1`
- Passed scripts: `1`
- Failed scripts: `none`

## Script Surface

| Script | Interface | Declared | Argparse | Main Guard | Input | Network | File Write | Subprocess | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scripts/docforge_project.py | cli | True | True | True | False | False | False | True | Stable Agent Skill entrypoint delegating to the shared Node importer. |
