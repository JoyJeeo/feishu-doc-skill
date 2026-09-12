# Bitable data model

Read this reference for Bitable inspection, data-quality checks, and record-change planning.

## Resolve the target

For `/base/` links, use the URL token as `app_token`. For Wiki links, first resolve the node and require its underlying object type to be `bitable`.

1. Read app metadata with user identity.
2. Page through every data table and select one exact `table_id`. A name is only a display aid; stop if a name is not unique.
3. Page through every field in that table. Preserve `field_id`, `field_name`, numeric type, `ui_type`, options, properties, and descriptions returned by MCP.
4. Prefer `appTableRecord_search` for records. Page until `has_more` is false. Do not use the historical record-list tool when search is available.

Never infer that the first page is complete. Tool visibility and a successful metadata call do not prove record read or write permission.

## Normalized pre-write state

Before a record preview, retain this non-sensitive structure in task context:

```yaml
app_token: exact app token
table_id: exact table ID
table_name: current table name
fields_pagination_complete: true
records_pagination_complete: true
fields:
  - field_id: exact field ID
    field_name: current field name
    ui_type: Text | Number | SingleSelect | ...
    options: [existing option names] # option fields only
records:
  - record_id: exact record ID
    fields: {selected field name: current value}
```

Include all fields that a proposed write touches and all records returned by the complete business-key query. The fingerprint covers this state. Reread the same fields and key matches before applying.

## Business keys and matching

Choose one user-visible, stable field such as project ID or task ID. Do not silently fall back from an ID to a name.

- Create: every proposed key must be non-empty, unique inside the preview, and have zero matches after complete pagination.
- Update: every proposed key must have exactly one match, and the planned `record_id` must equal that match.
- Zero matches on update, multiple matches, incomplete pagination, or a changed match set invalidate the operation.
- Keep the business key unchanged during ordinary updates. A key migration requires a separately scoped preview.

## Field values

Validate proposed values against the freshly read field schema. The local guard supports these shapes:

- `Text`, `Email`, `Barcode`, `SingleSelect`, `Phone`: string.
- `Number`, `Progress`, `Currency`, `Rating`: number, excluding booleans.
- `MultiSelect`: string array.
- `DateTime`: millisecond integer.
- `Checkbox`: boolean.
- `Url`: object with a non-empty `link` and optional string `text`.

Single- and multi-select values must already exist in the field options. Creating a new option changes schema and requires a separate field-change preview.

Formula, created/modified metadata, creator/modifier, and auto-number fields are read-only. User, group, attachment, relation, location, and other complex values remain unsupported until their exact MCP payloads pass real integration validation; stop instead of guessing.

## Data-quality audit

Report issues with the table, record ID or business key when available, field, evidence, and impact. Check only what the returned schema and complete record set can prove:

- missing or duplicate business keys;
- empty values for user-declared required fields;
- values incompatible with field type;
- select values absent from current options;
- broken relation identifiers when the related record set was also read;
- unexpected status, date, or numeric values under an explicit user rule.

Do not treat an empty value as an error without a required-field rule, invent replacement values, or mutate data during an audit.

## Batches and failures

Keep each preview homogeneous: create records or update records, never both. Use single-record tools for one record and batch tools only when more than one record is declared. A batch preview lists every key and field difference even if the user-facing summary shows representative rows.

Use `client_token` for create calls when supported and keep consistency checking enabled. After a write, reread affected record IDs and the complete business-key match set. If a batch is partially successful, pass its planned, successful, and failed keys through `summarize_batch_outcomes` in `scripts/feishu_guard.py`; report the returned successful, failed, and unattempted groups separately, and never replay the whole preview.
