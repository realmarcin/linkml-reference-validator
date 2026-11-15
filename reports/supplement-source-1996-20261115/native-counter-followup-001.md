The same issue-count label remains observable in the retained v0.2.1 runtime
used for the isolated #1996 supplementary-source candidate. This is a
deduplicated follow-up to #257, not evidence that validation is a no-op.

The installed native CLI processed one scratch Switchgrass record. Independent
observation of real `SupportingTextValidator.validate` returns established
37 calls, 37 non-null matcher results and 37 matches, while native stdout
still printed `Total checks: 0`. The exact native log SHA256 is
`67f82fc6201fa9d1b101d413f1d4f849da8ea769c0a62d5c2c9b06bf83285bec`;
the persisted measured receipt SHA256 is
`e911410ac55cda792b4b5e5d56df093e5b8c7e042398f1e467467aa571d863e3`.
The selected-source patch leaves this preexisting label unchanged. Its own
coverage claims use actual match results and distinguish source-selection
failure from comparison; the wrong-parent control has 37 calls but only
36 comparisons.

Deduplication included live all-state own-repository searches for `Total checks`
and reference counters, full live #257/#1469 reads, and an ignored/hidden-file
inclusive search of CommunityMech reports, integration evidence and scripts.
#257 directly owns the misleading native label; #1469 records historical
reporting corrections. No duplicate issue or external upstream notification
is needed. No state change or counter implementation is included in the
bounded #1996 source-selection work.
