# Preview workflow

Use for every request that could change a Feishu resource.

1. Identify the resource, exact target, requested operation, and scope.
2. Reject disabled operations before any remote call.
3. Check that the necessary read, write, and verification tools exist under `mcp__feishu__`.
4. Read the current target using user identity and retain only the state needed for planning.
5. Resolve ambiguous sections, ranges, records, or nodes. Stop if the scope is not unique.
6. Build the proposed content or structural change locally.
7. Calculate the target-state fingerprint and build a deterministic preview.
8. Show the target, identity, operation, scope, before/after differences, risks, required tools, and verification plan.
9. Stop and wait for confirmation of the displayed `preview_id`.

This workflow performs no remote writes. A statement made before the preview exists cannot authorize `apply`.

For cross-resource work, create separate previews and explain their dependency order.

For a new `docx` document, follow [docx-create-preview.md](docx-create-preview.md).
