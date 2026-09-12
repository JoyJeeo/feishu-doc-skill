# Preview protocol

Use this protocol before every remote Feishu mutation.

## Preview fields

```yaml
preview_id: deterministic identifier
target: exact Feishu target
resource_type: docx | sheets | bitable | wiki | drive | minutes | board | slides | mindnote
identity: user | application
application_identity_explicit: false
operation: create | append | insert | replace | move | update
scope: exact block, section, range, record set, or node
before_fingerprint: fingerprint of the last-read target state
changes: proposed changes
risks: known permission, overwrite, format, or partial-failure risks
required_tools: exact Feishu MCP tools needed to apply and verify
verification: expected post-write checks
status: pending_confirmation
```

Deletion, ownership transfer, and public-permission changes are not valid operations while their policy switches are disabled.

## Lifecycle

1. Read the target with user identity.
2. Build the proposed change without remote mutation.
3. Produce a preview and `preview_id`.
4. If the preview contains converter-generated block IDs or another transient nested payload, persist the exact non-sensitive payload in a task-local temporary artifact before requesting confirmation. Do not rely on memory-only state across user turns.
5. Wait for the user to confirm that exact identifier.
6. Reread the target and recompute its fingerprint.
7. Invalidate the preview if the fingerprint, target, identity, scope, required tools, or persisted payload changed or is unavailable.
8. Apply only the declared change, reading transient nested arguments from the persisted artifact without reconstruction.
9. Reread and verify the result.
10. Mark the preview as applied in the current task context so it cannot be applied again, then remove its temporary artifact.

## Confirmation

Valid confirmation must unambiguously refer to the current preview, preferably by `preview_id`. Generic statements made before preview generation do not count as confirmation.

## Cross-resource changes

Create one preview per resource. Confirmation of one preview does not authorize the others. Report dependencies between previews so the user can choose an order.

## Diff expectations

- Documents: show affected section or block and before/after content.
- Sheets: show sheet name, range, changed dimensions, and representative differences.
- Bitable: show table, record selection rule, affected count, and field changes.
- Wiki or Drive: show source, destination, names, and permission effects.
- New resources: show final parent location and complete initial structure.

Use `scripts/feishu_guard.py make-preview` and `validate-preview` for deterministic checks.
