# Route Scorecard

Generated: 2026-08-29

## Result

- Cases: 16
- Precision: 1.0
- Recall: 1.0
- False positives: 0
- False negatives: 0
- Ambiguous cases: 0
- Threshold: 0.42

## Coverage

| Bucket | Passed | Total | Pass rate |
| --- | ---: | ---: | ---: |
| Should trigger | 5 | 5 | 1.0 |
| Should not trigger | 7 | 7 | 1.0 |
| Near neighbor | 4 | 4 | 1.0 |

The deterministic semantic trigger evaluator confirms that `docforge-project`
routes only requests that create a new DocForge project from Markdown and local
resources. Direct Markdown-to-Word, thesis generation, translation, summary,
explanation-only, remote-download, and existing-project repair requests remain
outside the Skill boundary.
