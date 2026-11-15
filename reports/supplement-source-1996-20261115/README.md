# Explicit supplementary-source routing: installed candidate evidence

The isolated candidate resolves the two retained Switchgrass quotation
mismatches by selecting exact supplementary table cells. Its real native CLI
run compared all 37 unchanged snippets and matched all 37. Three comparisons
carry complete source identities. This is a scratch-record routing result,
not a canonical record repair, scientific review or downstream adoption.

The implementation starts from v0.2.1 at
`ae3979a14b9c99cc681ab1731e20c9df580b567f`. Article-only lookup, matching,
normalization and bracket handling retain that version's behavior. Explicit
locators never fall back to an article or another source. The closed contract
and its bounded DOCX rendering rules are documented in
[the source-locator guide](../../docs/how-to/supplement-source-locators.md).
An optional downstream schema field may allow null structurally; this runtime
always refuses an explicitly present null locator before matching.

Publication is to the user-owned `realmarcin/linkml-reference-validator` fork,
against a dedicated base branch pinned to that tested revision. Current
upstream/fork main `6ccc05bdb1ccb160e247dea7bb975759f4c3aef7` contains substantial
later matching, acquisition and inheritance changes. This patch has not been
rebased onto or verified with that later runtime; no upstream PR, review or
issue notification is part of this work.

## Installed artifact and real retained source

The explicit wheel SHA256 is
`83674019192a1b6fb81ccd75654c27dc319ad8f66cb8a94fdc8661e37d070efc`.
It was installed noneditably into the fresh private `candidate-env-003`, with
copied dependencies. The corrected distribution verifier confirms exact
membership and bytes for all 49 package Python files across source, wheel
and installation, and rechecks membership and bytes before reporting.
Its verification does not inventory non-Python package data or authenticate
dependencies beyond the retained frozen lock and environment observations.
The actual canary used Python 3.13.12, LinkML 1.9.5 and linkml-runtime 1.9.5.
CommunityMech's separately inspected environment uses LinkML 1.9.3 and runtime
1.9.5. Any adoption must repeat the canary in its exact resolved environment.
The project's dynamic Git version may change built distribution metadata after
publication; the trial wheel is identified by its exact digest, not version
text alone.

The retained DOCX is `msystems.00951-22-s0006.docx`, SHA256
`5bfa02fdb94538e9405fb0ec7d7b0dad338791a5ca0b4b651589f33148c8e0e7`.
The earlier acquisition URL and receipt remain bound; no new download was
needed. The candidate mechanically reproduced the complete
`docx-table-cells-v2` projection, SHA256
`c322c14c7e754df924e3e3151fb3d8e18564537dd0448e43d9a856d4e3ef32a5`.
Unsupported content controls remain opaque cells without partial text. They
do not prevent selection of a supported neighboring cell or change coordinates.

The three locators select table 1, row 12, cell 2 (`OAE516`); row 18, cell 1
(`Bacillus`); and row 18, cell 2 (`OAE603`). All positions include headers.
Each result binds the parent PMID, asset ID/version, asset and extraction
digests, catalog digest, complete locator and selected-text digest. No study
stock identity or mechanism is inferred from these lexical matches.

The original CommunityMech record SHA256 remains
`bb31b1df4a9be2241453528101fc5d55657c23eccf1d58ce1cc9639e5912b368`.
The scratch selected record differs only by the three locators. All 37
snippet texts and citation surfaces were independently enumerated and compared
with the native calls. All original source bytes remained unchanged.

## Real canary and sequential controls

All runs used the same recorder, installed environment and native CLI helper.
Preparation and execution plans passed before actual execution. The selected
canary's persisted log, exit and receipt were verified before the controls.
The observer records actual native returns without replacing the matcher,
provider or traversal. A socket guard refused any attempted network access;
none was attempted. Native `Total checks: 0` is the preexisting issue counter,
not the assertion denominator used below.

| Run | Calls | Comparisons | Matches | Mismatches | Source failures | Native exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Selected canary | 37 | 37 | 37 | 0 | 0 | 0 |
| Original article-only | 37 | 37 | 35 | 2 | 0 | 1 |
| Wrong selected cell | 37 | 37 | 36 | 1 | 0 | 1 |
| Wrong parent | 37 | 36 | 36 | 0 | 1 | 1 |
| Restored selection | 37 | 37 | 37 | 0 | 0 | 0 |

The wrong-cell control selects a cell that does not contain `Bacillus`, even
though that word occurs in the article. Its failure verifies no article
fallback. The wrong-parent failure is a hard source-selection error before
matching, so it is not counted as a quotation comparison. Each control
asserts the exact failing field and the complete expected source identities.

Full receipts remain in the durable private namespace
`.temp/supplement-source-1996-20261115/switchgrass-<run>-003/receipt.json`:

