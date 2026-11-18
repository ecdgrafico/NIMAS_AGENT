---
name: nimas-semantic-review
description: Review a NIMAS/DTBook package against its editorial PDFs, proposing structural and semantic XML, OPF, and resource corrections before making any edits.
---

# NIMAS Semantic Review

Use this skill for a NIMAS package containing DTBook XML, an OPF manifest, image assets, and editorial PDFs. Its primary outcome is an approval-ready review; do not modify package files unless the user explicitly approves a proposed change set.

## Non-negotiable release gates

- Never apply book-wide transformations merely because one lesson was approved. First produce a per-page map for every target lesson and use the PDF as the ordering authority.
- Do not use a global image substitution, page-range heuristic, or automatic level wrapping as a delivery transformation. Those may create a proposal only.
- Before editing a lesson, preserve a page map recording PDF page, XML `pagenum`, XML block range, image files, proposed structure, and reviewer status.
- Do not package or label an output as corrected when a page anchor is missing, page anchors are out of order, an image filename page disagrees with its preceding `pagenum`, a DTD validator has an error, or required review approval is absent.
- Run `nimas-agent/audit_package.py` against the candidate package after every material correction. Treat a nonzero result as a hard stop, not a warning.
- Validate with the project catalog before release: `XML_CATALOG_FILES="file:///Users/ecorrea/Altavista%20Editores%20Dropbox/Esteban%20Correa/PHE27_NIMAS/nimas-agent/catalog.xml" xmllint --noout --valid PACKAGE.xml`. A well-formed-only check is insufficient.
- Package only through `nimas-agent/package_if_valid.py` after the audit result is `pass` and the external NIMAS validator CSV has no errors.
- If a PDF page cannot be matched confidently, leave the package unchanged and put the page in the review queue. Do not invent XML structure to force completion.

## Package roles

- Treat the `*_original` package as the source package to correct. Preserve it unmodified until an approved output package is created.
- When a working package with extracted images is present, use it as an image-source inventory and provenance record; do not use its XML hierarchy as authority.
- Treat the corresponding editorial PDF page as the authority for visual order, printed text, hierarchy, activity boundaries, and whether material is substantive. The PDF is not authority for machine-readable structure.
- Keep all `<img>` `alt` attributes empty unless the user supplies a different accessibility policy. Do not invent alt text or other textual content that is absent from the editorial PDF.

## Review sequence

1. Inventory original XML/OPF/assets, extracted replacement images, and PDFs. Record counts, image dimensions/DPI, and all asset/manifest discrepancies.
2. Check well-formedness before semantic assessment. Report XML parse errors precisely; do not use a parser's recovery output as evidence of semantic structure.
3. Compare each PDF page to its XML location. Propose the reading order and DTBook hierarchy, distinguishing lesson titles, content-section titles, activity labels/instructions, tables, lists, answer choices, and decorative or repeated material.
4. Match extracted replacement images to their PDF page and visual position. Replace the original image reference only when the match is supported by page number, visual content, and reading order. Add each replacement image to XML and the OPF manifest with a unique ID; remove superseded original image files and their manifest entries only in an approved output package.
5. Validate resource integrity: XML image references must resolve to files and corresponding OPF manifest items; flag duplicate IDs, unreferenced images, and lower-resolution original assets separately.
6. Check NIMAS/DTBook validity only after XML is well formed. Then check OPF package structure and manifest/spine consistency.
7. Deliver a report with (a) blocking structural defects, (b) semantic proposals, (c) resource/OPF findings, (d) repeated conversion patterns suitable for app fixes, and (e) an explicitly scoped change proposal. Await approval before editing.

Analyze `FM` (frontmatter) and `EM` (end matter) with the same rigor as lessons. Detect them from the editorial PDF filenames and page sequences, map their extracted images to `images/FM` and `images/EM`, and report every missing 300-DPI image or resource-path discrepancy before proposing XML/OPF changes.

## Semantic rules

- Start each lesson at `level1` with its lesson heading as `h1`. A page boundary (`pagenum`) never starts a new logical lesson by itself.
- Use a lower level and its matching heading for a named instructional topic or distinct content section. Keep instructional prose in `p`, not headings.
- Treat a lettered activity (A, B, C, etc.) as `level3` with a matching `h3` when it has its own instruction and associated exercise content. Preserve the printed label and punctuation at the start of the heading, for example `A. Listen...`. Keep a continued activity in its original `level3` across page boundaries; do not create a level from a page break. Leave a letter as ordinary text only when it is decorative or does not introduce an independent activity.
- Mark a bounded word bank, reminder, or supplementary instructional box as `<sidebar render="required">`. Use `hd` for its printed label and a list for discrete choices. For example, “Letters to Use” becomes a sidebar with `hd` and a list of its letters; do not reduce such content to a generic paragraph.
- Preserve worksheet response blanks and option groupings. Use lists for genuine sequences/options and tables only when row/column relationships are meaningful.
- Mark each writable answer position with `<span class="WOL">`. Where the PDF visibly prints an underscore response line, retain those underscores inside the span as the visual fallback. When an example prints a letter, word, or expression on the answer line, place that existing content inside the same `WOL` span. Keep the surrounding word fragments outside it so the response position is unambiguous.
- Do not represent a final editorially blank page with a raster image, an empty `imggroup`, or a stand-alone `pagenum`, unless the user explicitly requires complete blank-page pagination.
- Exclude recurrent page furniture such as name/date fields, lesson folios, copyright notices, and printer marks unless the user asks to retain them.
- Never infer a semantic structure from source XML order when it conflicts with the PDF's intended reading order; report the discrepancy and propose the correction.
- Do not normalize, correct, paraphrase, complete, or add visible text. If the PDF cannot be read unambiguously, preserve the source text when available and flag the location instead of inventing content.

## Lesson calibration

Before applying hierarchy patterns book-wide, create a page-by-page proposal for one complete representative lesson and request review. Store the approved map with the project or skill and apply only its generalizable decisions.

## Reporting standards

For each proposed change, identify the PDF page, current XML location, issue type, proposed DTBook construct, confidence, and whether the change is mechanical or needs editorial approval. Group repeated faults into a concise app-improvement backlog; do not mistake a one-off editorial choice for a general conversion rule.

## Serialization

Deliver NIMAS/DTBook XML with readable line breaks, but align every element to the left margin: no leading spaces and no tab characters. Formatting whitespace must remain outside text content and must not alter the reading order.
