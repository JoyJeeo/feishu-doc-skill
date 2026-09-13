# Wiki write model

Read this reference for Wiki 只读解析后可执行的创建、复制、移动和改名预览。

## Create node

1. Read parent context and keep `space_id` and `parent_node_token` with `useUAT: true`.
2. Resolve and keep parent child list snapshot (`node_token`, `title`, `node_type`) with stable order.
3. Build deterministic `before_state` including:
   - `space_id`
   - `parent_node_token`
   - `children` list
4. Scope must include:
   - `space_id`
   - `parent_node_token`
   - optional `placement`
5. Changes must include:
   - `title` (non-empty)
   - `node_type` (`docx`、`sheets`、`bitable` 或其他已确认支持对象类型)
   - `pending_confirmations`
6. Reject if target child list already contains the same title.

## Move / copy existing node

1. Resolve source node and target parent with complete state.
2. Scope must include:
   - `space_id`
   - `source_node_token`
   - `source_parent_node_token`
   - `target_parent_node_token`
3. Keep `before_state.source_node` and `before_state.target_parent` with:
   - `space_id`
   - `node_token`
   - `parent_node_token`
   - `title`
   - `node_type`
   - parent `children` with names and tokens
4. Changes should include:
   - `title` (optional, defaults to source title)
   - `pending_confirmations`
5. Reject when `move` results in no effective change (`source_parent == target_parent` and unchanged title).
6. Reject when target parent already has same title that is not clearly the moved node itself in an allowed position.

## Rename (update) existing node

1. Scope and before-state must clearly identify same node and parent.
2. Keep:
   - `space_id`
   - `scope.node_token`
   - `scope.parent_node_token`
   - `before_state.node` with old `title`
3. Changes must include:
   - `title` (non-empty and changed)
   - `pending_confirmations`

## Move Drive document into Wiki

1. Read the source document's exact Drive folder entry and metadata, plus the complete target Wiki child list.
2. Scope must include `entity: drive_document`, source token/type/folder, target `space_id`, and target parent node token.
3. Support only source types accepted by `spaceNode_moveDocsToWiki`.
4. Reject a target parent that already contains the source title.
5. Lock `apply_arguments` to the exact source, target, `useUAT: true`, and `apply: false`; never create a deferred permission request when the current user cannot move the document.
6. After execution, read the asynchronous result with `wiki_v2_task_get`, then confirm the source disappears from its Drive folder and resolves as a child of the declared Wiki parent with the same title and object type.

## Verification and acceptance

Preview should state:
- source and target space/parent
- expected name and destination
- no-op checks
- required tools (all `mcp__feishu__` prefixed)
- readback point and conflict explanation

## Disabled/forbidden operations

- `delete`
- `transfer_owner`
- `public_permission_change`

These stay blocked even if a tool appears visible.
