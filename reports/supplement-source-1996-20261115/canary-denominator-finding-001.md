# Source-routing canary must distinguish calls from quote comparisons

Independent read of the unexecuted #1996 scratch-canary runner found that
`native_comparisons = len(events)` counts native `validate()` returns, including
an explicit source-selection failure that never calls the matcher. The
independent 37-path census is useful, but is not a quote-comparison denominator.

Affected runner SHA:
`89d8f0d698bef80f3dda058a4c590cfe95818c3b8c9a9d871a996f1a26fead84`.
No retained-source run or published canary result exists from this version.

Acceptance: retain `native_validation_calls` separately. Count a comparison
only when an actual native match result exists. Require these exact outcomes:

| Control | Calls | Comparisons | Matches | Mismatches | Source-selection failures |
|---|---:|---:|---:|---:|---:|
| Article only | 37 | 37 | 35 | 2 | 0 |
| Selected | 37 | 37 | 37 | 0 | 0 |
| Wrong cell | 37 | 37 | 36 | 1 | 0 |
| Wrong parent | 37 | 36 | 36 | 0 | 1 |

Keep exact failed paths, native nonzero controls, input hashes and restoration.
Compare every established source identity to the prepared parent, asset ID,
version, locator, asset/extraction/catalog hashes and selected-cell digest.

Related: https://github.com/CultureBotAI/CommunityMech/issues/1996
