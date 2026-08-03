## ADDED Requirements

### Requirement: Resolve semantic thesis section roles
The Compiler SHALL derive renderer-neutral semantic roles for abstract titles and bodies,
keywords, table-of-contents headings, bibliography headings and entries, acknowledgements and
other special headings from stable document IDs and structure without adding Word implementation
details to the Parser or Domain Model.

#### Scenario: Chinese abstract role
- **WHEN** a level-one heading has the stable ID `chap:abstract-zh` and is followed by paragraphs
- **THEN** the compiled heading and following abstract paragraphs identify the Chinese abstract title and body roles

#### Scenario: English keywords role
- **WHEN** an English abstract contains a recognized keywords paragraph after `chap:abstract-en`
- **THEN** the compiled paragraph identifies the English keywords role while preserving its original text

#### Scenario: Ordinary body remains ordinary
- **WHEN** a paragraph appears under a numbered main-matter chapter without a special semantic marker
- **THEN** the compiled paragraph retains the normal body role

### Requirement: Preserve Markdown compatibility
The semantic role resolution SHALL use existing stable IDs, headings and paragraph content
contracts and MUST NOT require new mandatory Markdown syntax for existing thesis sources.

#### Scenario: Existing complete thesis
- **WHEN** an existing valid thesis source is compiled with a legacy template
- **THEN** parsing succeeds without source changes and unsupported semantic roles fall back to existing body or heading behavior
