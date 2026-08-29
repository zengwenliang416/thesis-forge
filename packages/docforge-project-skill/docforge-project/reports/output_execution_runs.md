# Output Execution Runs

This report records how output-eval variants were produced and whether timing or token evidence is observed or estimated.

- Cases: `6`
- Variant runs: `12`
- Command executed: `0`
- Model executed: `0`
- Recorded fixtures: `12`
- Timing observed: `0`
- Token observed: `0`
- Token estimated: `12`
- Delta: `100.0`
- Gate pass: `True`

No model-executed runs are recorded yet.

Use `python3 scripts/yao.py output-exec --provider-runner openai --self` or `--runner-command` with a reviewed provider-backed runner to replace recorded fixtures with real model output evidence.

## Runs

| Case | Variant | Mode | Model | Duration ms | Tokens | Score | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| minimal-project | baseline | recorded_fixture |  |  | 36 | 0.0 | pass |
| minimal-project | with_skill | recorded_fixture |  |  | 77 | 100.0 | pass |
| full-format-local-resources | baseline | recorded_fixture |  |  | 55 | 0.0 | pass |
| full-format-local-resources | with_skill | recorded_fixture |  |  | 93 | 100.0 | pass |
| missing-image | baseline | recorded_fixture |  |  | 40 | 0.0 | pass |
| missing-image | with_skill | recorded_fixture |  |  | 54 | 100.0 | pass |
| remote-image | baseline | recorded_fixture |  |  | 35 | 0.0 | pass |
| remote-image | with_skill | recorded_fixture |  |  | 50 | 100.0 | pass |
| existing-destination | baseline | recorded_fixture |  |  | 45 | 0.0 | pass |
| existing-destination | with_skill | recorded_fixture |  |  | 49 | 100.0 | pass |
| existing-project-repair-near-neighbor | baseline | recorded_fixture |  |  | 50 | 0.0 | pass |
| existing-project-repair-near-neighbor | with_skill | recorded_fixture |  |  | 76 | 100.0 | pass |

## Next Fixes

- Keep recorded fixtures as reproducible baselines, but do not describe them as model-executed evidence.
- Use `scripts/provider_output_eval_runner.py` for provider-backed holdout cases when release confidence depends on real generation behavior.
- Compare timing, token cost, and assertion deltas before promoting a skill to governed reuse.
