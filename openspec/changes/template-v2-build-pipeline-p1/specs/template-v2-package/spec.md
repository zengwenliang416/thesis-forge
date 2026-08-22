## ADDED Requirements

### Requirement: Expose a pure package-to-compilation mapping
The template package v2 module SHALL expose the resolved-package to compilation-template mapping as a public pure function reused by the build services, and the mapping SHALL NOT import DOCX/OOXML implementation details.

#### Scenario: Services reuse the package mapping
- **WHEN** application services resolve a v2 template source
- **THEN** they obtain the compilation template through the shared package mapping function instead of a duplicated implementation

### Requirement: Carry shell and reference assets through resolution
Resolution of a v2 template source SHALL carry the package shell and reference asset paths alongside the mapped compilation template so the build service can merge into the shell when present, while `reference.docx` stays a lint/validation asset and never becomes the renderer base document.

#### Scenario: Shell asset reaches the build service
- **WHEN** a loaded package contains `shell.docx`
- **THEN** the resolution context exposes the shell path to the build service for anchor merging

#### Scenario: Reference asset does not alter the product
- **WHEN** a package contains `reference.docx`
- **THEN** it is used for package lint/validation only and the rendered artifact's base document is unchanged
