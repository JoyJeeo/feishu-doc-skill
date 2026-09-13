# Project audit model

Read this reference for a cross-resource project-material inventory, source-traced status summary, or read-only project audit.

## Fix the audit scope

Start from the exact resources supplied by the user or one declared Wiki parent. A Wiki child listing covers only direct children unless the user requests recursive traversal; a Drive folder listing is also direct-child only. Do not broaden an empty result into a global search.

Read each source through its resource model:

- Docx: metadata and complete block hierarchy.
- Wiki: resolved node and complete child pagination for every parent in scope.
- Drive: one exact folder listing or exact file metadata.
- Bitable: exact app and table, complete fields, and complete selected records.
- Sheets: metadata, worksheet list, or exact find results only; never claim arbitrary cell-value coverage.

## Evidence map

Build this local, non-sensitive audit object and validate it with `scripts/feishu_guard.py validate-project-audit`:

```yaml
project_name: user-visible project name
as_of: YYYY-MM-DD
sources:
  - source_id: SRC-001
    resource_type: docx | wiki | drive | bitable | sheets
    url: exact Feishu China link
    title: returned title
    read_scope: exact document, table, node subtree, folder, or worksheet scope
    read_complete: true
    limitation: required only when read_complete is false
claims:
  - claim_id: CLM-001
    kind: fact | finding | recommendation | pending_confirmation
    category: status | milestone | document | action | risk | decision | metric | source | other
    text: one checkable statement
    source_ids: [SRC-001]
```

Facts, findings, and recommendations require at least one registered source. A pending confirmation may have no source because it identifies missing evidence. Keep one claim per statement so a citation does not appear to support unrelated text.

## Audit rules

Report only checks supported by the declared scope and returned fields:

- missing expected documents only when the user or an existing project index defines the expected set;
- broken project links only after the exact target fails to resolve;
- missing action owner or due date only when those fields are required by the source schema;
- overdue actions only when a due date is earlier than `as_of` and the source status is not terminal;
- risks missing an owner or response only when the risk register defines those fields;
- conflicting status, owner, date, metric, or decision values as conflicts, preserving every source instead of choosing one;
- unreadable, partially read, unsupported, or inaccessible sources as limitations, not healthy results.

Do not invent a project stage, required document set, terminal status vocabulary, risk threshold, owner, date, metric, or decision. Ask for the missing rule or record it as pending confirmation.

## Report

Lead with the evidence-backed project conclusion, then show source coverage, confirmed facts, findings by severity, pending confirmations, and limitations. Every fact and finding must expose its source link. State that the audit performed no remote writes.
