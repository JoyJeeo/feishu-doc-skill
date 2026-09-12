# MCP capability routing

Use this reference when identifying a Feishu resource or selecting tools.

## Allowed transport

Every remote Feishu tool name must start with `mcp__feishu__`. Local filesystem and deterministic helper scripts may be used for local planning, diffing, and validation, but never to send Feishu requests.

Do not call Chrome, CUA, browser automation, web tools, other connectors, or direct HTTP to compensate for a missing Feishu MCP tool.

## Resource routing

| Link segment | Resource type | Expected MCP prefix |
|---|---|---|
| `/docx/` | `docx` | `mcp__feishu__docx_` |
| `/sheets/` | `sheets` | `mcp__feishu__sheets_` |
| `/base/` | `bitable` | `mcp__feishu__bitable_` |
| `/wiki/` | `wiki` | `mcp__feishu__wiki_` plus the underlying resource prefix when needed |
| `/drive/` or `/file/` | `drive` | `mcp__feishu__drive_` |
| `/minutes/` | `minutes` | `mcp__feishu__minutes_` |
| `/board/` | `board` | `mcp__feishu__board_` |
| `/slides/` | `slides` | `mcp__feishu__slides_` |
| `/mindnote/` or `/mindnotes/` | `mindnote` | `mcp__feishu__mindnote_` |

For a Wiki link, first resolve the node and actual object type before choosing the content tool.

## Capability check

Before a remote call:

1. Identify the exact operation and target resource.
2. Identify the minimum read or write tools needed.
3. Check that those tools are visible.
4. Check whether they support user identity and prepare `useUAT: true` when available.
5. Treat permissions as unverified until the call succeeds.

Tool visibility does not imply authorization or complete resource support. For partially supported resources, perform only the exact operation backed by a visible tool.

## Current cloud-document snapshot

Observed from the connected Feishu MCP metadata on 2026-09-10. This is a development snapshot, not a permanent API promise.

| Prefix | Visible tools | User identity metadata |
|---|---:|---|
| `docx` | 21 | `useUAT` visible |
| `drive` | 52 | `useUAT` visible |
| `sheets` | 27 | `useUAT` visible |
| `bitable` | 46 | `useUAT` visible |
| `wiki` | 16 | `useUAT` visible |
| `minutes` | 3 | `useUAT` visible |
| `board` | 1 | `useUAT` visible |
| `slides` | 0 | unavailable |
| `mindnote` | 0 | unavailable |

The snapshot confirms tool metadata only. It does not prove that the current user can access a target resource or that a call's response matches the declared schema.

## M1-B minimum document contract

Use a direct Feishu China `/docx/` test document when available. A Wiki link is also valid after `mcp__feishu__wiki_v2_space_getNode` resolves it to an underlying `docx` object; all subsequent content calls must use the resolved document ID and `docx` tools.

Minimum tool chain:

1. `mcp__feishu__docx_v1_document_get` — read title and latest revision ID.
2. `mcp__feishu__docx_v1_documentBlock_list` — page through blocks and locate one user-designated disposable text block.
3. `mcp__feishu__docx_v1_documentBlock_get` — read the exact block before preview and again after writing.
4. `mcp__feishu__docx_v1_documentBlock_patch` — update only that block after confirmation.
5. `mcp__feishu__docx_v1_document_get` — obtain the post-write revision for verification evidence.

Pass `useUAT: true` on every call. Use the document revision and selected block content in the pre-write fingerprint. Use a stable `client_token` on the patch call when supported. M1-B verified `update_text_elements` for replacing one plain-text block; other block types and update payloads remain unverified and must not be inferred from that result.

The M1-B write must be a local text change in a dedicated test block. It must not create, delete, move, share, or change permissions on any resource. Any restoration is a separate write and therefore requires a new preview.

## M2 rich document creation contract

Use `mcp__feishu__docx_v1_documentBlockChildren_create` for flat first-level blocks. The currently connected MCP rejects even an exact, converter-generated minimal table through `mcp__feishu__docx_v1_documentBlockDescendant_create` with `invalid param`; treat descendant-create as unavailable until its parameter contract changes or gains a typed schema.

For a table in an existing document, use a staged write instead: create the empty table through `documentBlockChildren_create`, read back its generated table-cell and default text block IDs, then prepare a separate preview to fill those text blocks with `documentBlock_patch.update_text_elements`. Empty-table creation and row-major cell filling have both passed real readback verification and user-visible forward acceptance.

`mcp__feishu__docx_builtin_import` creates a new document; it does not update an existing Wiki-backed document. Do not use it as a corrective overwrite after a partially successful Wiki creation.

If a descendant-create request fails with `invalid param`, do not retry the same mixed payload in smaller arbitrary batches. A verified flat text write proves only the base child-create path; it does not validate nested insertion.

If node creation succeeds but content insertion fails, treat the preview as partially applied and never replay it. Reread the new document, then generate a separate preview for any corrective content write.

## Missing capability response

Use this result shape:

```text
当前飞书 MCP 未提供完成该操作所需的能力。
缺失能力：<capability or tool>
目标：<resource and scope>
本次未执行任何修改，也未尝试其他通道。
```
