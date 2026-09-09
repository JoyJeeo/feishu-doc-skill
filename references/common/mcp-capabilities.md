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

## Missing capability response

Use this result shape:

```text
当前飞书 MCP 未提供完成该操作所需的能力。
缺失能力：<capability or tool>
目标：<resource and scope>
本次未执行任何修改，也未尝试其他通道。
```
