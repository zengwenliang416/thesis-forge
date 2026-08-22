# Prototype Question: v2-rich-inline-renderplan-p1

## Question

Does the `a1m-renderplan-typed-inline-seam-v1` component-seam variant provide
an acceptable production boundary for the four capability-registered typed
inline runs, with downstream consumers intentionally deferred to ordered child
changes?

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Required reviewer decision: approve the exact run names, semantic fields,
  single-union boundary, explicit unknown-run failure, and renderer-neutral
  dependency direction.

## Out of Scope

- Production implementation.
- Parser or domain Inline changes.
- Figure caption ownership and downstream Preview, Review, compiler, or DOCX
  consumers.
- Database writes, deployment behavior, and UI changes.
