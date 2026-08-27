# DocForge v1 Coverage Matrix

本矩阵把语料中的 source 结构映射到领域 IR、RenderPlan、Review、DOCX 和
聚焦验收测试。测试文件为
`tests/acceptance/test_v2_format_corpus.py`。

| Coverage item | Source evidence | Domain IR | RenderPlan | Review | DOCX/OpenXML | Test evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Project entry and metadata | `docforge.yaml` schema/project/metadata | `DocForgeProjectManifest`, `LoadedProject` | cover and section policy inputs | cover fields and source map | cover content, section geometry | `test_v2_format_corpus_cli_validate_is_clean`, DOCX test |
| Abstract and English abstract | `# 摘要 {#chap:abstract-zh}`, `# Abstract {#chap:abstract-en}` | `Heading`, `Paragraph` | semantic heading/body/keyword roles | reader-facing abstract blocks | semantic paragraph styles and manifest metadata | `test_v2_format_corpus_covers_render_plan_review_and_inline_semantics` |
| Main chapter, H2 and H3 | `chap:introduction`, `sec:*`, `sec:semantic-types` | typed headings with stable IDs | heading bookmarks, TOC entries | visible heading hierarchy | heading paragraphs and TOC/PAGEREF fields | plan kind/TOC assertions and DOCX fields |
| Acknowledgements and achievements | `chap:acknowledgements`, `chap:achievements` | semantic heading/body roles | `special.acknowledgements`, `special.achievements` | visible back-matter sections | semantic role-compatible paragraphs | heading role assertions and Review export assertions |
| Rich inline text | bold, italic, bold+italic, `` `inline-code` `` | `Strong`, `Emphasis`, `InlineCode`, `Text` | `TextRun` flags | styled `ReviewTextRun` | `w:b`, `w:i`, Courier New, `w:noProof` | inline run assertions and DOCX XML assertions |
| Links and breaks | HTTP link, mailto link, email autolink, ordinary/hard line breaks | `Link`, `SoftBreak`, `HardBreak` | `HyperlinkRun`, `SoftBreakRun`, `HardBreakRun` | visible link and break projection | hyperlink relationships, `w:br` | inline run assertions; DOCX package smoke path |
| Citations | locator citation plus article/book/conference citations | `Citation` and bibliography index | `CitationRun`, citation order, bibliography entries | formatted citation text without raw keys | citation text and bibliography paragraphs | three-key citation/bibliography assertions |
| Cross-references | chapter, section, figure, table, equation, listing, algorithm links | `CrossReference` | `ReferenceRun`, resolved bookmarks | visible labels without technical IDs | `REF` fields and bookmark pairs | target coverage assertion and field/bookmark checks |
| Ordered and nested unordered lists | ordered list starts at `3`; unordered list has three levels | `ListBlock`, list items with levels | `ListInstruction` and numbering metadata | readable list items | `w:numPr` list paragraphs | ordered start and level assertions |
| Figures and width overrides | two image figures; manifest `75%` and `90mm` | `Figure` with stable IDs | `FigureInstruction.resolved_width` percent/mm | figure labels and safe asset handles | two `w:drawing` objects and `wp:extent/@cx` | manifest unit assertions and extent calculation |
| Tables | aligned Markdown table and caption ID | `Table`, typed rows/cells | `TableInstruction`, caption sequence | aligned reader-facing table | three-line borders and `w:jc` cell alignment | table XML border/alignment assertions |
| Equations | loss, `E=mc^2`, frac+sum, pmatrix | `Equation` nodes | numbered `EquationInstruction` | equation labels and LaTeX | OMML objects and SEQ fields | formula IDs/count and OMML assertions |
| Ordinary code, listing, algorithm | plain fence plus typed listing/algorithm fences | `CodeBlock`, `Listing`, `Algorithm` | code/listing/algorithm instructions | code preserved as literal, markers hidden from normal text | Courier New preformatted paragraphs, bookmarks | Review fence isolation and DOCX code assertions |
| Blockquote | `>` paragraph with inline emphasis/code | `BlockQuote` with child blocks | recursive `BlockQuoteInstruction` | nested reader-facing children | left/right `w:ind` blockquote indentation | DOCX indent assertion |
| Footnote | `[^scope]` reference and definition | `FootnoteReference`, `FootnoteDefinition` | typed footnote reference/definition | footnote number and readable text | `word/footnotes.xml`, native references | footnote XML assertions |
| Review marker isolation | source IDs and raw citation markers only in source/code | stable IDs remain outside visible text | resolved labels instead of raw markers | no `{#...}`, `[@...]`, or technical IDs in normal text | captions/paragraphs contain visible labels only | `_review_markdown` marker assertions |
| Sections and page fields | template sections in manifest-selected school template | section policy in validation context | cover/front_matter/main breaks and TOC | generated section/page break blocks | `sectPr`, header/footer, PAGE/SECTIONPAGES/TOC/PAGEREF | DOCX fields, sections and header/footer assertions |
