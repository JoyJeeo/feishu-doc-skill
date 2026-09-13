# Sheets find/replace model

Read this reference for worksheet inspection and range-bound replacement. The connected Feishu MCP does not expose arbitrary range-value reads or writes, so this capability must not be presented as general spreadsheet editing.

## Resolve the target

1. Read spreadsheet metadata with `sheets_v3_spreadsheet_get`.
2. Read the complete worksheet list with `sheets_v3_spreadsheetSheet_query`.
3. Select one exact `sheet_id`; use its current title only as a display label. Stop if the ID is absent, duplicated, or does not match the previewed title.
4. Use one rectangular A1 range in the form `<sheet_id>!A1:B2`. Whole-column, whole-row, reversed, multi-sheet, and disjoint ranges are unsupported.

## Supported matching

Use `sheets_v3_spreadsheetSheet_find` with all four options explicit. Require `match_entire_cell: true`, `search_by_regex: false`, and `include_formulas: false`. `match_case` may be either boolean value but must be shown in the preview.

Before a replacement, find both the old and replacement strings inside the same exact range. Retain every returned cell address and reject the preview when:

- the old string has no matches;
- a returned address is outside the range or belongs to another worksheet;
- old- and replacement-string match sets overlap;
- the response is incomplete or cannot be normalized to unique cell addresses.

The preview fingerprint covers spreadsheet and worksheet identity, range, worksheet list, both match sets, strings, and matching options.

## Replacement and verification

Serialize the exact `spreadsheetSheet_replace` arguments into `changes.apply_arguments`, including `useUAT: true`. The local guard requires those arguments to match the previewed token, worksheet, range, strings, and conditions.

After confirmation, repeat the metadata, worksheet-list, and two find calls. Invalidate the preview if any fingerprint input changed. Apply the serialized arguments once, then find both strings again in the same range. Verification succeeds only when:

- the old string has no matches;
- replacement-string matches equal the union of its pre-existing matches and the old-string matches;
- the service result does not report a contradictory replacement count;
- the user can inspect the target and confirm that cells outside the range did not change.

The exact range passed to the Feishu replace endpoint constrains the write. Because no arbitrary range reader is visible, outside-range content cannot be independently reread through MCP; record that part as a manual check instead of claiming full automated verification.

## Unsupported requests

Stop without writing when the request needs cell matrices, arbitrary values, formulas, formatting, sorting, cleaning, standardization, structural edits, or multiple ranges. Report the missing arbitrary range-value capability and do not use another connector, browser, or OpenAPI.
