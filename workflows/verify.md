# Verify workflow

Use after every write and for standalone read-only checks.

For a cross-resource project workspace, also follow [project-integration-verify.md](project-integration-verify.md) and validate exact links, dependencies, and partial outcomes locally.

1. Identify the expected target, identity, scope, and result.
2. Check that the required Feishu MCP read tools are visible.
3. Reread the target with the same identity used for the operation.
4. Compare content, structure, counts, links, locations, and permissions that were part of the preview.
5. Check non-target content when the operation promised a local edit.
6. Classify the result as verified, partially verified, failed, or unknown.
7. Report evidence, completed actions, mismatches, and unverified areas.

Do not mutate the target while verifying. A mismatch may produce a proposed corrective preview, but never an automatic correction.
