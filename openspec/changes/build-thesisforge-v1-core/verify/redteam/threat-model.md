# Redteam Threat Model

## Assets

- Local Markdown, YAML, BibTeX, and image inputs
- Previously valid DOCX output
- Output-directory integrity
- DOCX ZIP/package semantics
- Offline and no-AI execution boundary
- Prototype review-state and permission signaling

## Trust Boundaries

- Untrusted document and template text entering Parser and Validator
- Untrusted local resource paths entering image and bibliography loaders
- Compiler instructions entering DOCX Renderer
- Renderer output entering package validation and atomic replacement
- Static prototype controls entering state and build simulations

## Threats

- Path traversal or symlink escape outside the document root
- Malformed Markdown, YAML, BibTeX, LaTeX, image, XML, or ZIP input
- Duplicate ZIP parts, CRC corruption, missing relationships, or wrong package semantics
- Partial build replacing a valid output
- Temporary-file leakage after failure
- Oversized input causing unbounded failure or network fallback
- Hidden network or AI dependency in core commands
- Mobile overflow, disabled-state bypass, or permission-state confusion

## Safety Constraints

- Probes use temporary local files and synthetic fixtures only.
- No real user data, credentials, remote services, or destructive external operations are used.
- Expected failure must be concise, stage-specific, and traceback-free where exposed through CLI.
- Previously valid output bytes must remain unchanged on every failed rebuild path.
