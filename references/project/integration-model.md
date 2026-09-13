# Project integration result model

Read this reference when verifying a project workspace across Wiki, Docx, Bitable, Sheets, or Drive resources.

Build one local result after every declared resource has been reread through Feishu MCP:

```yaml
project_name: visible project name
resources:
  - resource_key: stable local key
    resource_type: docx | wiki | drive | bitable | sheets
    url: exact Feishu URL
    status: verified | failed | unattempted
    read_complete: true
    depends_on: []
    reason: required for failed or unattempted
links:
  - source_resource_key: HOME
    target_resource_key: ACTIONS
    observed_url: exact URL read from the source resource
```

Run `scripts/feishu_guard.py validate-project-integration`. A verified or failed resource may run only after all declared prerequisites are verified; otherwise it must remain `unattempted`. Every reported link must connect two verified resources and its observed URL must equal the target's exact URL.

The validator derives `complete`, `partial`, or `failed` from resource outcomes. Never replace that result with a success claim. A failed prerequisite leaves dependent writes unattempted; it does not authorize a fallback or a whole-plan replay.

For final acceptance, expose each resource link, the read scope, verification evidence, unsuccessful and unattempted resources, unsupported areas, and whether any remote writes occurred. A resource is not verified when pagination or readback is incomplete.
