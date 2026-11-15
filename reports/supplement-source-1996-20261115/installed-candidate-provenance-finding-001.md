# A successful sync did not establish the candidate's installed source bytes

The isolated #1996 workflow created a fresh environment with `uv sync --frozen
--no-editable`, but it reused the earlier local project's built distribution.
The v2 source tree had changed while its Git revision and package version had
not. A new environment therefore still contained the earlier v1 extractor.
This is an observed candidate-installation provenance failure, not a claim of
an upstream uv defect.

The second preparation plan stopped before creating its scratch namespace or
performing any native quotation comparison. Its retained failure log SHA is
`a57fbe45167460bbd4101c5e4f76bc98d690636258ed810021093a54687deb19`.
Installed candidate environment 002 and prior environment 001 remain unchanged.
The source-tree focused tests passed, but they do not establish installed
candidate behavior. The full native test attempt 003 was explicitly interrupted
and is not an installed-candidate pass.

Acceptance: build an explicit new wheel, compare every package Python member
to the captured candidate source, install that exact wheel in a fresh isolated
environment with copied site-package files, and verify all installed members
before any new preparation plan. Retain wheel/source/installed hashes and the
actual environment. Re-run the one-record canary through that installed package.
Never infer artifact identity from installer success or version text alone.

Related: https://github.com/CultureBotAI/CommunityMech/issues/1996
