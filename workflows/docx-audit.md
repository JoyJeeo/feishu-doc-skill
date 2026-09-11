# Docx quality audit workflow

Use this read-only workflow inside `analyze` mode.

1. Read the common safety, identity, MCP capability, and quality rules.
2. Read [the document model](../references/docx/document-model.md).
3. Resolve the target to a `docx` document and confirm the requested audit scope.
4. Read metadata and all blocks with user identity, following pagination and nested content needed for the scope.
5. Build the normalized inventory without discarding unknown blocks.
6. Run the structure, clarity, consistency, completeness, and fidelity checks supported by the available evidence.
7. Report findings in severity order. Include the target, audited scope, block or heading-path evidence, limitations, and unsupported content.

An audit performs no remote write and creates no `preview_id`. If the user also requests corrections, finish the audit first and route the proposed corrections to the preview workflow.
