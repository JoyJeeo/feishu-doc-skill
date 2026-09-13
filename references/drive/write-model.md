# Drive write model

Read this reference for folder-scoped Drive 变更前的定位、写入前校验与版本更新预览。

## Folder create

1. Read the exact parent folder and complete child list with `useUAT: true`.
2. Keep `before_state.folder_token` and `children` (each with `token`, `name`, `type`).
3. Scope must include:
   - `parent_folder_token` (允许空串表示根目录)
   - `resource_type: folder`
4. Changes must include:
   - `name` (non-empty)
   - `resource_type: folder`
   - `pending_confirmations`
5. Reject when a direct child with same `name` already exists.

## Copy

1. Read source node and target parent folder with complete snapshot.
2. Scope must include:
   - `source_token`
   - `source_type` (`file`、`doc`、`sheet`、`bitable`、`docx`、`mindnote` 或 `slides`)
   - `target_parent_folder_token`
3. Keep `before_state.source` and `before_state.target_parent` containing:
   - `token`
   - `name`
   - `type`
   - `children` of target parent (ordered)
4. Changes should include:
   - `name` (optional, defaults to source name)
   - `pending_confirmations`
5. Reject folders and any source type not accepted by `drive_v1_file_copy`.
6. Reject if `target_parent` already has same target `name`.
7. Lock `apply_arguments` to the exact source token/type, destination folder token, target name, and `useUAT: true`.

## Move

Use the copy checks, but allow `folder` as a source type and additionally require `source_parent_folder_token` in scope and `before_state.source.parent_folder_token`. Reject when the move has no effective location change, or when the target parent already has the same target name. The write target must be a real non-empty folder token; when moving to the root, use the unique root `parent_token` established by the complete root listing rather than the empty-string listing input.

## File version create (update)

1. Read file metadata and the complete current version list with `fileVersion_list`.
2. Scope must include:
   - `resource_token`
   - `resource_type` (`docx` or `sheet`)
3. Changes must include:
   - `name` (non-empty version name)
   - exact `apply_arguments`: `path.file_token`, `data.name`, `data.obj_type`, and `useUAT: true`
   - `pending_confirmations`
4. Keep `before_state.resource` with:
   - `token`
   - `type`
   - `name`
5. Keep the complete existing `versions` list and `versions_complete: true` in `before_state`.
6. Reject unsupported resource types, incomplete version lists, duplicate version entries, and an existing version with the requested name.
7. After creation, list versions again and use `fileVersion_get` to verify the returned version identifier, name, and source resource.

## Export task create

1. Read exact source metadata and keep its token, type, title, and current modification time.
2. Scope must use `entity: export_task` and include source token/type plus the requested extension.
3. The current supported subset is `doc`/`docx` to `docx` or `pdf`, and `sheet`/`bitable` to `xlsx`; CSV export remains out of scope because it requires a separately resolved sheet or table ID.
4. Lock `apply_arguments` to the exact source token/type, extension, and `useUAT: true`.
5. After creation, read the asynchronous result with `exportTask_get` and verify only the returned task status, file token, file name, extension, and size.
6. This metadata check does not verify that the exported file can be downloaded, opened, or contains complete content. Because the current MCP exposes no export-file download tool, report usable export as unsupported and do not mark the export capability complete.

## Import existing file token

1. Accept only a file token with a verifiable upload or existing Drive-file provenance; local-file upload remains unsupported because the current MCP lacks the upload-part tool.
2. Do not use a token returned by `exportTask_get` as an import source. A real call returned `1069910 import file extension not match` even though the export metadata reported `docx`; export result tokens are for the download flow and are not a verified import source.
3. Read the exact target folder and complete child list, and keep the source file name, extension, `file` type, provenance, and token metadata supplied by the originating MCP result. A positive size is mandatory for a direct upload result; it may remain unknown for an existing Drive file because the current listing and metadata tools do not expose file size.
4. The verified subset is an existing Drive `file` whose name ends in `.docx`, imported as a new `docx` document in a non-root target folder.
5. Reject duplicate target names and lock the exact source token, extension, target type, target name, folder mount key, `mount_type: 1`, and `useUAT: true`.
6. Read the asynchronous task result, then confirm the new document appears only in the target folder with the requested title and type.

## Verification and acceptance

Preview should state:
- source/target identity
- exact token/type pair for each target
- duplicate-name and no-op checks
- required tools (all `mcp__feishu__` prefixed)
- post-write readback strategy

## Disabled/forbidden operations

- `delete`
- `transfer_owner`
- `public_permission_change`

These remain blocked for all Drive write paths.
