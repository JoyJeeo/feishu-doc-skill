# Docx creation preview workflow

Use this workflow in `preview` mode for a new Feishu document.

1. Read the common safety, identity, capability, preview, and quality rules.
2. Read the document model, content-generation rules, and selected template.
3. Resolve the exact Wiki parent node or Drive folder. If no target location is available, stop and ask for one.
4. Check the minimum create, content-write, and readback tools. All remote calls must support the declared identity.
5. Read the parent and its current child or file listing with user identity. Use only that parent state for the creation fingerprint.
6. Generate the complete title, summary, ordered block plan, and pending-confirmation list locally.
7. Build a deterministic `create` preview with this shape:

```yaml
target: exact parent link
resource_type: docx
operation: create
scope:
  parent: exact parent link
  placement: wiki_child | drive_file
before_state: parent identity and current child/file listing
changes:
  title: final title
  template: selected template or custom
  blocks: complete ordered block plan and visible content
  pending_confirmations: unresolved facts
risks: permission, name collision, unsupported formatting, and unresolved-content risks
required_tools: exact create, content-write, and readback tools
verification: expected parent, title, block order, content, and pending markers
```

8. Show the final location, full initial content, unresolved items, risks, required tools, and verification plan with the `preview_id`.
9. Stop without writing. Only confirmation of that `preview_id` can enter `apply`.

Do not present a shortened outline as a complete creation preview. If MCP cannot represent a requested block, replace it with the simplest faithful supported block and disclose the format loss in `risks`.
