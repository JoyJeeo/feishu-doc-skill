---
name: feishu-doc-skill
description: Read, analyze, preview, create, or update Feishu China cloud documents through an already connected Feishu MCP. Use for Feishu Docs, Sheets, Bitable, Wiki, Drive, and cross-resource document organization. Every write requires a confirmed preview; never use browser automation or OpenAPI as a fallback.
---

# Feishu Cloud Documents

Use this skill for personal Feishu China cloud-document work. Remote Feishu access is MCP-only.

## Invariants

- Use only tools whose names start with `mcp__feishu__` for every remote Feishu read or write.
- Never use Chrome, CUA, browser automation, another connector, or direct HTTP/OpenAPI as a fallback.
- If the required Feishu MCP tool is unavailable, report the missing capability and stop that operation.
- Use user identity by default. When a tool supports `useUAT`, set it explicitly to `true`.
- Never retry a failed user-identity call with application identity. Application identity requires an explicit user request and a new preview.
- Treat an initial change request as authorization to prepare a preview only. Render every preview as a locally viewable effect confirmation showing the actual content, before/after difference, and unaffected scope. A `preview_id` only binds the operation and never substitutes for the visible preview. Write only after the user confirms the displayed operation.
- Before writing, reread the target and compare its state fingerprint. If it changed, invalidate the preview.
- After writing, reread the target and verify the declared result.
- Deletion, ownership transfer, and public-permission changes are disabled.

Read [references/common/safety-policy.md](references/common/safety-policy.md) and [references/common/identity-policy.md](references/common/identity-policy.md) before any remote Feishu operation.

## Route the request

| Mode | Use when | Workflow |
|---|---|---|
| `analyze` | The user asks to read, inspect, summarize, or audit without changes | [workflows/analyze.md](workflows/analyze.md) |
| `preview` | The user asks to create, change, move, organize, or format a Feishu resource | [workflows/preview.md](workflows/preview.md) |
| `apply` | The user confirms the specific locally displayed preview bound to a valid `preview_id` | [workflows/apply.md](workflows/apply.md) |
| `verify` | The user asks to check an existing result, or a write just completed | [workflows/verify.md](workflows/verify.md) |

If the request contains both read-only analysis and a possible change, complete the analysis and produce a preview; do not apply the change in the same initial turn.

## Select tools

Read [references/common/mcp-capabilities.md](references/common/mcp-capabilities.md) when resolving a link or choosing MCP tools. A visible tool is not proof that the user has permission to call it.

Use `scripts/feishu_guard.py` for deterministic URL classification, identity selection, preview construction, and preview validation. It performs no network access.

Read [references/common/preview-protocol.md](references/common/preview-protocol.md) for every `preview` or `apply` request. Read [references/common/quality-rules.md](references/common/quality-rules.md) when generating or validating user-facing content.

For any `docx` content request, read [references/docx/document-model.md](references/docx/document-model.md). For a document quality audit, follow [workflows/docx-audit.md](workflows/docx-audit.md) within `analyze` mode. For new document content or a creation preview, read [references/docx/content-generation.md](references/docx/content-generation.md) and [references/docx/templates.md](references/docx/templates.md), then follow [workflows/docx-create-preview.md](workflows/docx-create-preview.md).

For a section-level append, insert, replace, formatting change, or document table, read [references/docx/editing-formatting.md](references/docx/editing-formatting.md), then follow [workflows/docx-edit-preview.md](workflows/docx-edit-preview.md). The common `apply` and `verify` workflows remain mandatory after preview confirmation.

For any Bitable request, read [references/bitable/data-model.md](references/bitable/data-model.md). For record creation or updates, follow [workflows/bitable-record-preview.md](workflows/bitable-record-preview.md); the common `apply` and `verify` workflows remain mandatory after preview confirmation.

For a Sheets request, read [references/sheets/find-replace.md](references/sheets/find-replace.md). Only worksheet identification and exact-text whole-cell find/replace inside one rectangular A1 range are supported. For a replacement, follow [workflows/sheets-find-replace-preview.md](workflows/sheets-find-replace-preview.md); the common `apply` and `verify` workflows remain mandatory after preview confirmation.

For a Wiki request, read [references/wiki/read-model.md](references/wiki/read-model.md)。若涉及 Wiki 创建、复制、移动或改名，请先读 [references/wiki/write-model.md](references/wiki/write-model.md)。For Drive folder/file lookup、metadata、协作者或公开设置查看，请读 [references/drive/read-model.md](references/drive/read-model.md)。涉及文件夹创建、文件复制/移动或文件版本更新，请改读 [references/drive/write-model.md](references/drive/write-model.md)。Use [config/default-locations.json](config/default-locations.json) only when the user does not specify a location; an explicit target always overrides it.

For a cross-resource project-material inventory, source-traced status summary, or project audit, read [references/project/audit-model.md](references/project/audit-model.md) and follow [workflows/project-audit.md](workflows/project-audit.md). This path is read-only: do not turn audit findings into write previews unless the user separately requests changes.

For a project home, project document set, or weekly report, read [references/project/workspace-model.md](references/project/workspace-model.md) and follow [workflows/project-workspace-preview.md](workflows/project-workspace-preview.md). Keep one preview and confirmation per resource, and do not prepare a dependent child or link-update preview until its prerequisite resource has been verified.

For project action, risk, decision, or metric registers, read [references/project/register-model.md](references/project/register-model.md) and follow [workflows/project-register-preview.md](workflows/project-register-preview.md). Use one existing Bitable app and one preview-confirm-verify cycle per data table; route later record writes through the ordinary Bitable record workflow.

For final cross-resource verification, read [references/project/integration-model.md](references/project/integration-model.md) and follow [workflows/project-integration-verify.md](workflows/project-integration-verify.md). Preserve failed and unattempted resources instead of promoting a partial outcome to success.

## Stop conditions

Stop the affected operation without side effects when:

- the target or requested scope cannot be identified uniquely;
- the required Feishu MCP capability is unavailable;
- user-identity authorization fails;
- the user has not confirmed the exact preview;
- the target changed after preview generation;
- the operation is disabled by policy;
- verification cannot establish whether the write succeeded.

Report the stage, target, reason, completed actions, failed actions, and actions not attempted. Never turn a partial result into a success claim.
