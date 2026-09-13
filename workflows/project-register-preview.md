# Project register preview workflow

Use within `preview` mode for project action, risk, decision, or metric registers.

1. Read the project register model, Bitable data model, and common preview protocol.
2. Resolve one exact existing Bitable app with `useUAT: true`. Creating a new app is outside this verified path.
3. Page through the complete data-table list. Select one requested register role and stop on an exact same-name conflict.
4. Build only that role's required ordered field contract. Do not add fields, select options, owners, dates, values, or sources that the user did not provide.
5. Create one Bitable table preview with `scope.entity: table`, the complete pre-write table list, exact MCP-ready `changes.table`, business-key field, source field, and exact field-list readback plan.
6. Run `scripts/feishu_guard.py make-preview`, render the table name, columns, types, options, unchanged existing tables, risks, and verification as a locally viewable effect confirmation, then stop.

After confirmation, reread the complete table list, validate the same preview, create only that table with `appTable_create` and `useUAT: true`, then reread the complete table list and the new table's full field list. The exact name, field order, field types, select options, business key, and source field must match before the table is reported as verified.

Repeat the full preview-confirm-apply-verify cycle independently for another register. After a table exists and is verified, route record changes through the Bitable record preview workflow.
