# Select a retained supplementary table cell

This additive contract addresses CommunityMech issue 1996. It is implemented
on the 0.2.1 runtime so its existing article matcher, normalization and literal
bracket policy remain unchanged. It does not infer scientific support.

An omitted `source_locator` keeps the existing article-only lookup. A present
locator, including an invalid or null value, never falls back to the article,
another supplementary file, a skipped prefix or a network fetch.

```yaml
reference: PMID:36472419
snippet: OAE516
source_locator:
  kind: supplement
  asset_id: msystems.00951-22-s0006.docx
  version: published
  table: 1
  row: 12
  cell: 2
```

The schema must declare the optional, inlined `source_locator` attribute on
each evidence class that supports it. Its object has exactly the six fields
above; `table`, `row` and `cell` are positive integers, not strings or booleans.
`reference` keeps its existing authoritative-reference annotation and the
excerpt keeps its existing annotation. A locator does not supply a citation.
There must be exactly one usable reference and nonempty text excerpts on the
selected evidence object. Existing `evidence_source` values remain descriptive
and have no effect on routing.

Configure `source_catalog` as an explicit path in the normal validator config.
A relative catalog path is relative to the invocation's working directory.
The catalog is JSON with this closed structure:

```json
{
  "version": 1,
  "sources": [{
    "reference": "PMID:36472419",
    "asset_id": "msystems.00951-22-s0006.docx",
    "version": "published",
    "asset_path": "assets/s0006.docx",
    "asset_sha256": "<64 lowercase hexadecimal characters>",
    "extraction_path": "extractions/s0006.json",
    "extraction_sha256": "<64 lowercase hexadecimal characters>"
  }]
}
```

Catalog entries may also carry `reference_title`; it is required to match when
the evidence supplies an expected title. Duplicate JSON keys, duplicate
normalized parent/asset/version identities, unknown fields, unknown versions,
missing files and wrong digests are hard errors. Asset and extraction paths
must be normalized relative paths inside the catalog directory. Neither paths
nor any ancestor may be a symlink. Catalog, asset and extraction files are
bounded to 20 MiB each, as is the uncompressed DOCX document XML.

The catalog is a reviewed provenance assertion. Hashes detect changes relative
to that assertion; they do not independently authenticate publisher identity
or authorize redistribution. Preserve acquisition URL, access limits and the
original source in the owning repository's evidence record. Validation neither
acquires sources nor writes or publishes them.

## Mechanical indexing and extraction

`extract_docx_tables(raw_bytes)` in `etl/source_locator.py` produces:

```json
{
  "format": "docx-table-cells-v2",
  "asset_sha256": "<digest of the actual DOCX bytes>",
  "tables": [[
    [{"status": "supported", "text": "Genus"}, {"status": "supported", "text": "Strain"}],
    [{"status": "unsupported", "reason": "unsupported_cell_rendering"},
     {"status": "supported", "text": "OAE516"}]
  ]]
}
```

The arrays are positional. Tables are the top-level `w:tbl` children of
`w:body`; rows are each table's direct `w:tr` children; cells are each row's
direct `w:tc` children. All positions are **one-based and include headers**.
The sample projection therefore places `OAE516` at table 1, row 2, cell 2.
This synthetic position is not the real Table S1 position shown above.

Each simple paragraph preserves the order of its runs. Adjacent styled runs
are joined without an invented space. An explicit `w:tab` becomes a tab;
`w:br`, `w:cr` and paragraph boundaries become newlines. The native matcher
then normalizes whitespace normally, so `OAE` + a boundary + `516` cannot
become the contiguous token `OAE516`. No neighboring cells are joined.

Unsupported run/paragraph rendering marks the **entire cell** unsupported,
with that one fixed reason code and no partial text. Its position remains in
the array. Simple hyperlinks are traversed as displayed text; fields, symbols,
drawings and content controls (including placeholder-bearing controls) are
not rendered. Selecting an unsupported cell always fails before the matcher.
The complete projection, including every marker, must replay exactly; a
rehashed replacement of a marker with fabricated supported text is refused.

Hidden text markers (including any hidden style in `word/styles.xml`), tracked
insertions/deletions/moves and explicitly numbered paragraphs still refuse
the whole asset. Malformed archives/XML, nested/non-body tables, merged cells,
ambiguous row/cell alignment, DTDs and duplicate ZIP members also refuse the
whole asset. They cannot become opaque-cell markers. This is a bounded text
extractor, not a general Word renderer. Multi-cell ranges and other formats
require an explicit future contract. The earlier unadopted v1 projection is
not accepted by this v2 reader.

These separator and rendering constraints address the independent review
finding [CommunityMech #2930](https://github.com/CultureBotAI/CommunityMech/issues/2930).

The runtime captures each file once, hashes and parses those same bytes, and
regenerates the entire projection from the captured DOCX. Merely rewriting an
extraction hash cannot admit fabricated cell text. It then applies the native
matcher to only the selected nonblank cell. Before returning a result it
rechecks all captured files for drift. This is a cooperative filesystem guard,
not a transaction against a hostile concurrent filesystem writer.

## Results and coverage

`ValidationResult.source_identity` contains the normalized parent reference,
asset ID/version, asset/extraction/catalog digests, extractor contract, full
locator and selected-cell text digest. Source-specific reads do not use the
article's memory or disk cache and are recaptured on every comparison.

The normal `validate data` CLI prints one `Source selection:` JSON observation
for each explicit-source comparison, including its record field, outcome and
identity. Missing/unestablished identities are reported as failures, not
successful comparisons. The preexisting issue counter is not a denominator;
whole-record assertion coverage still requires measuring actual comparisons.

Tests use actual synthetic DOCX bytes, the real plugin and native CLI. They
exercise positive → input mutation → refusal → restoration, including warning
severity/skip-prefix settings, wrong parent/asset/cell, a rehashed fabricated
projection, same-PMID asset separation and drift after matching. No provider
is called. A real Switchgrass scratch canary and downstream schema adoption
remain separate steps; this runtime change alone does not repair any record.
