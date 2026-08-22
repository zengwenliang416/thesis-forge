## ADDED Requirements

### Requirement: Auto-detect template package sources
The template selection surface SHALL classify an explicit template path as a v0.3 single YAML file, a v2 package directory (containing `template.yaml` with `schema_version: 2`), a `.tftpl` archive, or an invalid source, and CLI and application services SHALL share one classifier.

#### Scenario: v0.3 single YAML stays unchanged
- **WHEN** the template path points to a `.yaml`/`.yml` file
- **THEN** resolution follows the existing v0.3 path with unchanged behavior

#### Scenario: v2 directory and archive are accepted
- **WHEN** the template path points to a v2 package directory or a `.tftpl` file
- **THEN** the source is resolved as a v2 package and compilation consumes the mapped template

#### Scenario: Malformed source is rejected
- **WHEN** the path is a directory without a valid v2 `template.yaml` or another unsupported shape
- **THEN** a structured diagnostic (severity/code/target) is emitted and no build output is produced

### Requirement: Map resolved package data to the compilation template
The v2 package adapter SHALL expose a pure, deterministic function that maps the inheritance-merged resolved data of a loaded package to the shared compilation template model, without depending on DOCX/OOXML implementation details.

#### Scenario: Round trip with migrate
- **WHEN** a v0.3 template is migrated to a v2 package and mapped back
- **THEN** the result is semantically equivalent to the original v0.3 template at field level

#### Scenario: Missing required data fails structurally
- **WHEN** resolved data lacks a field required by the compilation model
- **THEN** a structured template-mapping error is reported instead of silent defaulting

### Requirement: Enforce package gates before compilation
A v2 template source SHALL pass L1+L2 package lint and, for `.tftpl`, archive unpack protection with manifest sha256 reconciliation before compilation starts; gate failures SHALL stop the build with structured diagnostics and no output artifact.

#### Scenario: Lint gate failure stops the build
- **WHEN** the package has L1 or L2 lint errors
- **THEN** the build stops with a structured diagnostic and produces no output file

#### Scenario: Hostile archive is rejected
- **WHEN** a `.tftpl` contains Zip Slip paths, a decompression bomb, or a manifest mismatch
- **THEN** unpacking is refused with a structured diagnostic and the temporary directory is cleaned up

### Requirement: Merge rendered output into the package shell
When the resolved package carries a `shell.docx`, the build SHALL merge the rendered document into the shell anchors after rendering and before finalization, requiring the `tf_body` anchor and treating `tf_toc`/`tf_bibliography` as optional; the merged artifact SHALL continue through the existing finalization chain (field refresh, structural validation, atomic publish).

#### Scenario: Shell merge preserves school structure
- **WHEN** a package with `shell.docx` and a valid `tf_body` anchor is built
- **THEN** the published artifact keeps the shell cover/declaration/TOC structure with rendered content merged at the anchors and passes structural OOXML validation

#### Scenario: Missing body anchor fails the build
- **WHEN** the shell lacks the required `tf_body` anchor
- **THEN** the build fails with a structured missing-body-anchor diagnostic and no output is published

### Requirement: Keep no-shell builds deterministic and v0.3-equivalent
A v2 package without `shell.docx` SHALL degrade to normal rendering without error, produce output semantically equivalent to the same template consumed as v0.3, and produce byte-identical output across repeated builds of the same input.

#### Scenario: Repeated no-shell builds are byte-identical
- **WHEN** the same project and v2 package are built twice
- **THEN** the two output files are byte-identical
