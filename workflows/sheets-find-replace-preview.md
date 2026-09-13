# Sheets find/replace preview workflow

Use only for one exact-text, whole-cell replacement inside one rectangular range. This workflow extends the common preview protocol.

1. Resolve spreadsheet metadata and the complete worksheet list with user identity.
2. Select one exact worksheet ID and rectangular A1 range.
3. Find the old and replacement strings in that range with explicit, identical matching conditions.
4. Normalize and validate both match sets using the Sheets find/replace model.
5. Build one replacement plan containing every matched cell, the pre-existing replacement cells, the exact serialized replace arguments, and the expected post-write match sets.
6. Generate the deterministic preview with `scripts/feishu_guard.py make-preview` and stop for confirmation.

The preview scope must contain:

```yaml
entity: cells
spreadsheet_token: exact spreadsheet token
spreadsheet_title: current display title
sheet_id: exact worksheet ID
sheet_title: current display title
range: <sheet_id>!A1:B2
match_count: number of old-string matches
```

Use `operation: replace`. The preview must disclose the old and replacement strings, all matching cells, any cells already containing the replacement string, all four matching options, the exact apply arguments, and the manual outside-range check.

After confirmation, repeat the same reads and validate the preview against the fresh state. Call `sheets_v3_spreadsheetSheet_replace` only with `changes.apply_arguments`, then follow the common verify workflow and the post-write checks in the Sheets model.

Stop without writing if the worksheet or match sets changed, any match lies outside the declared range, the old string has no matches, the required tools are missing, or arbitrary cell-value access would be needed.
