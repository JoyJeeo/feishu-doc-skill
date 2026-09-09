---
name: feishu-doc-skill
description: Read, analyze, preview, create, or update Feishu China cloud documents through an already connected Feishu MCP. Use for Feishu Docs, Sheets, Bitable, Wiki, Drive, Minutes, and cross-resource document organization. Every write requires a confirmed preview; never use browser automation or OpenAPI as a fallback.
---

# Feishu Cloud Documents

Use this skill for personal Feishu China cloud-document work. Remote Feishu access is MCP-only.

## Invariants

- Use only tools whose names start with `mcp__feishu__` for every remote Feishu read or write.
- Never use Chrome, CUA, browser automation, another connector, or direct HTTP/OpenAPI as a fallback.
- If the required Feishu MCP tool is unavailable, report the missing capability and stop that operation.
- Use user identity by default. When a tool supports `useUAT`, set it explicitly to `true`.
- Never retry a failed user-identity call with application identity. Application identity requires an explicit user request and a new preview.
- Treat an initial change request as authorization to prepare a preview only. Write only after the user confirms that preview's `preview_id`.
- Before writing, reread the target and compare its state fingerprint. If it changed, invalidate the preview.
- After writing, reread the target and verify the declared result.
- Deletion, ownership transfer, and public-permission changes are disabled.

Read [references/common/safety-policy.md](references/common/safety-policy.md) and [references/common/identity-policy.md](references/common/identity-policy.md) before any remote Feishu operation.

## Route the request

| Mode | Use when | Workflow |
|---|---|---|
| `analyze` | The user asks to read, inspect, summarize, or audit without changes | [workflows/analyze.md](workflows/analyze.md) |
| `preview` | The user asks to create, change, move, organize, or format a Feishu resource | [workflows/preview.md](workflows/preview.md) |
| `apply` | The user confirms a specific valid `preview_id` | [workflows/apply.md](workflows/apply.md) |
| `verify` | The user asks to check an existing result, or a write just completed | [workflows/verify.md](workflows/verify.md) |

If the request contains both read-only analysis and a possible change, complete the analysis and produce a preview; do not apply the change in the same initial turn.

## Select tools

Read [references/common/mcp-capabilities.md](references/common/mcp-capabilities.md) when resolving a link or choosing MCP tools. A visible tool is not proof that the user has permission to call it.

Use `scripts/feishu_guard.py` for deterministic URL classification, identity selection, preview construction, and preview validation. It performs no network access.

Read [references/common/preview-protocol.md](references/common/preview-protocol.md) for every `preview` or `apply` request. Read [references/common/quality-rules.md](references/common/quality-rules.md) when generating or validating user-facing content.

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
