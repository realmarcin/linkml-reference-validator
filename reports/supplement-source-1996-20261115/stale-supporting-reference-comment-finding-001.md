# Native-reference recipe comment still describes the repaired annotation gap

Independent downstream planning review found that CommunityMech `justfile`
lines 153–156 still state that `SupportingReference` has no `implements`
annotations and Discussion evidence snippets are never checked. The maintained
shared schema now annotates both `SupportingReference.reference` with
`linkml:authoritative_reference` and its `snippet` with `linkml:excerpt`.

Read-only verification at CommunityMech integration commit
`fe054a5af8d9a7b90b81dfe9267dcb25ea682891` confirms the contradiction.
The adjacent warning that the CLI labels issue counts as "Total checks" remains
valid and must remain. This is a stale explanatory comment, not a new runtime
validation defect.

Acceptance: narrowly update that historical annotation-gap statement alongside
the eventual source-routing integration, preserving the issue-counter and
substring/representation limitations. Do not edit frozen curation/preparation
checkouts or imply whole-corpus reference validity.

Related: https://github.com/CultureBotAI/CommunityMech/issues/1996
