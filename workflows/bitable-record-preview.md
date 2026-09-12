# Bitable record preview workflow

Use this workflow for Bitable record creation or updates. It extends the common preview protocol.

1. Resolve the exact `app_token` and `table_id` with user identity.
2. Page through the full field schema and select one explicit business-key field.
3. Search all proposed keys and finish every result page. For updates, read each uniquely matched record.
4. Build the normalized pre-write state from the Bitable data model.
5. Validate field names, writable types, existing select options, key uniqueness, and match counts locally.
6. Build one homogeneous record plan. Each entry contains its key, record ID for updates, changed fields, exact before/after values, and field differences.
7. Include data-quality findings and unresolved choices. Do not invent missing values or create select options implicitly.
8. Generate the deterministic preview with `scripts/feishu_guard.py make-preview` and stop for confirmation.

The preview scope must contain:

```yaml
entity: records
app_token: exact app token
table_id: exact table ID
table_name: display name
business_key_field: exact field name
record_count: number of planned records
```

Use `operation: create` only when every key has zero matches. Use `operation: update` only when every key has one exact `record_id`. The preview must list all changed records even when the conversational summary is abbreviated.

After confirmation, rerun the same field and key reads, validate the preview against the new state, then call only the declared single or batch write tool. For creates, use the preview's stable `client_token` when the tool supports it. Follow the common apply and verify workflows, including affected-record readback and a second complete key search.

Stop without writing if pagination is incomplete, the schema or key matches changed, a field type is unsupported, a select value would create a new option, or the exact target cannot be proven.
