# Project audit workflow

Use within `analyze` mode for a project-material inventory, source-traced status summary, or project audit.

1. Fix the project name, `as_of` date, exact source roots, traversal depth, and any user-declared required documents, fields, terminal statuses, or risk rules.
2. Check the minimum read tools for each resource and stop only the unsupported source; do not replace it with another channel.
3. Read each source with `useUAT: true` and its resource-specific completeness rules.
4. Assign stable local source IDs and record exact link, title, read scope, completeness, and limitation.
5. Extract atomic facts, then derive findings and recommendations without mixing the three kinds.
6. Build the evidence map from the project audit model and run `scripts/feishu_guard.py validate-project-audit`.
7. Report the project conclusion, coverage, facts, findings, pending confirmations, and limitations with source links.

This workflow performs no remote writes and creates no write preview. A failed or partial source read remains visible in coverage and cannot support a claim beyond the returned evidence.
