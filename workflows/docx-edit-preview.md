# Docx section edit preview workflow

Use this workflow in `preview` mode for a section-level append, insert, replace, formatting change, or lightweight table.

1. Read the common safety, identity, capability, preview, and quality rules, plus the document model and editing-formatting reference.
2. Check the exact document read, block write, and readback tools. Use user identity for every remote read. For a table, select the staged child-create and cell-patch path; do not select descendant-create while its contract remains unsupported.
3. Read document metadata and every block page. Preserve the raw response and build the normalized inventory.
4. Resolve one section by heading block ID or full heading path. Record `match_count: 1`, ordered target block IDs, and both boundaries; stop on zero or multiple matches.
5. Build complete before and after block plans. List existing affected IDs, protected unknown or opaque IDs, pending confirmations, and any format fallbacks. A new table needs one preview for the empty container and a second preview after the generated cell text IDs are known.
6. Use `scripts/feishu_guard.py make-preview` to reject out-of-scope effects, implicit opaque-block replacement, malformed tables, and undisclosed format loss.
7. Show the exact section, before and after content, structural changes, format risks, protected blocks, required tools, and readback checks with the `preview_id`.
8. Stop without writing. Only confirmation of that exact `preview_id` can enter `apply`.

An append or insert uses its deterministic `preview_id` as the idempotency key. If that ID is already applied, do not issue any write call. A changed document revision or block inventory invalidates the preview.
