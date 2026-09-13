# Drive read model

Read this reference for folder-scoped file lookup, exact metadata, collaborators, and public-permission audits.

## Select one folder

Use the user-supplied `/drive/folder/` token. If the user omits a location, read `config/default-locations.json`; an empty `drive.folder_token` means the user's Drive root and must be passed as an empty string, not replaced with another folder.

The empty string is only the root-listing input. A move or copy write requires the actual target folder token. For the Drive root, derive one unique root `parent_token` from the complete returned root items; if the root is empty or returned items disagree, report that the root write target cannot be identified and stop.

Do not search a broader folder after an empty or failed result. An explicit user target always overrides the default.

## List and locate files

Call `drive_v1_file_list` with the exact `folder_token` and `useUAT: true`. For a non-root folder, follow every `page_token` until `has_more` is false. The MCP documents root listing as an all-items, non-paginated response.

Filter the completed direct-child listing locally by the user's requested name and returned file type. Preserve token, type, name, parent token when returned, owner ID, creation time, modification time, and URL. Do not claim recursive or global search: a folder listing covers only that exact folder.

Zero matches, multiple exact matches, or incomplete pagination are not a unique target. Report the candidates and stop any operation that needs one file.

## Read exact metadata

Use `drive_v1_meta_batchQuery` only after tokens and MCP document types are known. Send at most 200 exact token/type pairs per call and request URLs only when useful. Preserve each request pair in the result so same-token values of different types cannot be confused.

Folder-list fields are discovery evidence; batch metadata is the authoritative evidence for the requested file properties. Missing batch results must be reported rather than filled from a similarly named item.

## Permission audit

For each exact target:

- Call `drive_v1_permissionMember_list` with its token, matching MCP type, minimal requested `fields`, and `useUAT: true`.
- Call `drive_v2_permissionPublic_get` with the same token and type and `useUAT: true`.
- Report explicit collaborators separately from public-link, external-access, copy/download, and collaborator-management settings.

Do not infer inherited access or effective user access from these two calls alone. Never call member deletion, ownership transfer, password mutation, or public-permission mutation tools.

## Report

Include the exact folder, whether listing pagination completed, filters used, match count, exact token/type for each selected file, metadata source, permission source, and uncertainties. State clearly when only direct children were searched or when access inheritance was not established.
