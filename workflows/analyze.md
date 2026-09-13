# Analyze workflow

Use for read-only inspection, summarization, comparison, or audit.

1. Identify the target resource and requested scope.
2. Classify the Feishu link with `scripts/feishu_guard.py classify-url` when useful.
3. Read the common safety and identity policies.
4. Check that the required read tools exist under `mcp__feishu__`.
5. Call only the minimum Feishu MCP read tools, explicitly using `useUAT: true` when supported.
6. Analyze the returned content using the quality rules.
7. Report findings, evidence, uncertainties, and unsupported areas.

For a `docx` quality audit, read the document model and follow [docx-audit.md](docx-audit.md).

For a `bitable` inspection or data-quality audit, read [../references/bitable/data-model.md](../references/bitable/data-model.md). Page through the complete table, field, and selected-record results before reporting counts or duplicates.

For a `sheets` inspection, read [../references/sheets/find-replace.md](../references/sheets/find-replace.md). Report only spreadsheet metadata, the complete worksheet list, or exact-text whole-cell matches inside one declared rectangular range; do not imply arbitrary cell-value reading.

For a `wiki` inspection, read [../references/wiki/read-model.md](../references/wiki/read-model.md). Resolve the node before selecting its content tool, and follow every child-node page until `has_more` is false even when an intermediate page is empty.

For a Drive folder, file lookup, metadata, collaborator, or public-permission inspection, read [../references/drive/read-model.md](../references/drive/read-model.md). Search only inside one exact folder, page the complete listing when pagination is supported, and distinguish folder-list evidence from exact metadata and permission evidence.

Do not:

- call a write tool;
- create a write preview unless the user also requested a change;
- retry with application identity;
- use another channel when reading fails.

If the request also asks for a future change, finish the analysis and route the change to the preview workflow.
