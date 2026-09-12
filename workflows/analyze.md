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

Do not:

- call a write tool;
- create a write preview unless the user also requested a change;
- retry with application identity;
- use another channel when reading fails.

If the request also asks for a future change, finish the analysis and route the change to the preview workflow.
