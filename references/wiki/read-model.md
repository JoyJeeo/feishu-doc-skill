# Wiki read model

Read this reference for Wiki node resolution, child listing, and read-only permission audits.

## Resolve one node

1. Classify the link and take the `/wiki/` token as `node_token`.
2. Call `wiki_v2_space_getNode` with that token and `useUAT: true`.
3. Preserve the returned `space_id`, `node_token`, `obj_token`, `obj_type`, `parent_node_token`, `node_type`, title, and child flag. Do not treat the Wiki token as the underlying document token.
4. Select the content reader from the returned `obj_type`. If that reader is unavailable, report the exact unsupported type and stop the content operation.
5. When the user supplies an actual document token instead of a Wiki link, pass its exact MCP `obj_type` to `space_getNode`; do not guess the type.

The node response is authoritative for routing. A title or URL suffix is only a display hint.

## List children completely

Call `wiki_v2_spaceNode_list` with the resolved `space_id`, exact parent node token, and `useUAT: true`. Continue with each returned `page_token` until `has_more` is false.

Permission filtering can produce an empty page while `has_more` is true. Do not stop because `items` is empty. Report the result as complete only after the terminal page; otherwise label counts and hierarchy as partial.

Preserve source order and the same node identity fields used above. Listing one parent returns direct children only; recursively describing a subtree requires complete child pagination for every visited parent.

## Space and permission audit

- Use `wiki_v2_space_get` for the resolved space's type, visibility, and sharing state.
- Use `wiki_v2_spaceMember_list` with complete pagination only when the user asks for space members or administrators.
- Use `drive_v1_permissionMember_list` with `type: wiki` and the Wiki node token for node collaborators. State whether `perm_type` is `container` or `single_page`.
- Use `drive_v2_permissionPublic_get` with `type: wiki` and the Wiki node token for public settings.

Keep space membership, node collaborators, and public settings as separate evidence. Do not infer one from another, expose more identity fields than the audit needs, or call any permission mutation tool.

## Default location

When the user omits a Wiki destination, read `config/default-locations.json` and use its exact `space_id` and `parent_node_token`. First resolve both values and report the selected space and parent title. If the configured parent is missing, inaccessible, or belongs to another space, stop instead of falling back to another location.

An explicit user target always overrides the default for that request.
