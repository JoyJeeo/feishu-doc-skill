# Feishu document model

Read this reference for every `docx` content request. It defines the local representation used for analysis and planning; it does not replace the common preview or safety rules.

## Build a complete inventory

1. For a Wiki link, resolve the node and confirm that its underlying object is `docx`.
2. Read document metadata, then page through the document blocks until no page remains.
3. Preserve source order, parent-child relationships, block IDs, block types, text runs, and the formatting metadata returned by MCP.
4. If child content requires separate reads, traverse it before claiming that the document is fully parsed.
5. Keep an unrecognized block as opaque source data. Never infer its contents from a plain-text export.

Use this normalized inventory for local reasoning:

```yaml
document:
  id: document ID
  title: document title
  revision_id: latest revision
blocks:
  - block_id: stable block ID
    parent_id: parent block ID or null
    index: source-order position under the parent
    kind: heading | text | list | quote | code | table | callout | columns | media | unknown
    heading_level: integer or null
    text: extracted text when lossless, otherwise null
    raw_type: MCP block type
    support: readable | partially_readable | opaque
```

Do not discard the original MCP response while analyzing. The normalized inventory is an index, not a lossless serialization.

## Block compatibility

- Headings, plain text, lists, quotes, and code blocks may be interpreted when their complete text runs are available.
- Tables, Callouts, and columns are structural containers. Preserve their hierarchy and inspect their children before describing or changing them.
- Images, files, embeds, and other media are metadata-only unless MCP returns content that can be read without another channel.
- Unknown block types are opaque and protected. A future write must not replace or remove them implicitly, including through a parent-level overwrite.
- Plain-text exports may support search and summarization, but never prove formatting, hierarchy, block identity, or full fidelity.

## Locate a section

Prefer a user-provided block ID. Otherwise resolve a section by its full heading path and occurrence within the parsed hierarchy.

A section begins at the matched heading and ends before the next heading of the same or higher level. Do not match a heading from body text. If the path has zero or multiple matches, stop and report the ambiguity instead of choosing one.

For a local edit, record the target heading block ID, the ordered descendant block IDs, and the surrounding boundary headings. These identifiers define the scope used by preview, conflict detection, and verification.

## Quality audit

Audit only evidence present in the inventory and source content:

- Structure: heading order, skipped levels, duplicate sibling headings, empty sections, and misplaced blocks.
- Clarity: repeated passages, unclear titles, oversized sections, and inconsistent list or table structure.
- Consistency: terminology, product names, dates, statuses, and field labels.
- Completeness: missing owner, date, source, decision, or other fields required by the document's own pattern or the user's stated template.
- Fidelity: partially readable or opaque blocks that limit the audit.

Separate source facts from derived findings and recommendations. Do not invent the intended template, owner, date, metric, decision, or source.

Each finding must include severity, category, location by heading path or block ID, source evidence, and a recommended correction. Report unsupported blocks and uncertainty separately.