| Run directory | Receipt SHA256 |
| --- | --- |
| `selected` | `e911410ac55cda792b4b5e5d56df093e5b8c7e042398f1e467467aa571d863e3` |
| `article-only` | `67b6eaef79e7178ae599a3ee5721e547962d51c8e3f7a980dabac30d2a9ab13e` |
| `wrong-cell` | `373281f47430d242b598fc90a92227279e7acde5f2fa8df7fb8fce46bfbd5f42` |
| `wrong-parent` | `cfab3c608ad415e40dff2fb0dba6a97502ab80a54a6c509d82b6122c3b912051` |
| `restored` | `980c89639e74c0c9850a616067f8535e977a845a9554316bde3eead1310f5a55` |

The preparation receipt is `switchgrass-prepared-003/preparation.json`, SHA256
`d57008daae2939573b5b647b8c4f575fe861a339cd4cb0c221fdcfa7314e02b2`.
The selected native log SHA256 is
`67f82fc6201fa9d1b101d413f1d4f849da8ea769c0a62d5c2c9b06bf83285bec`.
Primary assets and record text are not redistributed in this change.

## Verification and retained findings

The final focused runtime/plugin/article controls passed: 257 tests, with
12 existing warnings, in 5.55 seconds. The retained recorder log
`supplement-runtime-focused-final-001.log` has SHA256
`6be442835da95d596fa39f551041e6afd7d7146c1fdff3e423b98f5a9e3e1b73`.
Separate final native `just mypy format` passed 89 source files and Ruff;
`supplement-native-quality-final-001.log` has SHA256
`27579812a7ee6b76c2aa6710e9e32a2b7625ef143cbc49d74c92151773b5bf74`.
This is not a full native-suite pass. The final native `just test` run004
collected 733 tests under OS-level network denial. It encountered the inherited
live ClinicalTrials test failure and was explicitly interrupted during further
slow provider retries (tool exit130). Its partial log SHA256 is
`50836a563fa3e8acdfbf27c45f4c5aff0d24aa960ebc5853d4323d22a6b7eda1`.
The recorder was interrupted too: no finalized JSON/exit receipt exists for004,
and its later mypy/Ruff recipes were not reached. All remaining full-suite
coverage is pending; the separate quality run above is not that suite's result.

The exact live test was then reproduced with the same environment and OS
denial on the candidate and clean pristine v0.2.1. Both failed at the same
`assert result is not None` after denied name resolution. The candidate raw
log is `62015e25895667f309705cd538b90606b7ccfb13e26ef08527c45a91e381580d`;
the pristine log is `a1aa264ce19a563915faaf630ea188863bdb20230d7ff702af2a86704604fb39`.
The unchanged test/provider/configuration admit this live integration case via
`pytest.ini`'s `not llm` selector. This establishes the observed inherited
failure, not the outcome of unexecuted tests. Runtime source and collected
tests stayed frozen; no provider patches or test exclusions were introduced.
See [the retained failure record](native-suite-offline-finding-001.md) and
[#2934](https://github.com/CultureBotAI/CommunityMech/issues/2934).

All recorder triplets are retained under `.temp/phase2-schema-20261115/`.
Earlier interrupted native runs retain their partial logs and are not passes.
The first native invocation failed before tests because the recorder's
`JUST_NO_DOTENV=1` was incompatible with the installed `just`; later runs set
the accepted boolean value explicitly after the recorder separator.
The first bounded clinical reproductions refused nested sandbox setup before
pytest (exit71); separately numbered retries used the same explicit OS denial
with normal tool approval. No network was enabled.

- [#2930](https://github.com/CultureBotAI/CommunityMech/issues/2930): the first
  extractor could invent contiguous text across DOCX separators. Real synthetic
  DOCX controls failed before correction, then passed with preserved boundaries,
  genuine adjacent styled runs, refusal of hidden/revised text, and opaque
  unsupported cells. The first real preparation plan refused content controls;
  v2 resolved only the supported-neighbor case, preserving the source asset.
- [#2931](https://github.com/CultureBotAI/CommunityMech/issues/2931): validation
  calls were initially mislabeled comparisons. Exact matcher-result accounting
  now separates source-selection failures, including the actual control above.
- [#2933](https://github.com/CultureBotAI/CommunityMech/issues/2933): an apparently
  successful isolated sync reused the earlier local wheel. The second plan
  refused that stale installation before any comparison. Both old environments
  and failed plans remain preserved. An explicit fresh wheel and exact installed
  verification resolved the provenance gap. Independent review additionally
  found an unchecked extra-module case: the synthetic installed package admitted
  a stale extra before the fix and now refuses it, then passes after restoration.
- [#2932](https://github.com/CultureBotAI/CommunityMech/issues/2932): stale
  CommunityMech comments about reference annotations are a separate downstream
  documentation finding, not changed by this runtime implementation.
- The native issue-count label is already owned by
  [#257](https://github.com/CultureBotAI/CommunityMech/issues/257), with the
  current measured reproduction recorded there. No duplicate issue or counter
  implementation is included in the source-selection patch.

The source catalog is a reviewed provenance assertion, not independent publisher
authentication. Filesystem drift checks are cooperative, not a transaction
against a hostile writer. Broader formats, ambiguous table geometry and unknown
rendering remain unsupported. Cross-repository schema/runtime adoption and
canonical Switchgrass correction require their own reviewed changes.
