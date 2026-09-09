# Identity policy

## Default

Use user identity for personal Feishu operations. When the selected MCP tool accepts `useUAT`, pass `useUAT: true` explicitly. Do not rely on an omitted parameter.

## No automatic fallback

If a user-identity call fails because of authentication, authorization, or resource access:

1. Stop the affected operation.
2. Report the tool, target, stage, and returned error.
3. Explain that application identity was not attempted.
4. Ask the user to repair user authorization or explicitly request application identity.

Never silently retry with `useUAT: false` or an omitted identity parameter.

## Explicit application identity

Application identity is allowed only when the user explicitly requests it. It requires:

- a new preview whose `identity` is `application`;
- an explicit marker that application identity was requested;
- a fresh confirmation for that preview;
- the same conflict, scope, and verification checks as user identity.

A previous user-identity preview cannot be reused for an application-identity call.

## Identity validation

Use `scripts/feishu_guard.py identity user` for the default parameters. Application identity validation requires the `--explicit` flag.
