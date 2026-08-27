# Plan Index

## Summary

Task 005's quality review found five implementation defects in the active
template-profile slice: empty optional bindings leak into RenderPlan,
Validator retains thesis-shaped global defaults, localized title policy is
undefined, direct compilation can produce a partial required academic cover,
and binding metadata is duplicated across model, resolver, and presentation.
The plan repairs the shared binding foundation first, then locale resolution,
compiler enforcement, and Validator defaults. The generic distribution
verifier (QR-004) is intentionally excluded because another work item owns
that file.

## Issues (ordered by execution sequence)

| # | Issue | Priority | Depends On | Scope |
| --- | --- | --- | --- | --- |
| 001 | Centralize metadata binding descriptors and formatting policy | 1 | - | `model.py`, `bindings.py`, `presentation/metadata.py`, template binding tests |
| 002 | Define locale-aware localized metadata resolution | 2 | 001 | project model, binding resolver, generic template, template binding tests |
| 003 | Enforce required template bindings before RenderPlan construction | 3 | 001, 002 | compiler and compiler profile tests |
| 004 | Remove thesis-shaped global validator metadata defaults | 4 | 001, 002 | validator and validator tests |

## Dependency Graph

```text
001
└── 002
    ├── 003
    └── 004
```

## Risk Assessment

- Locale fallback can accidentally duplicate or relabel a bilingual title.
  Mitigation: resolve one effective localized group and assert exact binding
  paths/values for zh-only, en-only, and bilingual fixtures.
- Enforcing required bindings in the lower-level compiler may expose callers
  that previously relied on renderer filtering. Mitigation: preserve the
  existing application validation gate and add a direct compiler negative test.
- Centralizing descriptors can create an import cycle between presentation and
  templates. Mitigation: keep the registry in `templates.model` and make
  presentation depend only on the registry accessor.
- Existing C901 complexity findings in large compiler/validator orchestrators
  are inherited and are not part of this slice; do not refactor them while
  applying these focused changes.
- QR-004, the isolated generic-template clean-install verifier, is not in this
  plan because `scripts/verify_distribution.py` is owned by another work
  item.

## Estimated Scope

- Total issues: 4
- Total implementation files affected across issues: 9 unique files
- New implementation files: 0
- New plan files: 5
