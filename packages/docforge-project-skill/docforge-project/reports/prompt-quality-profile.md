# Prompt Quality Profile

Skill: `docforge-project`
Relevance: `prompt-heavy`
Overall quality score: `90.0/100`

## Primary Task Family

**Execution operation**
- Matched keywords: workflow, execute, operate

## Complexity

- Band: `expert`
- Score: `11`
- Reason: multiple task families plus governance, evaluation, or expert-level constraints

## Need Model

- Explicit Need: Turn one ordinary Markdown document and its local resources into a new verified DocForge Project Format V1 directory.
- Implicit Need: The reusable skill needs a stable role, task, and output contract rather than a one-off prompt.
- Scenario: input_files: one UTF-8 Markdown source plus optional local image assets and one optional local BibTeX file; governed evaluations treat these as a file-backed fixture.
- User Level: infer from examples and standards; ask only if it changes output depth
- Success Standard: DocForge Project Format V1; schema docforge.project.v1; neutral general-document defaults; real docforge inspect and validate as completion oracles; deterministic atomic publication; cross-platform path safety; explicit Codex installation and rollback.

## RTF To Skill Mapping

- Role: Use an operator role with explicit boundaries, inputs, outputs, and failure handling.
- Task: Convert the job into ordered steps with validation checks and stop conditions.
- Format: Return a runbook-like handoff with commands, checks, owners, and next actions when relevant.

## Quality Matrix

### Completeness — 100/100
- Matched signals: input, output, example
- Repair: Name missing inputs, outputs, constraints, or success standards before deepening the package.

### Clarity — 90/100
- Matched signals: clear, specific
- Repair: Replace broad verbs with observable actions and define what done means.

### Consistency — 85/100
- Matched signals: boundary
- Repair: Check that role, task, format, exclusions, and examples do not contradict each other.

### Practicality — 95/100
- Matched signals: execute, use, workflow
- Repair: Add runnable steps, examples, or verification cues instead of abstract advice.

### Specificity — 80/100
- Matched signals: none
- Repair: Anchor wording in the user's audience, domain nouns, and target outcome.

## Matched Task Families

### Execution operation
- Score: `3`
- Keywords: workflow, execute, operate
- Role: Use an operator role with explicit boundaries, inputs, outputs, and failure handling.
- Task: Convert the job into ordered steps with validation checks and stop conditions.
- Format: Return a runbook-like handoff with commands, checks, owners, and next actions when relevant.

### Prompt engineering
- Score: `3`
- Keywords: prompt, role, format
- Role: Use a prompt engineer role only when role design materially improves execution.
- Task: Map Role, Task, and Format into skill behavior rather than copying a large prompt template.
- Format: Return a compact prompt contract plus tests, quality matrix, and usage notes.

### Creative generation
- Score: `2`
- Keywords: copy, content
- Role: Use a taste-aware creator role with clear audience, tone, and originality boundaries.
- Task: Generate variants, explain selection logic, and preserve the user's distinctive constraints.
- Format: Return options with rationale, selection criteria, and refinement paths.

### Teaching guidance
- Score: `1`
- Keywords: tutorial
- Role: Use a teacher role that adapts to learner level and avoids overloading the first pass.
- Task: Explain through progressive steps, examples, and visible success checks.
- Format: Return learner-facing sections, worked examples, checkpoints, and common mistakes.

## Self-Repair Checks

- Check explicit need, implicit need, scenario, user level, and success standard before deepening.
- Map Role, Task, and Format into skill behavior, not decorative prompt labels.
- Ask one focused clarification only when missing information changes the package boundary.
- Add tests or examples for prompt-heavy behavior before treating it as reusable.
- Keep prompt methodology in references and reports instead of bloating SKILL.md.

## Reviewer Note

Use this profile when the package depends on prompt behavior, role design, output contracts, or conversation quality.
