# Output Review Adjudication

This report adjudicates reviewer choices from the blind A/B output review pack against the separate answer key.

- Pairs: `6`
- Judgments: `0`
- Pending: `6`
- Agreement rate: `n/a`
- Invalid decisions: `0`
- Answer keys revealed: `0`
- Pending/invalid answers hidden: `6`
- Reviewer checklist: `0` ready / `6` total
- Reviewer metadata present: `false`
- Blind review attested: `false`
- Raw content excluded: `true`
- Ready for human evidence: `false`

No reviewer decisions recorded yet.

Generate a template with `--write-template`, fill `winner_variant` with `A` or `B`, then rerun adjudication.
Expected winners stay hidden until a valid reviewer decision is recorded.

## Case Adjudication

| Case | Reviewer | Expected | Status | Confidence | Reason |
| --- | --- | --- | --- | ---: | --- |
| minimal-project | pending | hidden | pending |  |  |
| full-format-local-resources | pending | hidden | pending |  |  |
| missing-image | pending | hidden | pending |  |  |
| remote-image | pending | hidden | pending |  |  |
| existing-destination | pending | hidden | pending |  |  |
| existing-project-repair-near-neighbor | pending | hidden | pending |  |  |

## Reviewer Checklist

| Case | Readiness | Answer key | Decision file |
| --- | --- | --- | --- |
| `minimal-project` | `awaiting-decision` | `hidden` | `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json` |
| `full-format-local-resources` | `awaiting-decision` | `hidden` | `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json` |
| `missing-image` | `awaiting-decision` | `hidden` | `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json` |
| `remote-image` | `awaiting-decision` | `hidden` | `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json` |
| `existing-destination` | `awaiting-decision` | `hidden` | `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json` |
| `existing-project-repair-near-neighbor` | `awaiting-decision` | `hidden` | `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json` |

### minimal-project

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_blind_review_pack.json`
- decisions: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit --self`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication --self`
- adjudicate: `python3 scripts/yao.py output-review --self`
- refresh_review_studio: `python3 scripts/yao.py review-studio . --self`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### full-format-local-resources

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_blind_review_pack.json`
- decisions: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit --self`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication --self`
- adjudicate: `python3 scripts/yao.py output-review --self`
- refresh_review_studio: `python3 scripts/yao.py review-studio . --self`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### missing-image

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_blind_review_pack.json`
- decisions: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit --self`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication --self`
- adjudicate: `python3 scripts/yao.py output-review --self`
- refresh_review_studio: `python3 scripts/yao.py review-studio . --self`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### remote-image

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_blind_review_pack.json`
- decisions: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit --self`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication --self`
- adjudicate: `python3 scripts/yao.py output-review --self`
- refresh_review_studio: `python3 scripts/yao.py review-studio . --self`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### existing-destination

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_blind_review_pack.json`
- decisions: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit --self`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication --self`
- adjudicate: `python3 scripts/yao.py output-review --self`
- refresh_review_studio: `python3 scripts/yao.py review-studio . --self`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### existing-project-repair-near-neighbor

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_blind_review_pack.json`
- decisions: `/Volumes/zwl/open_sources/thesis-forge/packages/docforge-project-skill/docforge-project/reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit --self`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- import_decisions: `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication --self`
- adjudicate: `python3 scripts/yao.py output-review --self`
- refresh_review_studio: `python3 scripts/yao.py review-studio . --self`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Required rationale; do not reveal baseline or with-skill labels before adjudication.
- reviewer: Human reviewer name or review group at the decision-file top level.
- reviewed_at: Review date or timestamp at the decision-file top level.
- reviewer_attestation.blind_review_completed_before_answer_key: True only after the reviewer has completed choices before opening the answer key.
- reviewer_attestation.answer_key_not_opened_before_decisions: True only when the answer key was not opened before decisions were recorded.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

## Next Fixes

- Keep the blind review pack separate from the answer key until decisions are recorded.
- Treat disagreement cases as prompts for rubric tuning or output improvement.
- Add model-executed holdout runs after this human adjudication harness is stable.
