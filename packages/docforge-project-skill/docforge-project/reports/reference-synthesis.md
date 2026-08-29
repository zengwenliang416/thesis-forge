# Reference Synthesis

Skill: `docforge-project`
- Description: Convert ordinary Markdown and local resources into a new, verified DocForge Project Format V1 directory. Use when creating an importable DocForge project; do not use for direct Markdown-to-Word conversion, thesis writing, translation, summaries, explanations, remote downloads, or editing an existing DocForge project.
- Intent confidence: `100/100` (`high`)

## Live GitHub Benchmarks

- No live GitHub benchmarks are attached yet.

## Curated World-Class Pattern Tracks

### Official skill anatomy and context discipline
- Type: `official`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: portable.
- Borrow: Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.
- Avoid: Do not let packaging or platform concerns swallow the core job boundary.

### Hypothesis-test-learn loop
- Type: `research`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: general fit.
- Borrow: Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
- Avoid: Do not create experimental overhead that exceeds the skill's real risk tier.

### Outcome-backwards design
- Type: `principles`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: output.
- Borrow: Borrow the habit of designing from the required hand-back output backwards.
- Avoid: Do not start with architecture terms before the deliverable is concrete.

## Borrow Now

- Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.
- Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
- Borrow the habit of designing from the required hand-back output backwards.
- Learn what quality, tone, workflow shape, or operating standard the user wants to preserve.

## Avoid Now

- Do not let packaging or platform concerns swallow the core job boundary.
- Do not create experimental overhead that exceeds the skill's real risk tier.
- Do not start with architecture terms before the deliverable is concrete.
- Do not copy wording, confidential material, or source-specific implementation details.

## Pattern Gate

- Summary: 3 accepted, 1 deferred using threshold 4/4.
- Acceptance threshold: `4/4`
- Accepted patterns:
  - **Official skill anatomy and context discipline**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **Outcome-backwards design**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **openspec/changes/docforge-project-skill/requirements.md**: 4/4 (recurrence, generativity, distinctiveness, boundary)
- Deferred patterns:
  - **Hypothesis-test-learn loop**: missing distinctiveness

## Default Recommendation

- Summary: Start by borrowing this pattern: Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts. Avoid this for the first pass: Do not let packaging or platform concerns swallow the core job boundary.
- Why: Intent is clear enough, so the system should make the first pattern call quietly.
- User decision required: `False`

## Visibility Mode

- Mode: `silent`
- User note: Apply the synthesis quietly unless uncertainty or a real design conflict appears.
- Reviewer note: Keep the full benchmark and synthesis evidence visible for authors and reviewers.

## Conflict Check

- No material design conflict detected. Keep the synthesis silent for the user.

## Quality Lift Thesis

- Use GitHub repositories for concrete package and workflow patterns.
- Use curated official or commercial tracks for entrypoint and operator ergonomics.
- Use research tracks to justify the smallest evaluation loop that still catches regressions.
- Use principle tracks to keep the package small, boundary-aware, and outcome-driven.

## Decision Prompt

Use the recommendation by default. Only surface the underlying benchmark tradeoffs when intent is uncertain or a real design conflict needs a deliberate call.
