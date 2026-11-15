The native v0.2.1 `just test` includes a live ClinicalTrials.gov test despite its
integration marker. Under the explicit OS network denial required for this
local #1996 trial, that test fails because the provider cannot fetch its record.
This is reproduced on both the candidate and pristine base; it is not evidence
of a supplementary-source regression or a successful complete native suite.

The exact test is
`tests/test_clinicaltrials_integration.py::TestClinicalTrialsLiveAPI::test_fetch_real_clinical_trial`.
It requires a non-null return from `source.fetch("NCT00001372", config)`.
The provider catches the denied request and returns `None`. `pytest.ini`
overrides the pyproject pytest configuration and selects only `not llm`, which
includes this integration-marked test. No provider or test was patched.

Both executions used the same isolated Python 3.13.12 environment and retained
OS `deny network` profile. Candidate run `supplement-native-clinical-failure-002`
failed in 0.59 seconds; pristine `ae3979a14b9c99cc681ab1731e20c9df580b567f`
run `supplement-pristine-clinical-failure-002` failed in 0.57 seconds. Both
failed at line 166 with `assert None is not None` after a name-resolution
failure. The pristine launch checks exact clean HEAD and seven input hashes
before and after execution. Independent read verified that the test, provider,
fixtures and native configuration/recipes are byte-identical across branches.

Retained raw logs:

- Candidate: `62015e25895667f309705cd538b90606b7ccfb13e26ef08527c45a91e381580d`.
- Pristine: `a1aa264ce19a563915faaf630ea188863bdb20230d7ff702af2a86704604fb39`.
- Reproduction helper: `53f0e2e23db54e47a4b7d83704951fe844370650127cae2f6aa16ae2b1eef9c8`.

The full native run004 collected 733 tests and was explicitly interrupted
after the observed failure and further slow provider retries. Tool exit was
130. Its partial log is
`50836a563fa3e8acdfbf27c45f4c5aff0d24aa960ebc5853d4323d22a6b7eda1`.
The recorder was also interrupted, so there is no finalized JSON/exit receipt
for004; no such receipt was fabricated. Its later mypy/Ruff recipes were not
reached. The separately completed focused tests and quality checks retain
their own evidence. Remaining full-suite coverage stays pending.

Both first bounded reproduction attempts refused sandbox nesting with exit71
before pytest (`d34a4e4359a4dc36526cf5b363da32f7b7594a3a09eea17cbdfd6425b052d93e`).
The second attempts ran under the actual OS denial after normal tool approval;
outbound network and email-bearing requests remained prohibited.

Disposition: retain this inherited environment boundary while publishing the
candidate as a draft. Any future cache-only fixture repair or native test
selection correction needs a separate reviewed change preserving the tested
behavior; do not relax tests, claim a pass, or enable network to hide the failure.
This record is in the user's CommunityMech repository, linked to #1996; no
external linkml organization issue, PR or review is posted.
