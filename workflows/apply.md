# Apply workflow

Use only after the user confirms a specific `preview_id`.

1. Load the exact preview and the confirmed identifier.
2. Reject the request if the preview was already applied in the current task.
3. Confirm that all required tools are visible and start with `mcp__feishu__`.
4. Reread the target using the same identity and scope used by the preview.
5. Validate the preview identifier, integrity, current fingerprint, identity, operation, required tools, and policy switches.
6. If validation fails, do not write; explain whether a new preview is required.
7. Call only the write tools and exact serialized arguments declared by the preview. Never reconstruct or edit a nested payload by hand after validation. Set `useUAT: true` when supported.
8. Record completed, failed, and unattempted actions.
9. Reread the affected target using Feishu MCP.
10. Follow the verify workflow before reporting success.
11. Mark the preview as applied in current task context only after the write result is known.

Never retry a failed user call as the application. Any corrective write requires a new preview.
