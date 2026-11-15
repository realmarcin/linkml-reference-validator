# Supplementary DOCX extraction must not invent contiguous text

Independent review of the local #1996 validator candidate found that its proposed
`docx-table-cells-v1` extractor joins all descendant `w:t` strings without
accounting for tabs, explicit breaks or paragraph boundaries. A source cell with
`OAE`, a structural separator, and `516` could therefore become `OAE516` and
falsely pass the unchanged substring matcher.

The finding applies to an unadopted local candidate, not to the existing article
matcher or a canonical CommunityMech record. The actual retained Switchgrass
Table S1 cells have independently verified single-text-node content, but the
general advertised extraction contract still needs correction before its canary.

Affected local candidate: `etl/source_locator.py` SHA
`e1b523f164fec415645fd124a4b73b9b1a658824206a38fa328164405101c1d4`,
based on linkml-reference-validator v0.2.1 commit
`ae3979a14b9c99cc681ab1731e20c9df580b567f`.

Acceptance: add real DOCX positive/refusal/restoration regressions for tabs,
breaks and paragraphs before changing the extractor. Preserve genuine adjacent
styled text runs without a separator. Explicitly bound hidden/deleted/revised
content rather than silently choosing a rendering. Either preserve documented
whitespace boundaries or fail closed for unsupported structures. Keep all
same-version article behavior, locator hard errors and source identities intact.
No upstream notification or runtime adoption is requested by this issue.

Related: https://github.com/CultureBotAI/CommunityMech/issues/1996

Filed as https://github.com/CultureBotAI/CommunityMech/issues/2930. The corrected
contract preserves explicit separators and refuses unsupported rendering.
Follow-up wording from independent rereview states *explicitly numbered*
paragraphs: document `numPr` is refused, while this bounded extractor does not
resolve inherited numbering styles. No general Word rendering is claimed.
