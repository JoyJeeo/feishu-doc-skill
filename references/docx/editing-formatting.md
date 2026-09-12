# Document editing and formatting

Read this reference for an existing `docx` section edit, formatting change, or lightweight table. It extends the document model and common preview rules.

## Fix the scope before drafting

Resolve one section from the complete block inventory. Prefer its heading block ID; otherwise use the full heading path. Record a match count of exactly one, every block ID in the section, and the surrounding same-or-higher-level heading IDs. Stop when the section is missing or ambiguous.

Never implement a local edit by overwriting the document root or an entire structural container. Blocks outside `target_block_ids` are out of scope. Unknown or opaque blocks inside the section remain in their original position and cannot appear in `affected_block_ids`.

## Build the edit plan

Use `append` to add content at the end of the section, `insert` for a declared position inside it, and `replace` only for the visible supported blocks named in the preview. Keep source facts, conclusions, recommendations, and pending confirmations distinct.

The preview must contain this local evidence:

```yaml
scope:
  selector:
    heading_block_id: heading ID when available
    heading_path: [full, heading, path]
    match_count: 1
  target_block_ids: [ordered IDs in the section]
  boundary:
    before: previous boundary heading ID or null
    after: next boundary heading ID or null
before_state:
  revision_id: current revision
  blocks: normalized complete document inventory
changes:
  before_blocks: complete visible blocks being changed
  after_blocks: complete replacement or inserted block plan
  affected_block_ids: existing blocks that a write may change
  preserved_block_ids: protected unknown or opaque blocks
  format_fallbacks: []
  pending_confirmations: []
```

`scripts/feishu_guard.py make-preview` rejects ambiguous selectors, out-of-section block IDs, unprotected opaque blocks, malformed tables, and undisclosed format fallbacks. Its deterministic `preview_id` is also the idempotency key: an applied append or insert preview cannot run again.

## Formatting

Use headings, text, bullets, ordered lists, quotes, code, tables, Callouts, and columns only when the visible MCP tools can write and read them back. Preserve existing formatting metadata on untouched text runs.

For a lightweight table, use `content.rows` as a non-empty rectangular list. Keep tables for repeated fields; ordinary parallel content stays a list.

With the current MCP, do not use `documentBlockDescendant_create` for tables: it rejects even exact converter output with `invalid param`. Apply a table as two separately confirmed stages:

1. Create an empty table block with `documentBlockChildren_create`, providing `row_size`, `column_size`, and optional `column_width` only.
2. Read back the table, its row-major `cells`, and each cell's default text child.
3. Generate a new preview that maps every requested cell value to one returned text block ID.
4. After confirmation, update those text blocks with `documentBlock_patch.update_text_elements`, stopping and rereading on the first failure.

Verify the final table from its `cells` order and text children, not from plain-text export alone. The empty table is a real partial result between the two previews and must be disclosed before stage 1.

If a requested format is not writable or cannot be verified, choose the simplest faithful supported block. Add an entry to `changes.format_fallbacks` with `requested_kind`, `rendered_as`, and `reason`, plus a `risks` item whose `type` is `format_degradation`. Do not claim format fidelity that the readback cannot prove.

## Apply and verify

After confirmation, reread the same inventory and revision, validate the fingerprint, then perform only the declared block-level calls. Stop on the first scope or conflict failure and report completed, failed, and unattempted actions.

Read back the edited section and both boundaries. Compare ordered visible content and supported formatting, confirm every protected block is unchanged, and confirm section-external fingerprints are unchanged. Mark uncertain formatting as partially verified rather than successful.
