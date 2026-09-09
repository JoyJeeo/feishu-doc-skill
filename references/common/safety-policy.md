# Safety policy

## Mode boundaries

| Mode | Remote reads | Remote writes |
|---|---:|---:|
| `analyze` | Allowed through Feishu MCP | Forbidden |
| `preview` | Allowed through Feishu MCP | Forbidden |
| `apply` | Required for preflight and verification | Allowed only for a confirmed, valid preview |
| `verify` | Allowed through Feishu MCP | Forbidden |

An initial request to create, edit, organize, format, move, or update a resource enters `preview`, not `apply`.

## Forbidden remote paths

Do not use any of the following for Feishu access:

- Chrome or another browser;
- CUA or simulated clicks;
- a non-Feishu connector;
- direct HTTP requests or OpenAPI clients;
- local scripts that perform network access.

If Feishu MCP is missing or fails, stop and report. Do not propose an automatic workaround.

## Disabled operations

The following are disabled:

- delete;
- transfer ownership;
- change public-access permissions.

Do not generate an executable preview for these operations while disabled. Explain that the policy must be changed explicitly before implementation.

## Partial failure

When a multi-step call partially succeeds:

- do not retry blindly;
- reread the affected scope using Feishu MCP;
- identify completed, failed, and unattempted actions;
- generate a new preview for any corrective write;
- do not delete test or partial resources without a separate authorized preview.

## Sensitive data

Do not store credentials, authorization headers, access tokens, tenant secrets, or complete sensitive document bodies in repository files or logs.
