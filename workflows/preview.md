# Preview workflow

Use for every request that could change a Feishu resource.

1. Identify the resource, exact target, requested operation, and scope.
2. Reject disabled operations before any remote call.
3. Check that the necessary read, write, and verification tools exist under `mcp__feishu__`.
4. Read the current target using user identity and retain only the state needed for planning.
5. Resolve ambiguous sections, ranges, records, or nodes. Stop if the scope is not unique.
6. Build the proposed content or structural change locally.
7. Calculate the target-state fingerprint and build a deterministic preview.
8. Create and display a locally viewable effect confirmation. It must make the actual content or structural change, before/after difference, unaffected scope, risks, and verification plan obvious without requiring the user to interpret tokens or encoded arguments.
9. Keep the `preview_id` as the internal binding for that visible confirmation, then stop and wait for the user to confirm the displayed operation. Do not present the identifier itself as the preview or require the user to type it.

This workflow performs no remote writes. A statement made before the preview exists cannot authorize `apply`.

For cross-resource work, create separate previews and explain their dependency order.

For a new `docx` document, follow [docx-create-preview.md](docx-create-preview.md).

For a project home, document set, or weekly report, follow [project-workspace-preview.md](project-workspace-preview.md) before the resource-specific Docx workflow.

For a project action, risk, decision, or metric register, follow [project-register-preview.md](project-register-preview.md). Create and confirm one data-table preview at a time.

For Bitable record creation or updates, follow [bitable-record-preview.md](bitable-record-preview.md).

For a Sheets find/replace, follow [sheets-find-replace-preview.md](sheets-find-replace-preview.md).

For Wiki mutation, read [references/wiki/write-model.md](../references/wiki/write-model.md) and validate create/copy/move/update scope, token/parent mapping, duplicate-name checks, and readback plan.

For Drive mutation, read [references/drive/write-model.md](../references/drive/write-model.md) and validate copy/move/create/update scope, source and target placement, duplicate-name checks, and revision-source requirements.
